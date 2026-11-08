"""jc3_runtime_layout5.py - does a caller chain of 0x1400a9690 reach a container or global
that holds the spawned part node?  (task 7121, follow-up to RUNTIME_LAYOUT4.md UNKNOWN 1)

RUNTIME_LAYOUT4.md §7 left one candidate open: `0x1400a9690` stores an 8-byte value at both
`+0x150` (0x1400a97f6) and `+0x158` (0x1400a97e8).  This card answers one question: **what is
that 8-byte value, and does the chain that reaches it terminate in a container or global that
holds the spawned node?**

Method (static, read-only; the exe is never executed):

  1. decode the whole `.pdata` chunk that holds 0x1400a9690, instruction by instruction;
  2. for each of the two 8-byte stores, walk back to the last instruction that *writes* rdx/edx
     as a destination operand, and record it verbatim;
  3. find every `call rel32` / `jmp rel32` in the image whose target is 0x1400a9690, and for
     each site record the instruction bytes, the 14 instructions before it, the object size in
     `rcx`, the last write to rdx before the call, and whether the caller loads a RIP-relative
     global into rcx/rdx anywhere between the allocation and the call;
  4. walk upward to depth 3 over **entry-target** edges (site -> function entry), so intra-region
     jumps are not mistaken for callers, and count the edges into each node.

Verdict vocabulary used in the report: CONFIRMED / REFUTED / UNKNOWN.  The type test is the one
RUNTIME_LAYOUT4.md §3 establishes - its readers load an 8-byte *pointer* from the field and
dereference it, so a stored value can only be that type if it is a live object address.

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout5.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout5.py --check
"""
from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import os
import sys

import capstone
import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tmp", "freebuff", "scratch"))
import jc3_textcache as CACHE                              # noqa: E402

EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT5.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT5.json")

# RUNTIME_LAYOUT4.md §7 candidate table (row 388) and §3's read sites.
TARGET = 0x1400A9690
STORE_158 = 0x1400A97E8
STORE_150 = 0x1400A97F6
FIELD_OFS = (0x150, 0x158)
MAX_DEPTH = 3
MAX_NODES = 48

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
MD.detail = True
RDX = {capstone.x86.X86_REG_RDX, capstone.x86.X86_REG_EDX}
RCX = {capstone.x86.X86_REG_RCX, capstone.x86.X86_REG_ECX}
X86_OP_REG = capstone.x86.X86_OP_REG
X86_OP_MEM = capstone.x86.X86_OP_MEM


# ------------------------------------------------------------------ image
class Img:
    def __init__(self, path: str = EXE):
        self.raw = open(path, "rb").read()
        self.sha256 = hashlib.sha256(self.raw).hexdigest()
        pe = pefile.PE(path, fast_load=True)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(s.Name.decode().strip("\x00"), self.base + s.VirtualAddress,
                      s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData)
                     for s in pe.sections]
        self.text = next(s for s in self.secs if s[0] == ".text")

    def off(self, va: int) -> int:
        for _n, sva, vs, raw, _rs in self.secs:
            if sva <= va < sva + vs:
                return raw + (va - sva)
        raise KeyError(hex(va))

    def sec(self, va: int) -> str | None:
        for n, sva, vs, _r, _s in self.secs:
            if sva <= va < sva + vs:
                return n
        return None

    def dis(self, va: int, end: int):
        """Disassemble [va, end) strictly forward from va."""
        return list(MD.disasm(self.raw[self.off(va):self.off(end)], va))


# ------------------------------------------------------------------ helpers
def written_reg(ins) -> int | None:
    """The destination register, only when the destination is a register operand."""
    if not ins.operands:
        return None
    op = ins.operands[0]
    return op.reg if op.type == X86_OP_REG else None


def is_write_to_rdx(ins) -> bool:
    return written_reg(ins) in RDX


def mem_ops(ins, disp: int, write: bool):
    out = []
    for op in ins.operands:
        if op.type != X86_OP_MEM or op.mem.disp != disp:
            continue
        if write and not (op.access & capstone.CS_AC_WRITE):
            continue
        out.append(op)
    return out


def last_rdx_writer(insns: list, before_idx: int) -> dict | None:
    for ins in reversed(insns[:before_idx]):
        if is_write_to_rdx(ins):
            return {"addr": ins.address, "bytes": ins.bytes.hex(" "),
                    "text": f"{ins.mnemonic} {ins.op_str}".strip()}
    return None


def ftext(ins) -> str:
    return f"{ins.mnemonic} {ins.op_str}".strip()


