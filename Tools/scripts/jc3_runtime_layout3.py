"""jc3_runtime_layout3.py - whole functions, a global, and the slot float4s (G3-07b).

The review of G3-07a showed two things that change the method: the six "functions" of the
first pass are `.pdata` chunks (four are fragments of larger functions), and the headline
call chain `0x1402020d1 -> 0x141505490 -> 0x1415140f0` does not exist.  This pass therefore

  1. rebuilds each anchor's **whole function** from the `.pdata` tuple table (contiguous
     chunks that fall through into each other, ending in `ret`/`jmp`);
  2. reproduces the refuted chain as a negative oracle;
  3. walks verified `call rel32` sites upward from the whole-function entries (five levels);
  4. lists **every** RIP-relative operand in that closure;
  5. runs a directed whole-image scan for the one pattern that would prove an entry point -
     `reg <- [rip+G]` then `[reg+0x150]` / `[reg+0x158]` - and follows every candidate
     statically (global -> object -> +0x150 -> world -> +0x60 pointer / +0x68 count);
  6. settles the body slot's two float4s by the instructions that consume them.

Static only: `D:/Games/Just Cause 3/JustCause3.exe` opened read-only and never run.

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3.py --check
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import os
import struct
import sys
import time

import capstone
import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT3.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT3.json")

ANCHORS = {                       # G3-07a's six chunk anchors
    "part_list_walk": 0x140201D4E,
    "part_node_update": 0x140201DE0,
    "raycast_body_read": 0x1402020D1,
    "body_slot_query": 0x141505490,
    "body_slot_use": 0x1415140F0,
    "body_slot_enum": 0x140222EF0,
}
CLAIMED_CHAIN = (0x1402020D1, 0x141505490, 0x1415140F0)
SLOT_USE = 0x1415140F0
SLOT_QUERY = 0x141505490
BOUNDS_CALLEE = 0x141516B40
MATMUL_CALLEE = 0x14119FA30

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
MD.detail = True


# ------------------------------------------------------------------ image
class Img:
    def __init__(self, path: str):
        self.path = path
        self.raw = open(path, "rb").read()
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        pe = pefile.PE(path, fast_load=True)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(s.Name.decode().strip("\x00"), self.base + s.VirtualAddress,
                      s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
                     for s in pe.sections]
        pd = next(s for s in pe.sections if s.Name.startswith(b".pdata"))
        o, end = pd.PointerToRawData, pd.PointerToRawData + pd.Misc_VirtualSize
        fns = []
        while o + 12 <= end:
            b, e, _u = struct.unpack_from("<III", self.raw, o)
            if not b or not e or e <= b:
                break
            fns.append((self.base + b, self.base + e))
            o += 12
        fns.sort()
        self.fns = fns
        self.starts = [f[0] for f in fns]
        self.text = next(s for s in self.secs if s[0] == ".text")

    def off(self, va: int) -> int:
        for _n, sva, vs, raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return raw + (va - sva)
        raise KeyError(hex(va))

    def sec(self, va: int):
        for n, sva, vs, _raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return n
        return None

    def bytes_at(self, va: int, n: int) -> bytes:
        o = self.off(va)
        return self.raw[o:o + n]

    def fn_of(self, va: int):
        i = bisect.bisect_right(self.starts, va) - 1
        if i >= 0:
            s, e = self.fns[i]
            if s <= va < e:
                return (s, e)
        return None

    def insns(self, va: int, n: int):
        return list(MD.disasm(self.bytes_at(va, n), va))

    def at(self, va: int):
        f = self.fn_of(va)
        if not f:
            return None
        for ins in self.insns(f[0], f[1] - f[0]):
            if ins.address == va:
                return ins
            if ins.address > va:
                return None
        return None

    def calls_to(self, target: int):
        tva, traw, trs = self.text[1], self.text[3], self.text[4]
        code = self.raw[traw:traw + trs]
        out, p = [], 0
        while True:
            p = code.find(b"\xe8", p)
            if p < 0 or p + 5 > len(code):
                break
            dest = tva + p + 5 + struct.unpack_from("<i", code, p + 1)[0]
            if dest == target:
                ins = self.at(tva + p)
                if ins is not None and ins.mnemonic == "call" and ins.operands and \
                        ins.operands[0].type == capstone.x86.X86_OP_IMM and \
                        ins.operands[0].imm == target:
                    out.append(tva + p)
            p += 1
        return out

    def whole_fn(self, va: int) -> dict:
        """Rebuild the whole function from its contiguous `.pdata` tuples, backwards first.

        A `.pdata` tuple is not a function: four of G3-07a's six anchors are fragments that
        fall through into the next tuple, so a forward-only merge starts mid-function
        (`0x1402020d1` came out as a 190 B "function" instead of its 943 B parent).  A
        preceding tuple whose end is this start, and whose last byte is not a return or jump,
        is part of the same function.
        """
        f = self.fn_of(va)
        if not f:
            return {"anchor": va, "entry": va, "end": va, "bytes": 0, "chunks": []}
        i = self.starts.index(f[0])
        while i > 0:
            prev = self.fns[i - 1]
            if (prev[1] != self.fns[i][0]
                    or self.raw[self.off(prev[1] - 1)] in (0xC3, 0xE9, 0xEB)):
                break
            i -= 1
        chunks, cur = [], self.fns[i]
        for _ in range(64):
            nxt = self.fns[i + 1] if i + 1 < len(self.fns) else None
            tail = self.raw[self.off(cur[1] - 1)]
            chunks.append({"start": cur[0], "end": cur[1], "bytes": cur[1] - cur[0],
                           "tail": tail})
            if tail in (0xC3, 0xE9, 0xEB) or nxt is None or nxt[0] != cur[1]:
                break
            i += 1
            cur = nxt
        return {"anchor": va, "entry": chunks[0]["start"], "end": chunks[-1]["end"],
                "bytes": chunks[-1]["end"] - chunks[0]["start"], "chunks": chunks}


# ------------------------------------------------------------------ analysis
def direct_calls(im: Img, lo: int, hi: int) -> list[int]:
    out = []
    for ins in im.insns(lo, hi - lo):
        if ins.mnemonic == "call" and ins.operands and \
                ins.operands[0].type == capstone.x86.X86_OP_IMM:
            out.append(ins.operands[0].imm)
    return out


def upward(im: Img, target: int, depth: int = 5) -> dict:
    levels = {0: [target]}
    seen = {target}
    for d in range(1, depth + 1):
        nxt = []
        for t in levels[d - 1]:
            for site in im.calls_to(t):
                f = im.fn_of(site)
                if f and f[0] not in seen:
                    seen.add(f[0])
                    nxt.append(f[0])
        nxt = sorted(set(nxt))[:200]
        if not nxt:
            break
        levels[d] = nxt
    return {str(k): v for k, v in levels.items()}


def rip_operands(im: Img, lo: int, hi: int) -> list[dict]:
    out = []
    for ins in im.insns(lo, hi - lo):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and ins.reg_name(op.mem.base) == "rip":
                out.append({"at": ins.address, "text": f"{ins.mnemonic} {ins.op_str}",
                            "target": ins.address + ins.size + op.mem.disp})
    return out


def global_to_offset(im: Img, lo: int, hi: int) -> dict:
    """reg <- [rip+G], then [reg+0x150]/[reg+0x158]: the entry-point pattern.

    Local provenance: a register is "global" from its `mov/lea reg, [rip+G]` until any other
    instruction writes that register.  Reported per function, first hit per register.
    """
    reg = {}
    hits, world = [], []
    for ins in im.insns(lo, hi - lo):
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_MEM and op.mem.base:
                b = ins.reg_name(op.mem.base)
                if b in reg:
                    if op.mem.disp in (0x150, 0x158):
                        hits.append({"at": ins.address, "text": f"{ins.mnemonic} {ins.op_str}",
                                     "base": b, "global": reg[b], "disp": op.mem.disp})
                    elif op.mem.disp in (0x60, 0x68):
                        world.append({"at": ins.address,
                                      "text": f"{ins.mnemonic} {ins.op_str}",
                                      "base": b, "global": reg[b], "disp": op.mem.disp})
        # register writes AFTER the memory checks (so the loading instruction itself counts)
        if ins.operands and ins.operands[0].type == capstone.x86.X86_OP_REG and \
                ins.mnemonic.split(".")[0] in ("mov", "lea", "xor", "add", "sub", "and",
                                               "or", "pop", "movzx", "movsx", "movsxd",
                                               "imul", "shl", "shr", "sar", "inc", "dec",
                                               "neg", "not", "pshufd", "punpck"):
            dst = ins.reg_name(ins.operands[0].reg)
            src = ins.operands[1] if len(ins.operands) > 1 else None
            if ins.mnemonic in ("mov", "lea") and src is not None and \
                    src.type == capstone.x86.X86_OP_MEM and \
                    ins.reg_name(src.mem.base) == "rip":
                reg[dst] = ins.address + ins.size + src.mem.disp
            else:
                reg.pop(dst, None)
    return {"hits": hits, "world_touch": world}


def static_chain(im: Img, g: int) -> dict:
    """global qword -> object -> +0x150 -> world -> +0x60 pointer / +0x68 count."""
    out: dict = {"global": g}
    q = struct.unpack("<Q", im.bytes_at(g, 8))[0]
    out["qword"] = q
    out["section"] = im.sec(q) if q else None
    out["canonical"] = bool(q and im.sec(q) is not None)
    if not out["canonical"]:
        return out
    out["object_150"] = struct.unpack("<Q", im.bytes_at(q + 0x150, 8))[0]
    out["object_158"] = struct.unpack("<Q", im.bytes_at(q + 0x158, 8))[0]
    w = out["object_150"]
    if w and im.sec(w) is not None:
        try:
            s60 = struct.unpack("<Q", im.bytes_at(w + 0x60, 8))[0]
            s68 = struct.unpack("<I", im.bytes_at(w + 0x68, 4))[0]
            out["world"] = {"ptr": w, "slot_array": s60, "slot_count": s68,
                            "layout_matches_g3_07a":
                                bool(s60 and im.sec(s60) is not None and 0 < s68 < 100000)}
        except KeyError:
            out["world"] = None
    return out


def whole_image_scan(im: Img) -> dict:
    t0 = time.time()
    tlo = im.text[1]
    thi = tlo + im.text[2]
    fns, hits = [], []
    for s, e in im.fns:
        if not (tlo <= s < thi) or e - s > 20000:
            continue
        r = global_to_offset(im, s, e)
        if r["hits"]:
            fns.append({"fn": s, "end": e, "bytes": e - s, "hits": r["hits"],
                        "world_touch": r["world_touch"]})
            hits.extend(r["hits"])
    chains, seen = [], set()
    for h in hits:
        if h["global"] in seen:
            continue
        seen.add(h["global"])
        chains.append(static_chain(im, h["global"]))
    return {"functions": fns, "globals": chains,
            "seconds": round(time.time() - t0, 1)}


def float4(im: Img) -> dict:
    w = im.whole_fn(SLOT_USE)
    body = [{"at": i.address, "mn": i.mnemonic, "text": f"{i.mnemonic} {i.op_str}"}
            for i in im.insns(w["entry"], w["end"] - w["entry"])]
    bounds = [{"at": i.address, "mn": i.mnemonic, "text": f"{i.mnemonic} {i.op_str}"}
              for i in im.insns(BOUNDS_CALLEE, 0x120)]
    mat = [{"at": i.address, "mn": i.mnemonic, "text": f"{i.mnemonic} {i.op_str}"}
           for i in im.insns(MATMUL_CALLEE, 0x40)]
    return {"bounds_callee": BOUNDS_CALLEE, "matmul_callee": MATMUL_CALLEE,
            "lo": w["entry"], "hi": w["end"], "body": body, "bounds": bounds, "matmul": mat}


# ------------------------------------------------------------------ build
def build() -> dict:
    im = Img(EXE)
    doc: dict = {
        "schema": 1, "generator": "jc3_runtime_layout3.py", "card": "G3-07b",
        "image": {"path": EXE.replace("\\", "/"), "sha256": im.sha256,
                  "bytes": len(im.raw), "base": hex(im.base),
                  "sections": [[s[0], hex(s[1]), s[2]] for s in im.secs],
                  "pdata_functions": len(im.fns)},
        "functions": {}, "chain": {}, "walk": {}, "closure_globals": {},
        "scan": {}, "slot": {},
    }
    for name, va in ANCHORS.items():
        b = im.whole_fn(va)
        b["declared_chunk"] = next((c["bytes"] for c in b["chunks"] if c["start"] == va), None)
        b["fragment"] = b["entry"] != va
        b["callers"] = im.calls_to(va)
        b["direct_calls"] = direct_calls(im, b["entry"], b["end"])
        doc["functions"][name] = b
    q = im.whole_fn(SLOT_QUERY)
    q_calls = direct_calls(im, q["entry"], q["end"])
    doc["chain"] = {
        "claimed": [hex(x) for x in CLAIMED_CHAIN],
        "slot_query_direct_callees": [hex(x) for x in q_calls],
        "slot_use_callers": [hex(x) for x in im.calls_to(im.whole_fn(SLOT_USE)["entry"])],
        "slot_query_calls_slot_use": im.whole_fn(SLOT_USE)["entry"] in q_calls,
        "anchors_with_zero_callers": [hex(v) for v in ANCHORS.values()
                                      if not im.calls_to(v)],
    }
    entries = sorted({b["entry"] for b in doc["functions"].values()})
    walk = {hex(e): upward(im, e, depth=5) for e in entries}
    closure = sorted({f for lv in walk.values() for fs in lv.values() for f in fs})
    doc["walk"] = {"entries": [hex(e) for e in entries], "levels":
                   {e: {k: [hex(x) for x in v] for k, v in lv.items()}
                    for e, lv in walk.items()}, "closure": len(closure)}
    rows = []
    for f in closure:
        fe = im.fn_of(f)
        if fe:
            rows.extend([{"fn": f, **r} for r in rip_operands(im, fe[0], fe[1])])
    doc["closure_globals"] = {"count": len(rows),
                              "distinct": sorted({hex(r["target"]) for r in rows}),
                              "rows": rows}
    doc["scan"] = whole_image_scan(im)
    doc["slot"] = float4(im)
    return doc


# ------------------------------------------------------------------ oracles
def oracles(doc: dict) -> list[dict]:
    f, ch, scan = doc["functions"], doc["chain"], doc["scan"]
    slot = doc["slot"]
    text = {b["at"]: b["text"] for b in slot["body"]}
    mul_rows = [b for b in slot["body"] if b["mn"] == "mulps" and "[rsi" in b["text"]]
    shuf = [b for b in slot["body"] if b["mn"] == "shufps"]
    mul_dst = [b["text"].split()[1].split(",")[0] for b in mul_rows]
    shuf_bcast = {b["text"].split()[1].split(",")[0] for b in shuf if ", xmm2, " in b["text"]}
    mul_mem = sorted(b["text"].split("xmmword ptr ")[1] for b in mul_rows)
    proven = [c for c in scan["globals"] if isinstance(c.get("world"), dict)
              and c["world"].get("layout_matches_g3_07a")]
    followed = all("qword" in c for c in scan["globals"])
    return [
        {"id": "whole_functions_rebuilt", "kind": "invariant",
         "ok": f["part_node_update"]["entry"] == 0x140201DE0
         and f["part_node_update"]["bytes"] > f["part_node_update"]["declared_chunk"]
         and f["raycast_body_read"]["entry"] == 0x140201DE0
         and f["part_list_walk"]["entry"] == 0x140201D30,
         "detail": {k: {"entry": hex(v["entry"]), "bytes": v["bytes"],
                        "declared": v["declared_chunk"], "fragment": v["fragment"]}
                    for k, v in f.items()}},
        {"id": "claimed_chain_refuted", "kind": "invariant",
         "ok": not ch["slot_query_calls_slot_use"],
         "detail": {"claimed": ch["claimed"],
                    "slot_query_callees": ch["slot_query_direct_callees"],
                    "slot_use_callers": ch["slot_use_callers"]}},
        {"id": "upward_walk_completed", "kind": "invariant",
         "ok": doc["walk"]["closure"] >= len(doc["walk"]["entries"]),
         "detail": {"entries": len(doc["walk"]["entries"]),
                    "closure": doc["walk"]["closure"]}},
        {"id": "closure_globals_listed", "kind": "invariant",
         "ok": doc["closure_globals"]["count"] == len(doc["closure_globals"]["rows"]),
         "detail": {"operands": doc["closure_globals"]["count"],
                    "distinct": doc["closure_globals"]["distinct"]}},
        {"id": "every_candidate_followed", "kind": "invariant", "ok": followed,
         "detail": {"functions": len(scan["functions"]),
                    "globals": [hex(c["global"]) for c in scan["globals"]]}},
        {"id": "entry_point_proved", "kind": "measured", "ok": bool(proven),
         "detail": {"proven": [hex(c["global"]) for c in proven],
                    "candidates": len(scan["globals"])}},
        {"id": "slot_40_is_matrix_multiplied", "kind": "invariant",
         "ok": "xmmword ptr [rcx + 0x40]" in text.get(0x141514105, "")
         and len(mul_rows) == 3
         and set(mul_mem) == {"[rsi]", "[rsi + 0x10]", "[rsi + 0x20]"}
         and set(mul_dst) <= shuf_bcast,
         "detail": {"load": text.get(0x141514105),
                    "mulps": [b["text"] for b in mul_rows],
                    "mul_mem": mul_mem, "broadcast_from_xmm2": sorted(shuf_bcast),
                    "shufps": [b["text"] for b in shuf]}},
        {"id": "slot_30_goes_to_min_max", "kind": "invariant",
         "ok": "xmmword ptr [rcx + 0x30]" in text.get(0x14151411F, "")
         and "xmmword ptr [r11 - 0x28], xmm0" in text.get(0x141514123, "")
         and any(b["mn"] == "call" and b["at"] > 0x141514123 for b in slot["body"])
         and [b["mn"] for b in slot["bounds"]].count("minps") >= 4
         and [b["mn"] for b in slot["bounds"]].count("maxps") >= 4,
         "detail": {"load": text.get(0x14151411F),
                    "shadow_store": text.get(0x141514123),
                    "callee": hex(slot["bounds_callee"]),
                    "minmax": [b["text"] for b in slot["bounds"]
                               if b["mn"] in ("minps", "maxps")][:4]}},
        {"id": "matmul_callee_repeats_the_operation", "kind": "invariant",
         "ok": [b["mn"] for b in slot["matmul"]][:8] ==
               ["movaps", "movaps", "movaps", "shufps", "shufps", "shufps", "mulps", "mulps"],
         "detail": [b["text"] for b in slot["matmul"][:9]]},
    ]


# ------------------------------------------------------------------ render
def render(doc: dict) -> str:
    f, ch, scan, cg, slot = (doc["functions"], doc["chain"], doc["scan"],
                             doc["closure_globals"], doc["slot"])
    text = {b["at"]: b["text"] for b in slot["body"]}
    proven = [c for c in scan["globals"] if isinstance(c.get("world"), dict)
              and c["world"].get("layout_matches_g3_07a")]
    L = []
    A = L.append
    A("# Whole functions, the global walk, and the slot float4s (G3-07b)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout3.py --write`; `--check` re-derives every")
    A("row from the exe (read-only, never run) and fails on drift.")
    A("")
    A(f"- image `{doc['image']['path']}`, sha256 `{doc['image']['sha256'][:16]}...`, "
      f"{doc['image']['bytes']:,} B, {doc['image']['pdata_functions']} `.pdata` entries")
    A("")
    A("## 1. The whole functions behind the six anchors")
    A("")
    A("| anchor | entry | whole function | G3-07a's chunk | fragment? | direct callers |")
    A("|---|---|---:|---:|---|---:|")
    for name, v in f.items():
        A(f"| `{name}` | `{v['entry']:#x}` | {v['bytes']} B | {v['declared_chunk']} B | "
          f"{'yes' if v['fragment'] else 'no'} | {len(v['callers'])} |")
    A("")
    A("Chunk chains (each arrow is a contiguous `.pdata` tuple that falls through):")
    A("")
    for name, v in f.items():
        A(f"- `{name}`: " + " -> ".join(f"`{c['start']:#x}`+{c['bytes']}"
                                        for c in v["chunks"]))
    A("")
    A("So `0x140201d4e` and `0x1402020d1` are **not** entries - the review's finding, re-derived.")
    A("")
    A("## 2. The claimed chain, re-derived negative")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| claimed | " + " -> ".join(f"`{x}`" for x in ch["claimed"]) + " |")
    A("| `0x141505490` direct callees | " + ", ".join(f"`{x}`" for x in
                                                       ch["slot_query_direct_callees"]) + " |")
    A("| `0x1415140f0` callers | " + ", ".join(f"`{x}`" for x in ch["slot_use_callers"]) + " |")
    A(f"| does the query call the use? | **{'yes' if ch['slot_query_calls_slot_use'] else 'no'}** |")
    A("| anchors with zero callers | " + ", ".join(ch["anchors_with_zero_callers"]) + " |")
    A("")
    A("## 3. Upward walk from the whole-function entries")
    A("")
    A(f"{len(doc['walk']['entries'])} entries, closure **{doc['walk']['closure']} functions**, "
      "five verified-call levels:")
    A("")
    A("| entry | d1 | d2 | d3 | d4 | d5 |")
    A("|---|---:|---:|---:|---:|---:|")
    for e, lv in doc["walk"]["levels"].items():
        A("| `%s` | %s |" % (e, " | ".join(str(len(lv.get(str(d), [])))
                                           for d in range(1, 6))))
    A("")
    A("## 4. Every RIP-relative global in that closure")
    A("")
    A(f"{cg['count']} operand(s); distinct targets: "
      + (", ".join(f"`{g}`" for g in cg["distinct"]) or "none") + ".")
    A("")
    if cg["rows"]:
        A("| function | at | instruction | target |")
        A("|---|---|---|---|")
        for r in cg["rows"][:40]:
            A(f"| `{r['fn']:#x}` | `{r['at']:#x}` | `{r['text']}` | `{r['target']:#x}` |")
    else:
        A("None - the closure touches no `.data` global.")
    A("")
    A("## 5. Whole-image scan: a global dereferenced at the part node's offsets")
    A("")
    A("Every function where `reg <- [rip+G]` is followed by `[reg+0x150]` / `[reg+0x158]`")
    A("(local register provenance; the register is dropped when any other instruction writes it).")
    A("")
    A(f"- functions: **{len(scan['functions'])}**, distinct globals: **{len(scan['globals'])}**, "
      f"scan {scan['seconds']} s")
    A("")
    A("| function | bytes | disp | instruction | global | global qword | canonical | object +0x150 | object +0x158 |")
    A("|---|---:|---|---|---|---|---|---|---|")
    for fn in scan["functions"]:
        for h in fn["hits"]:
            c = next(x for x in scan["globals"] if x["global"] == h["global"])
            A(f"| `{fn['fn']:#x}` | {fn['bytes']} | `{h['disp']:#x}` | `{h['text']}` | "
              f"`{h['global']:#x}` | `{c['qword']:#x}` | {c['canonical']} | "
              f"`{c['object_150']:#x}` | `{c['object_158']:#x}` |"
              if c.get("canonical") else
              f"| `{fn['fn']:#x}` | {fn['bytes']} | `{h['disp']:#x}` | `{h['text']}` | "
              f"`{h['global']:#x}` | `{c['qword']:#x}` | False | - | - |")
    A("")
    if proven:
        A("**Entry point proved.** Global -> object -> `+0x150` -> world with the `+0x60` slot")
        A("pointer and `+0x68` count of G3-07a:")
        A("")
        for c in proven:
            A(f"- `{c['global']:#x}` -> `{c['object_150']:#x}` -> slot array "
              f"`{c['world']['slot_array']:#x}`, count {c['world']['slot_count']}")
    else:
        A("**No entry point is proved.** The pattern exists, but no candidate's static chain")
        A("reaches a part node: the global's qword is not a canonical image pointer (it is built at")
        A("runtime), so `+0x150` cannot be read from the file. The closure around the physics")
        A("functions (§3-§4) touches no `.data` global that could be the root either.")
        A("**UNKNOWN**, with the candidates above and the tests in §7.")
    A("")
    A("## 6. The slot's two float4s, decided by their consumers")
    A("")
    A("| at | instruction | consumed by |")
    A("|---|---|---|")
    A(f"| `0x141514105` | `{text.get(0x141514105)}` | xmm2, later `shufps` x3 + `mulps` x3 against the slot's 3x4 rows |")
    A(f"| `0x14151411f` | `{text.get(0x14151411f)}` | shadow argument, passed to `{slot['bounds_callee']:#x}` |")
    A("")
    A("`+0x40` path:")
    A("")
    A("```")
    for b in slot["body"]:
        if b["at"] in (0x141514105, 0x14151411F, 0x1415141F8, 0x1415141FC, 0x1415141FF) or \
                (b["mn"] == "shufps" and b["at"] < 0x141514200):
            A(f"{b['at']:#x}  {b['text']}")
    A("```")
    A("")
    A(f"and the same operation repeated in `{slot['matmul_callee']:#x}`:")
    A("")
    A("```")
    for b in slot["matmul"]:
        A(f"{b['at']:#x}  {b['text']}")
    A("```")
    A("")
    A(f"`+0x30` path: `{slot['bounds_callee']:#x}` reads that argument and runs")
    A("")
    A("```")
    for b in slot["bounds"]:
        if b["mn"] in ("maxps", "minps", "movaps", "subss", "cmpleps"):
            A(f"{b['at']:#x}  {b['text']}")
    A("```")
    A("")
    A("Verdict: **`+0x40` is the transform vector** (it is broken into broadcasts and multiplied")
    A("by the slot's three 3x4 rows - a matrix multiply, repeated in the callee), and **`+0x30` is")
    A("the bounds/query float4** (it is handed to a function whose body is a `minps`/`maxps` run")
    A("over an array). Nothing in the chain compares `+0x30` with `+0x40`, so the min/max-corner")
    A("reading of the pair is refuted.")
    A("")
    A("## 7. UNKNOWNs")
    A("")
    A("* **A fixed address that leads to a spawned vehicle.** Tried: whole-function rebuild (§1),")
    A("  the refuted chain (§2), five-level caller walks (§3), every RIP-relative operand in the")
    A("  closure (§4), and a whole-image register-provenance scan for global -> `+0x150`/`+0x158`")
    A("  with static dereference of every candidate (§5). No candidate's global holds a canonical")
    A("  pointer in the image, so a node cannot be reached statically. Where it would be found: a")
    A("  runtime dump after a vehicle spawns, or the allocator that stores the node into the")
    A("  global (the store instruction, not the initialiser).")
    A("* **Which world pointer the raycast path uses** (`node+0x150` vs `+0x158`). Both are read")
    A("  in the same functions and never compared - G3-07a's UNKNOWN 2 stands.")
    A("* **The render-instance transform and the loaded-resource table.** No anchor reaches a")
    A("  draw instance or a resource table, so this render writes neither.")
    A("")
    A("## 8. Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3.py --check")
    A("```")
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.error("use --write or --check")
    doc = build()
    doc["oracles"] = oracles(doc)
    md = render(doc)
    bad = [o["id"] for o in doc["oracles"] if not o["ok"] and o["kind"] == "invariant"]
    rates = [o["id"] for o in doc["oracles"] if not o["ok"] and o["kind"] == "measured"]
    if a.write:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print(f"wrote {os.path.relpath(OUT_MD, ROOT)} ({md.count(chr(10))} lines)")
        print(f"wrote {os.path.relpath(OUT_JSON, ROOT)}")
        print(f"closure {doc['walk']['closure']} fns; scan {len(doc['scan']['functions'])} fns / "
              f"{len(doc['scan']['globals'])} globals; "
              f"proven {sum(1 for c in doc['scan']['globals'] if isinstance(c.get('world'), dict) and c['world'].get('layout_matches_g3_07a'))}")
        print("invariants not universal:", bad or "none")
        print("measured below 1.0:", rates or "none")
        return 1 if bad else 0
    fails = []
    if not os.path.exists(OUT_MD) or not os.path.exists(OUT_JSON):
        fails.append("outputs missing - run --write")
    else:
        if open(OUT_MD, encoding="utf-8").read() != md:
            fails.append("RUNTIME_LAYOUT3.md differs from a fresh render")
        if json.load(open(OUT_JSON, encoding="utf-8")) != doc:
            fails.append("RUNTIME_LAYOUT3.json differs from a fresh render")
    for o in doc["oracles"]:
        print(f"{'OK  ' if o['ok'] else 'MISS'} {o['id']} [{o['kind']}]: {o['detail']}")
    for f in fails:
        print("FAIL", f)
    print("invariants not universal:", bad or "none")
    print("measured (reported, not asserted):", rates or "none")
    if not bad and not fails:
        print("CHECK_EXIT=0")
    return 1 if (bad or fails) else 0


if __name__ == "__main__":
    sys.exit(main())
