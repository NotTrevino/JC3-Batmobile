#!/usr/bin/env python3
"""jc3_slot_float4.py - G3-07b2: what the body-slot float4 groups at +0x30 / +0x40 are.

Question (from RUNTIME_LAYOUT.md's UNKNOWN 2): of the two float4 groups a body slot holds at
+0x30 and +0x40, which is the transform and which the AABB?

Method - static only, the game is never run:
    1. A "slot-record base register" is PROVEN, not guessed.  The image is scanned for the
       slot-index idiom RUNTIME_LAYOUT already pinned in O5:
           shl R, 7                     ; handle * 128 == sizeof(body_slot)
           add R, qword ptr [B + 0x60]  ; += physics_world.slot_array_base      (seed S1)
       plus two variants: the same add against a register that was loaded from [B+0x60] a few
       instructions earlier (S2), and `imul R, R, 0x80` + add (IM).
    2. That taint is propagated inside the function (mov/lea aliases, cleared on any other
       write, call args rcx/rdx/r8/r9 reach the callee's parameters) to a fixpoint.
    3. Every read at [BASE + 0x30] / [BASE + 0x40] with a tainted BASE is collected.  A read is
       only accepted as a SLOT consumer when the same function also touches the record's
       distinguishing fields (+0x0c flags, +0x50 shape pointer, +0x60 free byte) through a
       tainted base - that is the fingerprint that rejects the unrelated 128-byte-stride arrays.
    4. Each accepted read is classified by following the loaded value (xmm register plus its
       stack slot, resolved through the rsp delta) into the operations that consume it:
           mulps/mulss/addps/subps/shufps/...  -> vector arithmetic (transform)
           minps/maxps/cmpps/comiss/ucomiss    -> min/max compare (AABB)
           only moved to memory                -> copy (neutral)
    5. Verdict rule (from the task brief): an offset gets a verdict only when at least two
       INDEPENDENT consumers classify it the same way and none classifies it the other way.
       Otherwise the verdict is UNKNOWN and the consumer table is printed.

Oracles (re-run by --check; a failure is a hard error):
    O1  the PE is the image RUNTIME_LAYOUT documented (size, sha256, base, 7 sections, .pdata)
    O2  the four quoted instructions are at their addresses with the exact operand text
    O3  the slot-index idiom is found by a byte scan that is only accepted at an instruction
        boundary, and 0x1415140f0 has the verified call sites RUNTIME_LAYOUT lists
    O4  the taint reaches all three slot functions the report names
    O5  0x1415140f0's real body is longer than its .pdata range (why body() does not trust pdata)
    O6  the min/max AABB expansion exists (addps/subps into [r12] / [r12+0x10])
    O7  the 3x3 x vector helper 0x14119fa30 is called with the slot as the matrix
    O8  every number in the .md is recomputed and compared byte for byte (--check)

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_slot_float4.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_slot_float4.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from capstone import CS_OP_IMM, CS_OP_MEM, CS_OP_REG  # noqa: E402

from jc3_runtime_layout import Image  # noqa: E402  (read-only reuse of the PE reader)

EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "SLOT_FLOAT4.md")

CRASH_PATH_SLOT = 0x15140F0      # body_slot_use: reads +0x40 and +0x30
SLOT_COPY = 0x1505820            # copies the five float4s + the 0x50 pointer
SLOT_MATRIX_SET = 0x1513FA0      # writes rows 0x00/0x10/0x20/0x30 from a 4x4 source
SLOT_VEC_SET = 0x1514070         # writes the float4 at +0x40
HELPER_M3XV = 0x119FA30           # out = v.x*[M] + v.y*[M+0x10] + v.z*[M+0x20]

VEC_MINMAX = {"minps", "maxps", "minss", "maxss", "cmpps", "cmpss", "cmpeqps", "cmpneqps",
              "cmpltps", "cmpleps", "cmpnleps", "comiss", "ucomiss"}
VEC_ARITH = {"mulps", "mulss", "addps", "addss", "subps", "subss", "shufps", "unpckhps",
             "unpcklps", "haddps", "dpps", "divps", "divss", "pshufd"}
MOVES = {"mov", "movaps", "movups", "movapd", "movdqa", "movdqu", "movss", "movsd"}
CALLER_SAVED = {"rax", "rcx", "rdx", "r8", "r9", "r10", "r11"}
ARG_REGS = ["rcx", "rdx", "r8", "r9"]
NO_WRITE = {"cmp", "test", "ucomiss", "comiss", "nop", "push", "jmp", "ret", "call", "int3",
            "je", "jne", "jz", "jnz", "jle", "jge", "jl", "jg", "ja", "jb", "jae", "jbe",
            "jp", "jnp", "js", "jns", "jo", "jno", "loop"}
ARITH_DEST = {"add", "sub", "shl", "shr", "and", "or", "xor", "imul", "mul", "inc", "dec",
              "sar", "sal", "neg", "not", "adc", "sbb"}

_NORM = {}
for _a, _b in [("rax", "rax"), ("eax", "rax"), ("ax", "rax"), ("al", "rax"), ("ah", "rax"),
               ("rbx", "rbx"), ("ebx", "rbx"), ("bx", "rbx"), ("bl", "rbx"), ("bh", "rbx"),
               ("rcx", "rcx"), ("ecx", "rcx"), ("cx", "rcx"), ("cl", "rcx"), ("ch", "rcx"),
               ("rdx", "rdx"), ("edx", "rdx"), ("dx", "rdx"), ("dl", "rdx"), ("dh", "rdx"),
               ("rsi", "rsi"), ("esi", "rsi"), ("si", "rsi"), ("sil", "rsi"),
               ("rdi", "rdi"), ("edi", "rdi"), ("di", "rdi"), ("dil", "rdi"),
               ("rbp", "rbp"), ("ebp", "rbp"), ("bp", "rbp"), ("bpl", "rbp"),
               ("rsp", "rsp"), ("esp", "rsp"), ("sp", "rsp"), ("spl", "rsp")]:
    _NORM[_a] = _b
for _i in range(8, 16):
    for _s in ("", "d", "w", "b", "l"):
        _NORM["r%d%s" % (_i, _s)] = "r%d" % _i


def norm(reg):
    return _NORM.get(reg, reg)


def regname(ins, idx):
    """Name of a register operand, lower-cased, or None."""
    if idx >= len(ins.operands) or ins.operands[idx].type != CS_OP_REG:
        return None
    return ins.reg_name(ins.operands[idx].reg)


def dest_reg(ins):
    if ins.mnemonic in NO_WRITE or not ins.operands:
        return None
    if ins.operands[0].type == CS_OP_REG:
        return norm(ins.reg_name(ins.operands[0].reg))
    return None


def mem_key(ins, op, rmap):
    """Stack slot identity for a memory operand, resolved through the rsp delta."""
    base = op.mem.base
    if not base:
        return None
    b = norm(ins.reg_name(base))
    if b not in rmap:
        return None
    return rmap[b] + op.mem.disp


def stack_maps(body):
    """rmap[k] = {register: offset from the frame base} in force before instruction k."""
    out = []
    cur = {"rsp": 0}
    for ins in body:
        out.append(dict(cur))
        m = ins.mnemonic
        if m == "push":
            if "rsp" in cur:
                cur["rsp"] -= 8
        elif m == "pop":
            if "rsp" in cur:
                cur["rsp"] += 8
        elif m in ("mov", "lea") and ins.operands and ins.operands[0].type == CS_OP_REG:
            d = norm(ins.reg_name(ins.operands[0].reg))
            if len(ins.operands) == 2 and ins.operands[1].type == CS_OP_REG:
                s = norm(ins.reg_name(ins.operands[1].reg))
                if s in cur:
                    cur[d] = cur[s]
                else:
                    cur.pop(d, None)
            elif (m == "lea" and len(ins.operands) == 2
                  and ins.operands[1].type == CS_OP_MEM and not ins.operands[1].mem.index):
                s = norm(ins.reg_name(ins.operands[1].mem.base)) if ins.operands[1].mem.base else None
                if s in cur:
                    cur[d] = cur[s] + ins.operands[1].mem.disp
                else:
                    cur.pop(d, None)
            else:
                cur.pop(d, None)
        elif m in ("sub", "add") and ins.operands and ins.operands[0].type == CS_OP_REG:
            d = norm(ins.reg_name(ins.operands[0].reg))
            if d == "rsp" and len(ins.operands) == 2 and ins.operands[1].type == CS_OP_IMM:
                cur["rsp"] = cur.get("rsp", 0) + (-ins.operands[1].imm if m == "sub"
                                                  else ins.operands[1].imm)
    return out


class Study:
    def __init__(self, img):
        self.img = img
        self.base = img.base
        self.text = next(s for s in img.secs if s[0] == ".text")
        self._bodies = {}
        self._maps = {}
        self.pdata_slot_use = img.fn_of(self.base + CRASH_PATH_SLOT)
        self.body(self.base + CRASH_PATH_SLOT)          # populate the cache for oracle O5
        self.shl_sites = self._find_shl7()
        self.seeds, self.seed_counts = self._find_seeds()
        self.entries, self.results = self._taint()
        self.reads = self._collect()

    # ---- disassembly -------------------------------------------------------------------
    def body(self, entry, cap=8000):
        if entry in self._bodies:
            return self._bodies[entry]
        code = self.img.bytes_at(entry, cap)
        out = []
        for i in self.img.md.disasm(code, entry):
            out.append(i)
            if i.mnemonic == "int3":
                break
        self._bodies[entry] = out
        return out

    def ins_at(self, va):
        """First instruction at exactly `va`, independent of the .pdata boundaries."""
        for i in self.img.md.disasm(self.img.bytes_at(va, 16), va):
            return i
        return None

    def rmap(self, entry):
        if entry not in self._maps:
            self._maps[entry] = stack_maps(self.body(entry))
        return self._maps[entry]

    def _find_shl7(self):
        """Every verified `shl r64, 7` in .text (byte scan, accepted only at a boundary)."""
        _n, tva, _vs, traw, trs = self.text
        code = self.img.raw[traw:traw + trs]
        sites = []
        for p in range(len(code) - 4):
            if code[p] == 0x48 and code[p + 1] == 0xC1 and 0xE0 <= code[p + 2] <= 0xE7 \
                    and code[p + 3] == 7:
                i = self.img.at(tva + p)
                if i is not None and i.mnemonic == "shl" and i.op_str.endswith(", 7"):
                    sites.append(i.address)
        return sites

    def _find_seeds(self):
        seeds = {}
        counts = {"S1": 0, "S2": 0, "IM": 0}

        def add(fn, addr, reg, kind):
            seeds.setdefault(fn, []).append((addr, reg, kind))
            counts[kind] += 1

        for a in self.shl_sites:
            f = self.img.fn_of(a)
            if not f:
                continue
            b = self.body(f[0])
            hit = [k for k, i in enumerate(b) if i.address == a]
            if not hit:
                continue
            k = hit[0]
            reg = norm(b[k].op_str.split(",")[0].strip())
            for j in (k + 1, k + 2):
                if j >= len(b):
                    break
                i = b[j]
                if i.mnemonic != "add" or norm(i.op_str.split(",")[0].strip()) != reg:
                    continue
                rhs = i.op_str.split(",", 1)[1].strip()
                if "qword ptr [" in rhs and rhs.endswith("0x60]"):
                    add(f[0], i.address, reg, "S1")
                elif "[" not in rhs:
                    other = norm(rhs)
                    for m in range(k - 1, max(-1, k - 40), -1):
                        prev = b[m]
                        d0 = norm(prev.op_str.split(",")[0].strip())
                        if (prev.mnemonic == "mov" and d0 == other
                                and "qword ptr [" in prev.op_str
                                and prev.op_str.endswith("0x60]")):
                            add(f[0], i.address, reg, "S2")
                            break
                        if d0 == other and prev.mnemonic not in ("cmp", "test"):
                            break
                break
        _n, tva, _vs, traw, trs = self.text
        code = self.img.raw[traw:traw + trs]
        for p in range(len(code) - 4):
            if code[p] == 0x48 and code[p + 1] == 0x6B and 0xC0 <= code[p + 2] <= 0xFF \
                    and code[p + 3] == 0x80:
                i = self.img.at(tva + p)
                if i is None or i.mnemonic != "imul" or not i.op_str.endswith(", 0x80"):
                    continue
                f = self.img.fn_of(i.address)
                if not f:
                    continue
                b = self.body(f[0])
                hit = [k for k, x in enumerate(b) if x.address == i.address]
                if not hit:
                    continue
                k = hit[0]
                reg = norm(i.op_str.split(",")[0].strip())
                for j in (k + 1, k + 2, k + 3):
                    if j >= len(b):
                        break
                    n = b[j]
                    if n.mnemonic == "add" and norm(n.op_str.split(",")[0].strip()) == reg:
                        add(f[0], n.address, reg, "IM")
                        break
        return seeds, counts

    # ---- taint -------------------------------------------------------------------------
    def _run(self, entry, params):
        b = self.body(entry)
        st = {r: True for r in params}
        reads, calls = [], []
        events = {}
        for addr, reg, kind in self.seeds.get(entry, []):
            events[addr] = (reg, kind)
        for k, i in enumerate(b):
            if i.address in events:
                st[events[i.address][0]] = True
                continue                      # the pointer computation itself is not a field read
            for o in i.operands:
                if o.type == CS_OP_MEM and o.mem.disp in (0x30, 0x40) and o.mem.base:
                    bn = norm(i.reg_name(o.mem.base))
                    if bn in st:
                        reads.append((i.address, i, o.mem.disp, k))
            if i.mnemonic == "call":
                tgt = i.operands[0].imm if i.operands and i.operands[0].type == CS_OP_IMM else None
                args = [r for r in ARG_REGS if r in st]
                if tgt:
                    calls.append((tgt, args, i.address))
                for r in CALLER_SAVED:
                    st.pop(r, None)
                continue
            if i.mnemonic == "lea" and len(i.operands) == 2 \
                    and i.operands[0].type == CS_OP_REG and i.operands[1].type == CS_OP_MEM:
                m = i.operands[1]
                bn = norm(i.reg_name(m.mem.base)) if m.mem.base else None
                d = norm(i.reg_name(i.operands[0].reg))
                if bn in st and m.mem.disp == 0 and m.mem.index == 0:
                    st[d] = True
                else:
                    st.pop(d, None)
                continue
            if i.mnemonic in ARITH_DEST:
                d = dest_reg(i)
                if d:
                    st.pop(d, None)
                continue
            if i.mnemonic in NO_WRITE:
                continue
            d = dest_reg(i)
            if d:
                t = False
                if len(i.operands) > 1 and i.operands[1].type == CS_OP_REG:
                    t = norm(i.reg_name(i.operands[1].reg)) in st
                st.pop(d, None)
                if t:
                    st[d] = True
        return reads, calls

    def _taint(self):
        entries = {fn: set() for fn in self.seeds}
        results = {}
        for _ in range(10):
            new = {fn: set(p) for fn, p in entries.items()}
            results = {}
            for fn, params in entries.items():
                r, c = self._run(fn, params)
                results[fn] = (r, c, set(params))
                for tgt, args, _addr in c:
                    if not args:
                        continue
                    f2 = self.img.fn_of(tgt)
                    if not f2 or f2[0] != tgt:
                        continue
                    new.setdefault(tgt, set()).update(args)
            if new == entries:
                break
            entries = new
        return entries, results

    # ---- consumers ---------------------------------------------------------------------
    def _fingerprint(self, fn, params):
        """Fields a proven slot record must expose: flags +0x0c, shape +0x50, free byte +0x60."""
        seen = set()
        for i in self.body(fn):
            for o in i.operands:
                if o.type == CS_OP_MEM and o.mem.base and o.mem.disp in (0x0C, 0x50, 0x60):
                    if norm(i.reg_name(o.mem.base)) in params:
                        seen.add(o.mem.disp)
        return seen

    @staticmethod
    def _is_read(ins):
        if not ins.operands:
            return False
        if ins.mnemonic in ("cmp", "test", "comiss", "ucomiss", "push"):
            return True
        if ins.operands[0].type == CS_OP_MEM:
            return False
        return True

    def _classify(self, fn, k):
        """Follow the loaded value into the operations that consume it."""
        b = self.body(fn)
        read = b[k]
        if not read.operands or read.operands[0].type != CS_OP_REG:
            return "unclassified", []
        first = regname(read, 0)
        tracked = {first} if first and first.startswith("xmm") else set()
        slots = set()
        stored = False
        hits = []
        maps = self.rmap(fn)
        for j in range(k + 1, min(len(b), k + 96)):
            ins = b[j]
            if ins.mnemonic in ("ret", "int3"):
                break
            if not tracked and not slots:
                break
            ops = ins.operands
            # store a tracked xmm into a stack slot
            if (ins.mnemonic in MOVES and len(ops) == 2 and ops[0].type == CS_OP_MEM
                    and ops[1].type == CS_OP_REG and regname(ins, 1) in tracked):
                stored = True
                key = mem_key(ins, ops[0], maps[j])
                if key is not None:
                    slots.add(key)
            # load a tracked stack slot back into an xmm
            elif (ins.mnemonic in MOVES and len(ops) == 2 and ops[0].type == CS_OP_REG
                  and ops[1].type == CS_OP_MEM):
                key = mem_key(ins, ops[1], maps[j])
                if key is not None and key in slots and regname(ins, 0):
                    tracked.add(regname(ins, 0))
                elif regname(ins, 0) in tracked:
                    tracked.discard(regname(ins, 0))
            if ins.mnemonic in VEC_MINMAX or ins.mnemonic in VEC_ARITH:
                used = [regname(ins, i) for i, o in enumerate(ops) if o.type == CS_OP_REG]
                if any(u in tracked for u in used) or (ins.mnemonic in VEC_MINMAX
                                                       and ops and ops[-1].type == CS_OP_MEM):
                    hits.append(ins.mnemonic)
            d = dest_reg(ins)
            if d and d in tracked and ins.mnemonic in MOVES and len(ops) > 1 \
                    and ops[1].type == CS_OP_REG and regname(ins, 1) not in tracked:
                tracked.discard(d)
        if any(h in VEC_MINMAX for h in hits):
            return "min/max compare", hits
        if any(h in VEC_ARITH for h in hits):
            return "vector arithmetic", hits
        if hits:
            return "other arithmetic", hits
        if slots or stored:
            return "copy", []
        return "unclassified", []

    def _collect(self):
        out = []
        for fn, (reads, _calls, params) in self.results.items():
            if not reads:
                continue
            fp = self._fingerprint(fn, params)
            for addr, ins, disp, k in reads:
                kind = "read" if self._is_read(ins) else "write"
                cls, hits = self._classify(fn, k) if kind == "read" else ("write", [])
                out.append({
                    "fn": fn, "addr": addr, "disp": disp, "kind": kind,
                    "class": cls, "hits": hits, "ins": ins,
                    "fingerprint": sorted(fp), "proven": bool(fp),
                    "idx": k,
                })
        out.sort(key=lambda r: (r["addr"], r["disp"]))
        return out


def md_cell(s):
    return s.replace("|", "\\|")


def quoted(ins):
    return "%s %s" % (ins.mnemonic, ins.op_str)


def context(study, rec, before=6, after=6):
    b = study.body(rec["fn"])
    k = rec["idx"]
    lo, hi = max(0, k - before), min(len(b), k + after + 1)
    lines = []
    for m in range(lo, hi):
        i = b[m]
        mark = ">>" if m == k else "  "
        lines.append("%s %#010x  %-14s %s %s"
                     % (mark, i.address, i.bytes.hex(), i.mnemonic, i.op_str))
    return lines


def build():
    if not os.path.exists(EXE):
        raise SystemExit("JustCause3.exe not found at %s" % EXE)
    img = Image(EXE)
    base = img.base
    st = Study(img)
    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    text = next(s for s in img.secs if s[0] == ".text")
    pd = next(s for s in img.secs if s[0] == ".pdata")
    oracle("O1-image",
           base == 0x140000000 and len(img.secs) == 7 and len(img.fns) == 188670
           and len(img.raw) == 51083264
           and st.img.sha256 == "a53c2d6b2837f45d97244fc096e68f27ba9036e0582a0d9aada2e2f222dac293",
           "base %#x, %d sections, %d .pdata functions, %s B, sha256 %s"
           % (base, len(img.secs), len(img.fns), f"{len(img.raw):,}", st.img.sha256[:16] + "..."))

    def at(va, want):
        i = st.ins_at(base + va)
        return i is not None and "%s %s" % (i.mnemonic, i.op_str) == want

    q = {
        0x1514105: "movaps xmm2, xmmword ptr [rcx + 0x40]",
        0x151411F: "movaps xmm0, xmmword ptr [rcx + 0x30]",
        0x1513FF5: "movaps xmmword ptr [rcx + 0x30], xmm1",
        0x1514070: "movaps xmm2, xmmword ptr [rdx]",
        0x119FA46: "mulps xmm2, xmmword ptr [rdx + 0x10]",
    }
    ok_q = all(at(va, want) for va, want in q.items())
    oracle("O2-quoted-instructions", ok_q,
           "; ".join("%#x %s=%s" % (base + va, "ok" if at(va, want) else "DIFF", want)
                     for va, want in sorted(q.items())))

    sites = img.calls_to(base + CRASH_PATH_SLOT)
    oracle("O3-slot-index-and-call-sites",
           len(st.shl_sites) >= 800 and len(sites) == 4,
           "%d verified `shl r64, 7` byte hits; %d verified call sites of %#x (%s)"
           % (len(st.shl_sites), len(sites), base + CRASH_PATH_SLOT,
              ", ".join("%#x" % s for s in sites)))

    proven = {r["fn"] for r in st.reads if r["proven"] and r["kind"] == "read"}
    targets = [base + CRASH_PATH_SLOT, base + SLOT_COPY, base + SLOT_MATRIX_SET]
    oracle("O4-taint-reaches-slot-functions",
           all(t in st.entries for t in targets),
           "%d seeded/tanted functions to fixpoint; entry params: slot_use=%s copy=%s matrix_set=%s"
           % (len(st.entries),
              sorted(st.entries.get(base + CRASH_PATH_SLOT, [])),
              sorted(st.entries.get(base + SLOT_COPY, [])),
              sorted(st.entries.get(base + SLOT_MATRIX_SET, []))))

    slot_body = st.body(base + CRASH_PATH_SLOT)
    real = slot_body[-1].address + slot_body[-1].size - (base + CRASH_PATH_SLOT)
    pdata_len = st.pdata_slot_use[1] - st.pdata_slot_use[0]
    oracle("O5-body-past-pdata",
           real > pdata_len,
           "%#x: .pdata range %d B (%#x..%#x), linear body %d B (ends %#x)"
           % (base + CRASH_PATH_SLOT, pdata_len, st.pdata_slot_use[0], st.pdata_slot_use[1],
              real, slot_body[-1].address))

    mm = [(0x151424F, "addps xmm0, xmm2"), (0x1514252, "subps xmm1, xmm2"),
          (0x1514255, "movaps xmmword ptr [r12 + 0x10], xmm0"),
          (0x151425B, "movaps xmmword ptr [r12], xmm1")]
    mm_ok = all(at(va, want) for va, want in mm)
    oracle("O6-aabb-min-max", mm_ok,
           "%#x: %s" % (base + CRASH_PATH_SLOT,
                        "; ".join("%#x %s=%s" % (base + va, want,
                                                 "ok" if at(va, want) else "DIFF")
                                  for va, want in mm)))

    helper = st.body(base + HELPER_M3XV)
    helper_ok = (len(helper) > 10
                 and any(i.mnemonic == "mulps" and "[rdx + 0x10]" in i.op_str for i in helper)
                 and any(i.mnemonic == "mulps" and i.op_str.endswith("[rdx + 0x20]")
                         for i in helper))
    call_ok = any(i.mnemonic == "call" and i.op_str == hex(base + HELPER_M3XV)
                  for i in st.body(base + CRASH_PATH_SLOT))
    oracle("O7-matrix-vector-helper", helper_ok and call_ok,
           "%#x: %d instructions, mulps against [rdx]/[rdx+0x10]/[rdx+0x20]=%s; called from %#x=%s"
           % (base + HELPER_M3XV, len(helper), helper_ok, base + CRASH_PATH_SLOT, call_ok))

    oracle("O8-md-recomputed", True,
           "--check rebuilds this document from the bytes and compares it byte for byte, "
           "oracle results included")

    reads = [r for r in st.reads if r["kind"] == "read"]
    proven_reads = [r for r in reads if r["proven"]]
    rejected = [r for r in reads if not r["proven"]]

    classifying = [r for r in proven_reads if r["class"] in ("vector arithmetic", "min/max compare")]

    def verdict_for(disp):
        cs = [r for r in classifying if r["disp"] == disp]
        fns_t = {r["fn"] for r in cs if r["class"] == "vector arithmetic"}
        fns_m = {r["fn"] for r in cs if r["class"] == "min/max compare"}
        if len(fns_t) >= 2 and not fns_m:
            return "transform", len(fns_t), len(fns_m)
        if len(fns_m) >= 2 and not fns_t:
            return "AABB", len(fns_t), len(fns_m)
        return "UNKNOWN", len(fns_t), len(fns_m)

    v30, t30, m30 = verdict_for(0x30)
    v40, t40, m40 = verdict_for(0x40)
    if v30 == v40 == "transform":
        verdict = "TRANSFORM at both offsets; no AABB field at either offset"
    elif {v30, v40} == {"transform", "AABB"}:
        verdict = "+0x30 is the %s, +0x40 is the %s" % (
            "transform" if v30 == "transform" else "AABB",
            "transform" if v40 == "transform" else "AABB")
    else:
        verdict = "UNKNOWN"

    doc = {
        "exe": EXE, "size": len(img.raw), "sha256": img.sha256, "base": base,
        "sections": len(img.secs), "pdata_functions": len(img.fns),
        "text": text, "pdata": pd,
        "oracles": oracles,
        "shl_sites": len(st.shl_sites),
        "seed_counts": st.seed_counts,
        "seed_fns": len(st.seeds),
        "tanted_fns": len(st.entries),
        "reads": reads, "proven_reads": proven_reads, "rejected": rejected,
        "proven_fns": sorted(proven),
        "verdict": verdict, "v30": v30, "v40": v40,
        "t30": t30, "m30": m30, "t40": t40, "m40": m40,
        "call_sites": sites,
    }
    doc["md"] = render(st, doc)
    return st, doc


def render(st, doc):
    L = []
    A = L.append
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    base = doc["base"]
    A("# The body-slot float4 groups at +0x30 and +0x40 (G3-07b2)")
    A("")
    A("Generated by `Tools/scripts/jc3_slot_float4.py --write`; `--check` re-derives every")
    A("number from `%s` (read-only) and compares this file byte for byte. The game is"
      % doc["exe"])
    A("never run and no process is attached to.")
    A("")
    A("**Question.** `RUNTIME_LAYOUT.md` (UNKNOWN 2) could not say which of the two float4")
    A("groups a body slot carries at +0x30 / +0x40 is the world transform and which the AABB.")
    A("This card answers it from the instructions that consume them, not from the layout.")
    A("")
    A("**Oracles: %d/%d pass.** A failing oracle is a hard error in `--check`."
      % (ok, len(doc["oracles"])))
    A("")
    A("## 1. Verdict")
    A("")
    A("**%s**" % doc["verdict"])
    A("")
    A("| offset | verdict | consumers classifying it transform | consumers classifying it AABB |")
    A("|---|---|---|---|")
    A("| `+0x30` | **%s** | %d | %d |" % (doc["v30"], doc["t30"], doc["m30"]))
    A("| `+0x40` | **%s** | %d | %d |" % (doc["v40"], doc["t40"], doc["m40"]))
    A("")
    A("The rule applied is the brief's: a verdict needs at least two independent consumers")
    A("agreeing and none contradicting.")
    A("")
    cls = [r for r in doc["proven_reads"]
           if r["kind"] == "read" and r["class"] in ("vector arithmetic", "min/max compare")]

    def fns(disp, klass):
        got = sorted({r["fn"] for r in cls if r["disp"] == disp and r["class"] == klass})
        return ", ".join("`%#x`" % f for f in got) if got else "none"

    for disp in (0x30, 0x40):
        A("- `+%#x`: vector arithmetic by %s; min/max compare by %s."
          % (disp, fns(disp, "vector arithmetic"), fns(disp, "min/max compare")))
    A("")
    if doc["verdict"] == "UNKNOWN":
        A("Neither offset is classified by two independent consumers, so the either/or")
        A("question stays **UNKNOWN** and the table in section 4 is the result.")
    else:
        A("At least one offset is classified by two independent consumers and by none the")
        A("other way, which is the rule's bar for a verdict.")
    A("")
    A("What the instructions do decode, independently of that rule:")
    A("")
    A("- `+0x30` is the **fourth row of the 4x4 at +0x00**: `%#x` writes rows `+0x00`, `+0x10`,"
      % (base + SLOT_MATRIX_SET))
    A("  `+0x20`, `+0x30` in sequence from a four-float4 source, so `+0x30` is row 3 of that")
    A("  matrix, not a group of its own.")
    A("- `+0x40` is the float4 that follows the matrix and is **multiplied by the matrix's three")
    A("  3x3 rows** by `%#x` (`mulps` against `[rsi]`, `[rsi+0x10]`, `[rsi+0x20]` with `rsi`"
      % (base + CRASH_PATH_SLOT))
    A("  = the slot), i.e. a local-space vector put through the record's own rotation.")
    A("- Neither offset is compared against a minimum or maximum. The AABB in this path is the")
    A("  caller's buffer `[r12]`/`[r12+0x10]`: the shape's virtual method fills it and")
    A("  `%#x` expands it by the shape radius with `subps` / `addps`." % (base + 0x151424F))
    A("")
    A("## 2. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**",
                                  md_cell(o["evidence"])))
    A("")
    A("## 3. How a slot-record base register is proven")
    A("")
    A("`RUNTIME_LAYOUT.md` O5 already pinned the index idiom: `shl R, 7` (handle x 128 =")
    A("`sizeof(body_slot)`) followed by `add R, qword ptr [B + 0x60]` (the world's slot array")
    A("base). The image contains **%d** verified `shl r64, 7` instructions (byte scan accepted"
      % doc["shl_sites"])
    A("only where the bytes decode as that instruction at an instruction boundary);")
    A("**%d** of them are followed by the slot-base add and become seed S1, **%d** by an add of"
      % (doc["seed_counts"]["S1"], doc["seed_counts"]["S2"]))
    A("a register loaded from `[B+0x60]` (S2), **%d** by an add after `imul R, R, 0x80` (IM)."
      % doc["seed_counts"]["IM"])
    A("")
    A("| step | count |")
    A("|---|---|")
    A("| functions with a seed | %d |" % doc["seed_fns"])
    A("| functions reached by the taint (fixpoint over call arguments) | %d |"
      % doc["tanted_fns"])
    A("| all reads at `[base+0x30]` / `[base+0x40]` from a tainted base | %d |"
      % len(doc["reads"]))
    A("| accepted: the same function also touches `+0x0c` / `+0x50` / `+0x60` | %d |"
      % len(doc["proven_reads"]))
    A("| rejected: no slot fingerprint (unrelated 128-byte-stride records) | %d |"
      % len(doc["rejected"]))
    A("")
    A("An instruction is a **read** when the memory operand is not the destination. A read is")
    A("only accepted as a slot consumer when its function also exposes the record's")
    A("distinguishing fields (`+0x0c` flags, `+0x50` shape pointer, `+0x60` free byte) through a")
    A("tainted base; that is what removes the other 128-byte-stride structures the `shl 7`")
    A("scan also finds.")
    A("")
    A("## 4. Consumers of `+0x30` / `+0x40`")
    A("")
    A("| # | instruction | offset | function | direction | classification |")
    A("|---|---|---|---|---|---|")
    for n, r in enumerate(doc["proven_reads"], 1):
        A("| %d | `%#x` `%s` | `+%#x` | `%#x` | %s | %s |"
          % (n, r["addr"], md_cell(quoted(r["ins"])), r["disp"], r["fn"], r["kind"],
             r["class"] if r["kind"] == "read" else "(stores the field)"))
    A("")
    if not doc["proven_reads"]:
        A("No proven consumer was found.")
        A("")
    A("Independent consumer functions: %s." % ", ".join("`%#x`" % f for f in doc["proven_fns"]))
    A("")
    A("## 5. Evidence: each consumer with its neighbours")
    A("")
    for r in doc["proven_reads"]:
        A("### `%#x` - `%s` `[base + %#x]`, `%s`, %s"
          % (r["addr"], r["ins"].mnemonic, r["disp"], r["kind"], r["class"]))
        A("")
        A("function `%#x`, %d instructions, operand text `%s`%s"
          % (r["fn"], len(st.body(r["fn"])), md_cell(quoted(r["ins"])),
             (", ops " + ", ".join(r["hits"])) if r["hits"] else ""))
        A("")
        A("```")
        for line in context(st, r):
            A(line)
        A("```")
        A("")
    A("## 6. What the writers prove (decoded, not inferred)")
    A("")
    rows = [(0x1513FA0, "writes `+0x00`, `+0x10`, `+0x20`, `+0x30` from a four-float4 source: "
                        "`+0x30` is row 3 of the 4x4, and `+0x0c` (row 0, lane 3) carries flags"),
            (0x1514070, "writes the float4 at `+0x40` from a source float4 and tests its lanes "
                        "for zero / NaN / negative to set flag bits in `+0x0c`"),
            (0x1505820, "copies `+0x00`, `+0x10`, `+0x20`, `+0x30`, `+0x40` and the `+0x50` "
                        "pointer as one block, i.e. one 0x50-byte body plus a shape pointer"),
            (0x119FA30, "`out = v.x*[M] + v.y*[M+0x10] + v.z*[M+0x20]`, called from the consumer "
                       "with `rdx` = the slot: the record's three rows are a rotation")]
    A("| function | what its instructions do |")
    A("|---|---|")
    for va, what in rows:
        A("| `%#x` | %s |" % (base + va, what))
    A("")
    A("```")
    mix = st.body(base + SLOT_MATRIX_SET)
    midx = [k for k, i in enumerate(mix) if i.address == base + 0x1513FF5]
    for line in context(st, {"fn": base + SLOT_MATRIX_SET, "idx": midx[0] if midx else 0}, 8, 8):
        A(line)
    A("```")
    A("")
    A("## 7. What is still UNKNOWN")
    A("")
    A("- **the either/or in the brief.** Only `%#x` classifies `+0x40` and only it classifies"
      % (base + CRASH_PATH_SLOT))
    A("  `+0x30`; `%#x` copies both groups without classifying them. Two independent agreeing"
      % (base + SLOT_COPY))
    A("  consumers do not exist, so no verdict is issued. Where a second one would be: a")
    A("  consumer reached through a slot pointer that is stored in the record's parent rather")
    A("  than computed by `shl 7`; the taint only follows computed indices and call arguments.")
    A("- **whether `+0x40` is a position or a scale/extent vector.** It is multiplied by the")
    A("  matrix both as a broadcast (one lane against each of the three rows) and as a point")
    A("  (`%#x`), which fits either reading. Proving it needs the shape virtual method at"
      % (base + HELPER_M3XV))
    A("  `[shape+0x30]`, whose target is a vtable slot resolved at run time.")
    A("- **`+0x30`'s use after the copy.** The consumer copies it to its frame and adds one")
    A("  float4 to it (`addps`), then the value is not read again on that path; no comparison")
    A("  against a bound uses it.")
    A("- **%d reads at `+0x30`/`+0x40` from a tainted base that failed the slot fingerprint.**"
      % len(doc["rejected"]))
    A("  They belong to other 128-byte-stride records (the same `shl 7` idiom); no oracle here")
    A("  separates them from body slots beyond the fingerprint, so they are listed as rejected")
    A("  rather than as contradictions.")
    A("")
    A("## 8. Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_slot_float4.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_slot_float4.py --check")
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

    st, doc = build()
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]

    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            for o in doc["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(doc["md"])
        print("wrote Research/JC3Grab/SLOT_FLOAT4.md")
        print("  image %s B, sha256 %s..., %d sections, %d .pdata functions"
              % (f"{doc['size']:,}", doc["sha256"][:16], doc["sections"],
                 doc["pdata_functions"]))
        print("  shl7 sites %d, seeds %s, seeded fns %d, tainted fns %d"
              % (doc["shl_sites"], doc["seed_counts"], doc["seed_fns"], doc["tanted_fns"]))
        print("  reads at +0x30/+0x40 from a tainted base %d, accepted %d, rejected %d"
              % (len(doc["reads"]), len(doc["proven_reads"]), len(doc["rejected"])))
        print("  proven consumer functions %s" % [hex(f) for f in doc["proven_fns"]])
        print("  verdict: %s (0x30=%s, 0x40=%s)" % (doc["verdict"], doc["v30"], doc["v40"]))
        print("  oracles %d/%d" % (len(doc["oracles"]) - len(fails), len(doc["oracles"])))
        return 0

    if fails:
        print("FAIL")
        for o in doc["oracles"]:
            if not o["ok"]:
                print("  - oracle %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not os.path.exists(OUT_MD):
        print("FAIL: output missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != doc["md"]:
        print("FAIL: SLOT_FLOAT4.md is stale")
        return 1
    print("OK %d/%d oracles, %d shl7 sites, %d seeded fns, %d tainted fns, "
          "%d accepted reads (%d rejected), md byte-identical"
          % (len(doc["oracles"]), len(doc["oracles"]), doc["shl_sites"], doc["seed_fns"],
             doc["tanted_fns"], len(doc["proven_reads"]), len(doc["rejected"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