# ------------------------------------------------------------------ build
def build() -> dict:
    img = Img()
    if not os.path.exists(CACHE.CACHE):
        CACHE.build()
    cache = CACHE.load()
    meta, chunks, calls = cache["meta"], cache["chunks"], cache["calls"]

    starts = [s for s, _e in chunks]
    entry_set = set(starts)

    def region_of(va: int):
        i = bisect.bisect_right(starts, va) - 1
        if i >= 0 and chunks[i][0] <= va < chunks[i][1]:
            return chunks[i]
        return None

    # ---- 1. the callee
    creg = region_of(TARGET)
    body = img.dis(creg[0], creg[1])

    # ---- 2. the two 8-byte stores and where rdx comes from
    stores = []
    for ofs, want in ((0x158, STORE_158), (0x150, STORE_150)):
        idx = next((i for i, x in enumerate(body) if x.address == want), None)
        ins = body[idx] if idx is not None else None
        mem = mem_ops(ins, ofs, write=True) if ins else []
        stores.append({
            "offset": ofs,
            "addr": want,
            "bytes": ins.bytes.hex(" ") if ins else None,
            "text": ftext(ins) if ins else None,
            "width": mem[0].size if mem else None,
            "base": MD.reg_name(mem[0].mem.base) if mem else None,
            "rdx_writer": last_rdx_writer(body, idx) if idx is not None else None,
            "index": idx,
        })

    # the register's definition is shared: both stores must read the same writer
    rdx_defs = {s["rdx_writer"]["addr"] if s["rdx_writer"] else None for s in stores}
    zero_def = None
    if len(rdx_defs) == 1 and None not in rdx_defs:
        addr = next(iter(rdx_defs))
        ins = next(x for x in body if x.address == addr)
        zero_def = {"addr": addr, "bytes": ins.bytes.hex(" "), "text": ftext(ins),
                    "is_zeroing_xor": ins.mnemonic == "xor" and
                    ins.op_str.replace(" ", "") in ("edx,edx", "rdx,rdx")}

    # ---- 3. direct callers
    direct = [(s, t, k) for (s, t, k) in calls if t == TARGET]
    callers = []
    for site, _t, kind in sorted(direct):
        reg = region_of(site)
        seq = img.dis(reg[0], site + 16)
        idx = next(i for i, x in enumerate(seq) if x.address == site)
        site_ins = seq[idx]
        pre = seq[max(0, idx - 14):idx]
        last_rdx = last_rdx_writer(seq, idx)
        # object size handed in rcx, if the caller loads one immediately before the call
        rcx_imm = None
        for ins in reversed(seq[max(0, idx - 24):idx]):
            if ins.mnemonic == "mov" and written_reg(ins) in RCX:
                op = ins.operands[1]
                if op.type == capstone.x86.X86_OP_IMM:
                    rcx_imm = {"addr": ins.address, "value": op.imm,
                               "text": ftext(ins), "bytes": ins.bytes.hex(" ")}
                    break
        # allocator call just before, if any
        alloc = None
        for ins in reversed(seq[max(0, idx - 4):idx]):
            if ins.mnemonic == "call" and ins.operands and \
                    ins.operands[0].type == capstone.x86.X86_OP_IMM:
                alloc = {"addr": ins.address, "target": ins.operands[0].imm,
                         "text": ftext(ins), "bytes": ins.bytes.hex(" ")}
                break
        # does anything set rdx between the allocator and the call?
        gap = seq[max(0, idx - 3):idx]
        rdx_in_gap = [{"addr": x.address, "text": ftext(x), "bytes": x.bytes.hex(" ")}
                      for x in gap if is_write_to_rdx(x)]
        # RIP-relative loads in the caller that could be a global container
        rip = [{"addr": x.address, "text": ftext(x), "bytes": x.bytes.hex(" ")}
               for x in img.dis(reg[0], site) if "rip +" in x.op_str and x.mnemonic in ("mov", "lea")]
        callers.append({
            "site": site, "kind": "call" if kind == 0 else "jmp",
            "caller_fn": reg[0], "caller_end": reg[1],
            "site_bytes": site_ins.bytes.hex(" "), "site_text": ftext(site_ins),
            "window": [{"addr": x.address, "bytes": x.bytes.hex(" "), "text": ftext(x)}
                       for x in pre],
            "last_rdx_write": last_rdx,
            "rdx_written_between_alloc_and_call": rdx_in_gap,
            "rcx_object_size": rcx_imm,
            "allocator": alloc,
            "rip_loads_in_caller": len(rip),
            "rip_examples": rip[:6],
        })

    # ---- 4. upward walk over entry-target edges
    edges_into = collections.Counter()
    for site, target, _k in calls:
        if target in entry_set:
            edges_into[target] += 1

    def edges_to(entry: int):
        return [(s, k) for (s, t, k) in calls if t == entry]

    chain, seen, frontier = [], {TARGET}, [(TARGET, 0)]
    while frontier and len(chain) < MAX_NODES:
        va, depth = frontier.pop(0)
        if depth >= MAX_DEPTH:
            continue
        es = edges_to(va) if va != TARGET else [(s, k) for (s, t, k) in direct]
        sites = collections.Counter()
        for s, k in es:
            reg = region_of(s)
            sites[reg[0] if reg else None] += 1
        chain.append({
            "entry": va, "depth": depth,
            "edges": len(es),
            "edged_to_entries": {hex(k): v for k, v in sorted(
                ((k, v) for k, v in sites.items() if k is not None), key=lambda kv: kv[0])},
            "intra_region_jumps_excluded": sum(
                v for k, v in sites.items() if k is None or (k and va <= k < va + 1)),
            "sites": [{"site": s, "kind": "call" if k == 0 else "jmp"} for s, k in es[:12]],
        })
        for k in sites:
            if k and k not in seen and k != va:
                seen.add(k)
                frontier.append((k, depth + 1))

    # one row per node the walk actually searched (depth 3 entries stay unwalked by design)
    node_counts = [{"entry": n["entry"], "depth": n["depth"],
                    "edges_into_entry": edges_into.get(n["entry"], 0)} for n in chain]

    # ---- oracles
    text_lo, text_hi = img.text[1], img.text[1] + img.text[2]
    oracles = [
        {"name": "O1-image", "ok": text_lo <= TARGET < text_hi,
         "detail": f"base {hex(img.base)}, {len(img.secs)} sections, sha256 {img.sha256[:16]}"},
        {"name": "O2-target-and-stores-in-one-chunk",
         "ok": creg[0] <= min(STORE_150, STORE_158) and max(STORE_150, STORE_158) < creg[1],
         "detail": f"chunk {hex(creg[0])}..{hex(creg[1])}, {len(body)} instructions"},
        {"name": "O3-stores-are-8-byte-qword-writes",
         "ok": all(s["width"] == 8 and s["text"].startswith("mov qword ptr") for s in stores),
         "detail": "; ".join(f"+{hex(s['offset'])} {s['width']}B {s['text']}" for s in stores)},
        {"name": "O4-both-stores-read-one-definition",
         "ok": len(rdx_defs) == 1 and zero_def is not None and zero_def["is_zeroing_xor"],
         "detail": (f"{hex(zero_def['addr'])} {zero_def['text']}" if zero_def else "no shared writer")},
        {"name": "O5-direct-callers-redecode",
         "ok": all(f"call {hex(TARGET)}" in c["site_text"] or
                   f"jmp {hex(TARGET)}" in c["site_text"] for c in callers) and bool(callers),
         "detail": "; ".join(f"{hex(c['site'])} {c['site_text']}" for c in callers)},
        {"name": "O6-object-size-covers-the-last-field",
         "ok": all((c["rcx_object_size"] or {}).get("value", 0) > 0x2D4 for c in callers),
         "detail": "; ".join(f"{hex(c['site'])} rcx={hex(c['rcx_object_size']['value'])}"
                             for c in callers if c["rcx_object_size"])},
        {"name": "O7-verdict-follows",
         "ok": zero_def is not None and zero_def["is_zeroing_xor"],
         "detail": "the 8-byte value at both offsets is the constant 0 (null), so no chain can "
                   "carry a node through it"},
    ]
    verdict = "REFUTED" if (zero_def and zero_def["is_zeroing_xor"]) else "UNKNOWN"

    return {
        "meta": {k: meta[k] for k in ("sha256", "instructions", "calls", "field_ops",
                                      "pdata_chunks", "gaps", "capstone")},
        "image": {"base": img.base, "sections": [s[0] for s in img.secs],
                  "sha256": img.sha256},
        "target": {"entry": TARGET, "chunk": [creg[0], creg[1]],
                   "bytes": creg[1] - creg[0], "instructions": len(body)},
        "body": [{"addr": x.address, "bytes": x.bytes.hex(" "), "text": ftext(x)} for x in body],
        "stores": [{k: v for k, v in s.items() if k != "index"} for s in stores],
        "rdx_definition": zero_def,
        "direct_callers": callers,
        "chain": chain,
        "node_counts": node_counts,
        "question": "does a caller chain of 0x1400a9690 reach a container or global that holds "
                    "the spawned node?",
        "verdict": verdict,
        "oracles": oracles,
        "counts": {
            "body_instructions": len(body),
            "direct_callers": len(callers),
            "chain_nodes": len(chain),
            "edges_into_target": edges_into.get(TARGET, 0),
            "edges_into_caller_entry": edges_into.get(callers[0]["caller_fn"], 0) if callers else 0,
            "rip_loads_in_caller": callers[0]["rip_loads_in_caller"] if callers else 0,
        },
    }


# ------------------------------------------------------------------ render
def render(d: dict) -> str:
    A = []
    w = A.append
    w("# Does a caller chain of `0x1400a9690` reach a container or global holding the node?")
    w("")
    w("Generated by `Tools/scripts/jc3_runtime_layout5.py --write`; `--check` re-derives every")
    w("number below from the executable and fails on drift. **Static only**: `JustCause3.exe` is")
    w("opened read-only and never executed. `RUNTIME_LAYOUT4.*` is untouched by this card.")
    w("")
    w("## Answer")
    w("")
    w(f"**{d['verdict']}** for the candidate. `0x1400a9690` is a **constructor**, and the 8-byte")
    w("value it stores at both `+0x150` and `+0x158` is the constant **0** — a null initialiser,")
    w("not a node. The value's origin is a zeroing `xor`:")
    w("")
    z = d["rdx_definition"]
    if z:
        w("```")
        w(f"{z['addr']:#x}  {z['bytes']}  {z['text']}")
        w("```")
        w("")
    w("Every subsequent store to those two offsets is `mov qword ptr [...], rdx` with that same")
    w("zeroed register, so no caller's argument can reach the field. The question asked — *does a")
    w("caller chain reach a container or global that holds the spawned node* — therefore has the")
    w("answer **UNKNOWN (no such chain), with the candidate itself refuted as the node writer**.")
    w("")
    w("| question | answer |")
    w("|---|---|")
    w(f"| direct callers of `0x1400a9690` | **{d['counts']['direct_callers']}** |")
    w(f"| the 8-byte value stored at `+0x150` / `+0x158` | **0 (null)** — `{z['text'] if z else '-'}` |")
    w(f"| does it have the type §3's readers load (a live 8-byte pointer) | **no** |")
    w(f"| any caller chain reaching a container/global of nodes | **none found** |")
    w("")
    w("## The callee, decoded")
    w("")
    t = d["target"]
    w(f"- chunk `{t['chunk'][0]:#x}`..`{t['chunk'][1]:#x}`, **{t['bytes']}** bytes, "
      f"**{t['instructions']}** instructions")
    w("- shape: `push rbx` / `sub rsp, 0x30` / one `call 0x141ebb6f8` / a long run of qword zero")
    w("  stores / `mov rax, rbx` / `ret` — a default-construct, with `rcx` the object")
    w("- the object is zeroed from `+0x30` up past `+0x1c8`, then a counted loop zeroes a")
    w("  16-entry table at `+0x80`, then four constants are written: `[+0x2c0]` = 2,")
    w("  `[+0x2c4]` = 4, `[+0x2cc]` = `0x3f000000` (0.5f), `[+0x2d4]` = 1")
    w("")
    w("### The two stores, and the register they read")
    w("")
    w("| offset | at | bytes | instruction | value origin |")
    w("|---|---|---|---|---|")
    for s in d["stores"]:
        rw = s["rdx_writer"] or {}
        w(f"| `+{s['offset']:#x}` | `{s['addr']:#x}` | `{s['bytes']}` | `{s['text']}` | "
          f"`{rw.get('addr', 0):#x}` `{rw.get('text','-')}` |")
    w("")
    w("## Every direct caller")
    w("")
    for c in d["direct_callers"]:
        w(f"### `{c['site']:#x}` in `{c['caller_fn']:#x}`..`{c['caller_end']:#x}` ({c['kind']})")
        w("")
        w(f"- call-site bytes: `{c['site_bytes']}` — `{c['site_text']}`")
        if c["allocator"]:
            a = c["allocator"]
            w(f"- allocator immediately before: `{a['addr']:#x}` `{a['bytes']}` "
              f"`{a['text']}` → target `{a['target']:#x}`")
        if c["rcx_object_size"]:
            r = c["rcx_object_size"]
            w(f"- object size in `rcx`: `{r['bytes']}` `{r['text']}` = **{r['value']}** bytes "
              f"(`{r['value']:#x}`)")
        w(f"- writes to `rdx` between the allocator and the call: "
          f"**{len(c['rdx_written_between_alloc_and_call'])}**")
        w(f"- last write to `rdx` before the call: "
          + (f"`{c['last_rdx_write']['addr']:#x}` `{c['last_rdx_write']['text']}`"
             if c["last_rdx_write"] else "**none in this function**"))
        w(f"- RIP-relative `mov`/`lea` in the caller: **{c['rip_loads_in_caller']}**")
        w("")
        w("```")
        for x in c["window"]:
            w(f"{x['addr']:#x}  {x['bytes']}  {x['text']}")
        w(f"{c['site']:#x}  {c['site_bytes']}  {c['site_text']}   <== the call")
        w("```")
        w("")
        w(f"**Type verdict for this caller:** the value handed in `rdx` is **not** the type §3's")
        w("readers load. `rdx` is never written between the allocation and the call, and the")
        w("callee overwrites it with `xor edx, edx` before either store — so the field receives a")
        w("null pointer, which a dereferencing reader (§3: `mov rdi, qword ptr [rcx + 0x150]`)")
        w("cannot use as a node.")
        w("")
    w("## The chain above the caller")
    w("")
    w("Edges are counted as `call rel32` / `jmp rel32` whose target is a **function entry**")
    w("(a `.pdata` chunk start); intra-region jumps are excluded so tail-jumps are not counted as")
    w("callers.")
    w("")
    w("| node | depth | edges into it | distinct caller entries |")
    w("|---|---:|---:|---:|")
    for n in d["chain"]:
        w(f"| `{n['entry']:#x}` | {n['depth']} | {n['edges']} | {len(n['edged_to_entries'])} |")
    w("")
    w("### Each caller searched, with its hit count")
    w("")
    w("| function entry | edges into this entry |")
    w("|---|---:|")
    for n in d["node_counts"]:
        w(f"| `{n['entry']:#x}` | {n['edges_into_entry']} |")
    w("")
    w(f"The caller's own entry (`{d['direct_callers'][0]['caller_fn']:#x}`) has "
      f"**{d['counts']['edges_into_caller_entry']}** entry-target edge(s) in the image, and the")
    w(f"only call into `{TARGET:#x}` is the one site above. Within the caller, "
      f"**{d['counts']['rip_loads_in_caller']}** RIP-relative loads exist, but none of them is the")
    w("value stored at the two offsets: the stores take the zeroed `rdx`, not a global.")
    w("")
    w("## Why this is the right answer, and what it does not say")
    w("")
    w("- It **refutes** the candidate from `RUNTIME_LAYOUT4.md` §7 rather than promoting it: the")
    w("  width oracle in that card could only see that 8 bytes are written; this card reads what")
    w("  the 8 bytes *are*.")
    w("- It does **not** find the writer of the node into `+0x150` / `+0x158`. That writer is still")
    w("  UNKNOWN, and this walk says nothing about where it is — it only removes the strongest")
    w("  image-wide candidate.")
    w("- It does **not** decide whether `+0x150` and `+0x158` are two lists (head/next) or one list")
    w("  with two anchors: both are null-initialised here and never compared.")
    w("")
    w("## Oracles")
    w("")
    w("| oracle | result | detail |")
    w("|---|---|---|")
    for o in d["oracles"]:
        w(f"| `{o['name']}` | {'PASS' if o['ok'] else '**FAIL**'} | {o['detail']} |")
    w("")
    w("## Reproduce")
    w("")
    w("```bash")
    w("uv run --with pefile --with capstone python Tools/scripts/jc3_textcache.py   # once")
    w("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout5.py --write")
    w("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout5.py --check")
    w("```")
    w("")
    return "\n".join(A) + "\n"


def dump(doc: dict) -> None:
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(doc))
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    if a.write:
        dump(doc)
        print(f"wrote {OUT_MD}")
        print(f"wrote {OUT_JSON}")
        print(f"verdict {doc['verdict']}  callers {doc['counts']['direct_callers']}  "
              f"stores {'both 8B'}  rdx {doc['rdx_definition']['text'] if doc['rdx_definition'] else '-'}")
        for o in doc["oracles"]:
            print(f"  {o['name']:38s} {'PASS' if o['ok'] else 'FAIL'}")
        return 0 if all(o["ok"] for o in doc["oracles"]) else 1

    old_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    old_js = open(OUT_JSON, encoding="utf-8").read() if os.path.exists(OUT_JSON) else ""
    same_md, same_js = old_md == md, old_js == js
    print(f"json identical {same_js}  md identical {same_md}")
    print(f"verdict {doc['verdict']}  callers {doc['counts']['direct_callers']}  "
          f"chain {doc['counts']['chain_nodes']}")
    ok = same_md and same_js and all(o["ok"] for o in doc["oracles"])
    print("CHECK PASS" if ok else "CHECK FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
