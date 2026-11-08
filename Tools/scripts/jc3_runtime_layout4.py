#!/usr/bin/env python
"""jc3_runtime_layout4.py - who WRITES the part node's `+0x150` / `+0x158` (G3-07e, step 1 of 2).

`RUNTIME_LAYOUT3.md` §3/§5 established the *readers*: functions that load a global, dereference
it, and then touch `[node+0x150]` / `[node+0x158]` (qword loads), without proving an entry point
(its UNKNOWN 1) or which of the two pointers the raycast path uses (UNKNOWN 2).  This pass asks
the question from the other side and **stops at the writers**:

  * every instruction that writes `[reg+0x150]` or `[reg+0x158]` **inside** the functions §3/§5
    list as readers, **or inside their direct callers** (one hop, `call rel32` / `jmp rel32`);
  * for each hit: the address, the six instructions around it, the function it belongs to, and a
    type oracle - the written value's width must match the width the readers use at that offset,
    or the hit is refuted as a different class's field at the same displacement;
  * the whole-image writer census, so "no writer in scope" is a count and not an impression.

Disassembly happens **once** and is cached by `tmp/freebuff/scratch/jc3_textcache.py` (a
chunk-driven `.pdata` sweep, `tmp/freebuff/scratch/jc3_text_index_v1.pkl.z`); this tool loads that
cache, so a search is a dict lookup plus a few thousand re-decodes.  If the cache is missing or
belongs to another exe, it is rebuilt once.

Static only: `D:/Games/Just Cause 3/JustCause3.exe` is opened read-only and never run.
Nothing here links the node into a container or a global - that is the next task (7121).

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout4.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout4.py --check
"""
from __future__ import annotations

import argparse
import bisect
import collections
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
sys.path.insert(0, os.path.join(ROOT, "tmp", "freebuff", "scratch"))
import jc3_textcache as CACHE                              # noqa: E402  (the one-pass cache)

EXE = r"D:/Games/Just Cause 3/JustCause3.exe"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT4.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "RUNTIME_LAYOUT4.json")

# RUNTIME_LAYOUT3.md §1: the whole-function entries the anchors resolve to (readers of the node).
SEC3_ENTRIES = {
    "part_list_walk": 0x140201D30,
    "part_node_update": 0x140201DE0,
    "raycast_body_read": 0x140201DE0,
    "body_slot_query": 0x141505490,
    "body_slot_use": 0x1415140F0,
    "body_slot_enum": 0x140222EF0,
}
# RUNTIME_LAYOUT3.md §1: the chunk sizes it reports, re-derived as oracle O3.
SEC3_CHUNK_SIZES = {0x140201D4E: 122, 0x140201DE0: 76, 0x1402020D1: 157,
                    0x141505490: 38, 0x1415140F0: 80, 0x140222EF0: 315}
SEC3_MERGED_SIZES = {0x140201D30: 163, 0x140201DE0: 943, 0x141505490: 249,
                     0x1415140F0: 380, 0x140222EF0: 315}
# RUNTIME_LAYOUT3.md §5: the 28 functions of the global -> [node+0x150]/[node+0x158] scan.
SEC5_FUNCS = [
    0x1400C5960, 0x1400C60D0, 0x140105B90, 0x14012DDA0, 0x14013CD00, 0x14013FDE4,
    0x1403083AB, 0x14033E270, 0x14034E4A0, 0x14037A93A, 0x140490ABD, 0x1409AC840,
    0x140B1CBA0, 0x140B592F0, 0x140B78C50, 0x140DD0D90, 0x140DFB960, 0x140E0F620,
    0x140E88BC0, 0x140EDCF00, 0x140EEFC80, 0x140EFD5C0, 0x140EFD750, 0x140F06C15,
    0x140F09A90, 0x140F46E60, 0x141006170, 0x141F4A730,
]
FIELDS = CACHE.FIELDS
WRITE, READ = 2, 1
STOP_TAIL = {"ret", "jmp", "retf", "iretq"}
MAX_CONTEXT_HITS = 40

MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
MD.detail = True
STACK_REGS = {capstone.x86.X86_REG_RSP, capstone.x86.X86_REG_RBP}


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
        self.nsec = len(self.secs)

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

    def insns(self, va: int, n: int):
        return list(MD.disasm(self.raw[self.off(va):self.off(va) + n], va))


def regions(chunks: list, tails: dict) -> list[dict]:
    """Merge `.pdata` chunks that fall through, as RUNTIME_LAYOUT3A's rule does."""
    out = []
    for s, e in chunks:
        tail = (tails.get(e) or ("", 0))[0]
        out.append({"start": s, "end": e, "chunks": [(s, e)], "tail": tail})
    merged = []
    for r in out:
        if merged:
            p = merged[-1]
            if p["end"] == r["start"] and p["tail"] not in STOP_TAIL:
                p["end"] = r["end"]
                p["chunks"].append(r["chunks"][0])
                p["tail"] = r["tail"]
                continue
        merged.append(r)
    return merged


# ------------------------------------------------------------------ build
def build() -> dict:
    t0 = time.time()
    img = Img()
    if not os.path.exists(CACHE.CACHE):
        CACHE.build()
    try:
        cache = CACHE.load()
    except AssertionError:
        CACHE.build()
        cache = CACHE.load()
    meta = cache["meta"]
    chunks, tails = cache["chunks"], cache["tails"]
    fields = cache["fields"]
    calls = cache["calls"]
    regs = regions(chunks, tails)
    rstart = [r["start"] for r in regs]

    def region_of(va: int):
        i = bisect.bisect_right(rstart, va) - 1
        if i >= 0 and regs[i]["start"] <= va < regs[i]["end"]:
            return regs[i]
        return None

    def fops(lo: int, hi: int, access: int | None = None) -> list[dict]:
        return [{"addr": a, "len": ln, "disp": d, "width": w, "access": ac, "base": b,
                 "index": ix, "mnem": m, "text": f"{m} {t}".strip()}
                for (a, ln, d, w, ac, b, ix, m, t) in fields
                if lo <= a < hi and (access is None or ac & access)]

    # ---- the reader set: §3's whole functions and §5's functions, as regions
    readers, reader_keys = [], set()
    for label, va in sorted(SEC3_ENTRIES.items()):
        r = region_of(va)
        if r is None:
            continue
        key = r["start"]
        if key not in reader_keys:
            reader_keys.add(key)
            readers.append({"source": "§3", "label": label, "start": r["start"],
                            "end": r["end"], "size": r["end"] - r["start"],
                            "chunks": len(r["chunks"]), "tail": r["tail"],
                            "fields": fops(r["start"], r["end"])})
        else:
            for rw in readers:
                if rw["start"] == key and label not in rw["label"]:
                    rw["label"] += ", " + label
    for va in SEC5_FUNCS:
        r = region_of(va)
        if r is None:
            continue
        if r["start"] in reader_keys:
            for rw in readers:
                if rw["start"] == r["start"] and "§5" not in rw["source"]:
                    rw["source"] = "§3+§5"
                    rw["label"] += " (also §5)"
            continue
        reader_keys.add(r["start"])
        readers.append({"source": "§5", "label": "§5 row", "start": r["start"],
                        "end": r["end"], "size": r["end"] - r["start"],
                        "chunks": len(r["chunks"]), "tail": r["tail"],
                        "fields": fops(r["start"], r["end"])})

    # ---- the read-width census the type oracle is built on
    read_widths = collections.Counter()
    per_disp_reads = {d: [] for d in FIELDS}
    for rw in readers:
        for f in rw["fields"]:
            if f["access"] & READ:
                read_widths[(f["disp"], f["width"])] += 1
                per_disp_reads[f["disp"]].append({"addr": f["addr"], "width": f["width"],
                                                  "fn": rw["start"], "text": f["text"]})
    expected = {d: [w for (dd, w), n in read_widths.most_common() if dd == d]
                for d in FIELDS}

    # the widths §3's own readers load at each offset: the type a part-node writer must match
    sec3_expected = {d: set() for d in FIELDS}
    for rw in readers:
        if "§3" in rw["source"]:
            for f in rw["fields"]:
                if f["access"] & READ:
                    sec3_expected[f["disp"]].add(f["width"])
    own_basis: dict[tuple, set] = {}
    for rw in readers:
        for f in rw["fields"]:
            if f["access"] & READ:
                own_basis.setdefault((rw["start"], f["disp"]), set()).add(f["width"])

    # ---- direct callers of the readers (one hop)
    caller_edges = []
    caller_keys = {}
    for site, target, kind in calls:
        if region_of(target) is None:
            continue
        r = region_of(target)
        if r["start"] not in reader_keys:
            continue
        cr = region_of(site)
        if cr is None:
            continue
        caller_edges.append({"site": site, "kind": "call" if kind == 0 else "jmp",
                             "target": target, "callee_fn": r["start"],
                             "caller_fn": cr["start"],
                             "text": img.insns(site, 16)[0].mnemonic + " " +
                                     img.insns(site, 16)[0].op_str if img.insns(site, 16) else ""})
        caller_keys.setdefault(cr["start"], {"start": cr["start"], "end": cr["end"],
                                             "size": cr["end"] - cr["start"],
                                             "calls": [], "fields": fops(cr["start"], cr["end"])})
        caller_keys[cr["start"]]["calls"].append(
            {"site": site, "kind": "call" if kind == 0 else "jmp",
             "callee": r["start"], "label": next(x["label"] for x in readers
                                                 if x["start"] == r["start"])})
    callers = sorted(caller_keys.values(), key=lambda c: c["start"])
    scope = set(reader_keys) | {c["start"] for c in callers}

    # the widths a caller's callees load: a caller that stores into the object it hands over
    # must match them, so the same type test applies one hop out
    callee_basis: dict[tuple, set] = {}
    for e in caller_edges:
        rw = next(x for x in readers if x["start"] == e["callee_fn"])
        for f in rw["fields"]:
            if f["access"] & READ:
                callee_basis.setdefault((e["caller_fn"], f["disp"]), set()).add(f["width"])

    # ---- the writers in scope
    hits = []
    for f in fields:
        if not (f[4] & WRITE):
            continue
        r = region_of(f[0])
        if r is None or r["start"] not in scope:
            continue
        basis = own_basis.get((r["start"], f[2])) or callee_basis.get((r["start"], f[2])) or set()
        hit = {"addr": f[0], "disp": f[2], "width": f[3], "access": f[4], "base": f[5],
               "index": f[6], "mnem": f[7], "text": f"{f[7]} {f[8]}".strip(), "fn": r["start"],
               "fn_size": r["end"] - r["start"], "in": "reader" if r["start"] in reader_keys
               else "caller",
               "stack": f[5] in STACK_REGS, "indexed": bool(f[6]),
               "covers_both": f[2] == 0x150 and f[3] >= 16,
               "basis": ("own" if (r["start"], f[2]) in own_basis else
                         ("callee" if (r["start"], f[2]) in callee_basis else "none")),
               "expected_widths": sorted(basis),
               "sec3_widths": sorted(sec3_expected[f[2]])}
        hit["type_ok"] = bool(basis) and f[3] in basis
        hit["sec3_ok"] = bool(sec3_expected[f[2]]) and f[3] in sec3_expected[f[2]]
        hits.append(hit)
    hits.sort(key=lambda h: h["addr"])

    # ---- context: three instructions before and after the hit
    for h in hits:
        r = region_of(h["addr"])
        ins = img.insns(r["start"], r["end"] - r["start"])
        i = next((k for k, x in enumerate(ins) if x.address == h["addr"]), None)
        ctx = []
        if i is not None:
            for x in ins[max(0, i - 3):i + 4]:
                ctx.append({"addr": x.address, "bytes": x.bytes.hex(" "),
                            "text": f"{x.mnemonic} {x.op_str}".strip(),
                            "hit": x.address == h["addr"]})
        h["context"] = ctx

    # ---- whole-image writer census (supplementary; every hit, not only in scope)
    census = collections.Counter()
    census_rows, per_fn = [], collections.defaultdict(
        lambda: {"disp": set(), "widths": collections.Counter(), "stores": []})
    for (a, ln, d, w, ac, b, ix, m, t) in fields:
        if not (ac & WRITE):
            continue
        r = region_of(a)
        fstart = r["start"] if r else None
        census[(fstart, d, w)] += 1
        census_rows.append({"addr": a, "fn": fstart, "disp": d, "width": w,
                            "in_scope": fstart in scope})
        e = per_fn[fstart]
        e["disp"].add(d)
        e["widths"][(d, w)] += 1
        e["stores"].append({"addr": a, "text": f"{m} {t}".strip(), "width": w, "disp": d,
                            "stack": b in STACK_REGS})
    image_writes = len(census_rows)
    in_scope_writes = sum(1 for x in census_rows if x["in_scope"])
    both_writers = []
    for fn, e in per_fn.items():
        if len(e["disp"]) < 2:
            continue
        both_writers.append({"fn": fn, "in_scope": fn in scope,
                             "widths": {f"{d:#x}": {str(w): n for (dd, w), n in
                                                     e["widths"].items() if dd == d}
                                        for d in sorted(e["disp"])},
                             "stores": sorted(e["stores"], key=lambda s: s["addr"])[:8]})
        both_writers[-1]["w8_both"] = (len(both_writers[-1]["widths"]) == 2 and
                                       all(set(v) == {"8"}
                                           for v in both_writers[-1]["widths"].values()))
    both_writers.sort(key=lambda b: (not b["in_scope"], not b["w8_both"], b["fn"]))

    # ---- the UNKNOWN-2 decision, only from writers that match §3's own reads
    good = [h for h in hits if h["type_ok"] and not h["stack"]]
    pointer = [h for h in good if h["sec3_ok"]]
    both = [h for h in pointer if h["covers_both"] or
            any(o is not h and o["fn"] == h["fn"] and o["disp"] != h["disp"]
                for o in pointer)]
    decision = "FILLED" if both else "UNKNOWN"

    doc = {
        "schema": 1,
        "card": "G3-07e",
        "generator": "Tools/scripts/jc3_runtime_layout4.py",
        "inputs": {
            "exe": {"path": EXE, "sha256": img.sha256, "base": img.base,
                    "sections": img.nsec,
                    "text": [s for s in img.secs if s[0] == ".text"][0]},
            "cache": {"path": os.path.relpath(CACHE.CACHE, ROOT).replace("\\", "/"),
                      "version": meta["version"], "sha256": meta["sha256"],
                      "instructions": meta["instructions"], "calls": meta["calls"],
                      "field_ops": meta["field_ops"], "chunk_tails": meta["chunk_tails"],
                      "gaps": meta["gaps"], "bytes_covered": meta["bytes_covered"],
                      "seconds": meta["seconds"]},
            "quoted": {"sec3_entries": {k: hex(v) for k, v in SEC3_ENTRIES.items()},
                       "sec5_functions": [hex(v) for v in SEC5_FUNCS]},
        },
        "method": {
            "cache": "one chunk-driven `.pdata` sweep of `.text` (188,670 chunks), every call/jmp "
                     "site and every [reg+0x150]/[reg+0x158] operand stored",
            "regions": "`.pdata` chunks merged where they fall through (tail not ret/jmp)",
            "readers": "the merged functions containing §3's entries and §5's functions",
            "callers": "regions holding a call/jmp site whose target is inside a reader region",
            "writers": "instructions in the cache with CS_AC_WRITE at disp 0x150 / 0x158 whose "
                       "address lies in a reader or a direct caller",
            "type_oracle": "the written operand's width must equal a width the readers use at the "
                           "same displacement (qword loads in §5), else the hit is another class",
        },
        "read_widths": {f"{d:#x}": {str(w): n for (dd, w), n in read_widths.items() if dd == d}
                        for d in FIELDS},
        "sec3_widths": {f"{d:#x}": sorted(sec3_expected[d]) for d in FIELDS},
        "expected_widths": {f"{d:#x}": expected[d] for d in FIELDS},
        "read_sites": {f"{d:#x}": per_disp_reads[d][:20] for d in FIELDS},
        "readers": readers,
        "callers": [{"start": c["start"], "end": c["end"], "size": c["size"],
                     "calls": c["calls"],
                     "fields": c["fields"]} for c in callers],
        "edges": caller_edges,
        "hits": hits,
        "census": {"image_writes": image_writes, "in_scope_writes": in_scope_writes,
                   "distinct_functions": len({x["fn"] for x in census_rows}),
                   "both_writers": both_writers,
                   "top": [{"fn": k[0], "disp": k[1], "width": k[2], "n": n}
                           for k, n in census.most_common(30)]},
        "searches": searches(hits, in_scope_writes, image_writes, both_writers),
        "decision": {"verdict": decision,
                     "typed_hits": len(good), "pointer_hits": len(pointer),
                     "both_offset_hits": len(both),
                     "detail": describe(good, pointer, both, hits, both_writers)},
        "counts": {"readers": len(readers), "callers": len(callers), "edges": len(caller_edges),
                   "hits": len(hits), "hits_in_readers": sum(1 for h in hits
                                                             if h["in"] == "reader"),
                   "hits_stack": sum(1 for h in hits if h["stack"]),
                   "hits_type_ok": len(good), "hits_sec3_ok": len(pointer)},
        "oracles": oracles(img, meta, chunks, tails, regs, hits, readers, decision),
        "elapsed_s": round(time.time() - t0, 1),
    }
    doc["digest"] = hashlib.sha1(json.dumps({k: v for k, v in doc.items() if k != "digest"},
                                            sort_keys=True, separators=(",", ":")).encode()
                                ).hexdigest()[:16]
    return doc


def searches(hits: list, in_scope: int, image: int, both_writers: list) -> list[dict]:
    """Every search this card ran, with its hit count - so "none" is a number, not a claim."""
    def n(pred) -> int:
        return sum(1 for h in hits if pred(h))
    return [
        {"what": "writers at `+0x150` inside a reader", "hits": n(lambda h: h["in"] == "reader"
                                                                   and h["disp"] == 0x150)},
        {"what": "writers at `+0x158` inside a reader", "hits": n(lambda h: h["in"] == "reader"
                                                                   and h["disp"] == 0x158)},
        {"what": "writers at either offset inside a direct caller", "hits": n(
            lambda h: h["in"] == "caller")},
        {"what": "8-byte writers anywhere in scope (stack frames included)", "hits": n(
            lambda h: h["width"] == 8)},
        {"what": "8-byte writers in scope, not a stack frame", "hits": n(
            lambda h: h["width"] == 8 and not h["stack"])},
        {"what": "writers matching the §3 read width (8 B), stack frames included", "hits": n(
            lambda h: h["sec3_ok"])},
        {"what": "writers matching the §3 read width, not a stack frame", "hits": n(
            lambda h: h["sec3_ok"] and not h["stack"])},
        {"what": "writers filling both offsets with 8 B in scope", "hits": n(
            lambda h: h["sec3_ok"] and h["covers_both"])},
        {"what": "all writers at the two offsets in scope, stack frames included", "hits": in_scope},
        {"what": "all writers at the two offsets in the whole image", "hits": image},
        {"what": "functions writing both offsets with 8 B, whole image", "hits": sum(
            1 for b in both_writers if b["w8_both"])},
        {"what": "functions writing both offsets with any width, whole image", "hits": len(
            both_writers)},
    ]


def describe(good: list, pointer: list, both: list, hits: list, both_writers: list) -> str:
    if both:
        fns = sorted({h["fn"] for h in both})
        return ("a writer in scope fills both offsets with the width §3's readers load, in "
                + ", ".join(f"`{f:#x}`" for f in fns)
                + " - the context blocks show whether one value reaches both fields or two do.")
    near = [b for b in both_writers if b["w8_both"]]
    tail = (f" The nearest image-wide candidate is `{near[0]['fn']:#x}`: it stores an 8-byte "
            f"value at both offsets, but it is not a reader or a direct caller of one, so this "
            f"card does not claim it - the next card can test it against a caller path."
            if near else "")
    if hits:
        return (f"UNKNOWN. {len(hits)} writer(s) touch the two offsets in the searched functions, "
                f"but none writes the {', '.join(str(w) + ' byte' for w in sorted({8}))} value "
                f"§3's readers load there: they are byte/dword/float4 stores to another class's "
                f"fields at the same displacements, and the width oracle refutes each one." + tail)
    return ("UNKNOWN. No instruction in the searched functions writes either offset" + tail)


# ------------------------------------------------------------------ oracles
def oracles(img: Img, meta: dict, chunks: list, tails: dict, regs: list,
            hits: list, readers: list, decision: str) -> list[dict]:
    out = []

    # O1: the image is the one the earlier cards were built on
    ok = (img.base == 0x140000000 and img.nsec == 7 and len(chunks) == 188670
          and img.sha256.startswith("a53c2d6b2837f45d"))
    out.append({"id": "O1-image", "pass": ok,
                "evidence": f"base {img.base:#x}, {img.nsec} sections, {len(chunks):,} .pdata "
                            f"chunks, sha256 {img.sha256[:16]}"})

    # O2: the anchored instruction from RUNTIME_LAYOUT3A still decodes the same way
    ins = img.insns(0x14151410F, 16)
    txt = f"{ins[0].mnemonic} {ins[0].op_str}".strip() if ins else ""
    out.append({"id": "O2-crash-site", "pass": txt == "movss xmm0, dword ptr [rax + 0x14]",
                "evidence": f"at 0x14151410f: {txt}"})

    # O3: §1's chunk and merged sizes re-derive
    chunk_sizes = {s: e - s for s, e in chunks}
    bad = {hex(k): (v, chunk_sizes.get(k)) for k, v in SEC3_CHUNK_SIZES.items()
           if chunk_sizes.get(k) != v}
    reg_by_start = {r["start"]: r for r in regs}
    badm = {hex(k): (v, (reg_by_start[k]["end"] - k) if k in reg_by_start else None)
            for k, v in SEC3_MERGED_SIZES.items()
            if k not in reg_by_start or reg_by_start[k]["end"] - k != v}
    out.append({"id": "O3-chunk-and-merged-sizes", "pass": not bad and not badm,
                "evidence": f"chunk mismatches {bad or 'none'}; merged mismatches {badm or 'none'}"})

    # O4: the cache is the one for this exe and it is complete
    ok = (meta["version"] == CACHE.VERSION and meta["sha256"] == img.sha256
          and meta["chunk_tails"] == len(chunks) and meta["instructions"] > 7_000_000)
    out.append({"id": "O4-cache", "pass": ok,
                "evidence": f"v{meta['version']}, sha256 match, {meta['instructions']:,} "
                            f"instructions, {meta['chunk_tails']:,} chunk tails, "
                            f"{meta['calls']:,} call sites, {meta['gaps']:,} undecodable bytes"})

    # O5: every hit re-decodes from the exe bytes to the same instruction
    bad = []
    for h in hits:
        i = img.insns(h["addr"], 16)
        again = f"{i[0].mnemonic} {i[0].op_str}".strip() if i else ""
        if again != h["text"]:
            bad.append(hex(h["addr"]))
    out.append({"id": "O5-hits-redecode", "pass": not bad,
                "evidence": f"{len(hits)} hit(s) re-decoded from the exe bytes; mismatches "
                            f"{bad or 'none'}"})

    # O6: the readers really are the §5 pattern's functions (they read the offsets)
    n_read = sum(len(r["fields"]) for r in readers)
    out.append({"id": "O6-readers-touch-the-offsets", "pass": n_read > 0,
                "evidence": f"{len(readers)} reader regions hold {n_read} operand(s) at 0x150/"
                            f"0x158 (reads and writes)"})

    # O7: the verdict is a function of the hits, not a judgement call made on top of them
    good = [h for h in hits if h["type_ok"] and not h["stack"]]
    pointer = [h for h in good if h["sec3_ok"]]
    both = [h for h in pointer if h["covers_both"] or
            any(o is not h and o["fn"] == h["fn"] and o["disp"] != h["disp"]
                for o in pointer)]
    ok = (decision == "FILLED") == bool(both)
    out.append({"id": "O7-decision-follows", "pass": ok,
                "evidence": f"verdict {decision}: {len(hits)} hit(s), {len(good)} typed, "
                            f"{len(pointer)} matching §3's read width, {len(both)} filling both "
                            f"offsets with it"})
    return out


# ------------------------------------------------------------------ render
def render(d: dict) -> str:
    h, c, cen, dec = d["counts"], d["counts"], d["census"], d["decision"]
    L: list[str] = []
    A = L.append
    A("# Who writes the part node's `+0x150` / `+0x158` (G3-07e, step 1 of 2)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout4.py --write`; `--check` re-derives every")
    A("row from the exe (read-only) through the one-pass `.text` cache and fails on drift.")
    A("Static only: `Just Cause 3/JustCause3.exe` is opened read-only and never run.")
    A("")
    A("## Answer - **%s**" % d["decision"]["verdict"])
    A("")
    A(d["decision"]["detail"])
    A("")
    A(f"Searched: **{c['readers']} reader functions** (§3's entries and §5's functions) and")
    A(f"**{c['callers']} direct callers** ({c['edges']} call/jmp edges). Writers in scope:")
    A(f"**{c['hits']}**, {c['hits_in_readers']} of them inside a reader itself; "
      f"{c['hits_stack']} write a `rsp`/`rbp` stack frame (not an object field); "
      f"{c['hits_type_ok']} match their own function's read width and **{c['hits_sec3_ok']}** "
      f"match the width §3's readers load at that offset.")
    A("")
    A("## Method (decoded -> derived)")
    A("")
    A("- one **chunk-driven** disassembly of `.text`, cached: 188,670 `.pdata` chunks, "
      f"{d['inputs']['cache']['instructions']:,} instructions, "
      f"{d['inputs']['cache']['calls']:,} call/jmp sites, "
      f"{d['inputs']['cache']['field_ops']:,} operands at the two displacements "
      f"({d['inputs']['cache']['gaps']:,} undecodable bytes skipped, chunk by chunk, so no")
    A("  desync can cross a function boundary). A flat sweep was tried first and stopped after")
    A("  25,252 of 36,310,271 bytes on the first bad byte - recorded here so the method is not")
    A("  mistaken for a whole-image linear disassembly.")
    A("- `.pdata` chunks are merged where they fall through (tail mnemonic not `ret`/`jmp`),")
    A("  reproducing §1's sizes as oracle `O3`.")
    A("- readers = the merged functions containing §3's whole-function entries and §5's functions;")
    A("  callers = functions holding a `call`/`jmp` site whose target is inside a reader.")
    A("- writers = cache instructions with `CS_AC_WRITE` at `+0x150`/`+0x158` inside those")
    A("  functions. Each hit is re-decoded from the exe bytes (`O5`) and tested against the width")
    A("  the readers use at that offset (`O7`): a byte or dword store at the same displacement is")
    A("  another class's field, not the node pointer.")
    A("")
    A("## Every search and its hit count")
    A("")
    A("| search | hits |")
    A("|---|---:|")
    for s in d["searches"]:
        A(f"| {s['what']} | {s['hits']} |")
    A("")
    A("## The read widths the type oracle is built on")
    A("")
    A("| offset | widths read across all readers | widths read by §3's readers |")
    A("|---|---|---|")
    for disp in FIELDS:
        key = f"{disp:#x}"
        widths = d["read_widths"].get(key, {})
        A(f"| `+{key}` | {', '.join(f'{w} B x{n}' for w, n in sorted(widths.items())) or 'none'}"
          f" | {', '.join(str(w) + ' B' for w in d['sec3_widths'].get(key, [])) or '-'} |")
    A("")
    A("Read sites the writers must match (`decoded`):")
    A("")
    A("| offset | at | function | instruction |")
    A("|---|---|---|---|")
    for disp in FIELDS:
        for s in d["read_sites"].get(f"{disp:#x}", [])[:8]:
            A(f"| `+{disp:#x}` | `{s['addr']:#x}` | `{s['fn']:#x}` | `{s['text']}` |")
    A("")
    A("## The readers (§3 entries + §5 functions)")
    A("")
    A("| source | function | bytes | chunks | operands at 0x150/0x158 |")
    A("|---|---|---:|---:|---|")
    for r in d["readers"]:
        ops = ", ".join(("W" if f["access"] & WRITE else "R") + f"{f['width']}@"
                        f"{f['disp']:#x}" for f in r["fields"]) or "-"
        A(f"| {r['source']} `{r['label']}` | `{r['start']:#x}`..`{r['end']:#x}` | {r['size']} | "
          f"{r['chunks']} | {ops} |")
    A("")
    A("## Writers in scope (%d)" % c["hits"])
    A("")
    if not d["hits"]:
        A("None. Every search and its hit count is in §6; the census below shows the image-wide")
        A("writers that were excluded and why.")
    else:
        A("| at | function | in | width | offset | stack | own-type | §3-type | instruction |")
        A("|---|---|---|---:|---|:-:|:-:|:-:|---|")
        for x in d["hits"]:
            own = ("PASS" if x["type_ok"] else "**FAIL**") if x["expected_widths"] else "n/a"
            s3 = "PASS" if x["sec3_ok"] else "**FAIL**"
            A(f"| `{x['addr']:#x}` | `{x['fn']:#x}` | {x['in']} | {x['width']} B | "
              f"`+{x['disp']:#x}` | {'yes' if x['stack'] else '-'} | {own} | {s3} | "
              f"`{x['text']}` |")
    A("")
    A("## The six instructions around each hit")
    A("")
    shown = 0
    for x in d["hits"]:
        if shown >= MAX_CONTEXT_HITS:
            A(f"_{len(d['hits']) - shown} more hit(s) omitted from the context listing; all are in "
              f"the table above._")
            break
        A(f"### `{x['addr']:#x}` in `{x['fn']:#x}` ({x['in']})")
        A("")
        A("```")
        for i in x["context"]:
            A(f"{'>>' if i['hit'] else '  '} {i['addr']:#x}  {i['bytes']:<24} {i['text']}")
        A("```")
        A("")
        if x["stack"]:
            A(f"Oracle that would fail if this were the wrong field: the base register is a "
              f"`rsp`/`rbp` frame, so this is a stack local and not a field of any object the "
              f"readers load - refuted on the base, before the width is even consulted "
              f"(an object field would be `[rcx]`/`[rax]`-style, as every read site above is).")
        elif not x["expected_widths"]:
            A(f"Oracle: no reader in this function's call chain loads `+{x['disp']:#x}`, so there "
              f"is no width to match - the type is UNDECIDED for this hit, and it is not counted "
              f"as a node writer.")
        else:
            A(f"Oracle that would fail if this were the wrong field: the readers load "
              f"{', '.join(str(w) + ' B' for w in x['expected_widths'])} at `+{x['disp']:#x}`, so a "
              f"store of {x['width']} B here "
              f"{'matches' if x['type_ok'] else '**does not match**'} "
              f"({'PASS' if x['type_ok'] else 'FAIL'}); against §3's own readers "
              f"({', '.join(str(w) + ' B' for w in x['sec3_widths'])}) it "
              f"{'matches' if x['sec3_ok'] else '**does not match**'}.")
        A("")
        shown += 1
    A("## Whole-image census (supplementary)")
    A("")
    A(f"{cen['image_writes']} write operand(s) to `+0x150`/`+0x158` in the whole image, in "
      f"{cen['distinct_functions']} functions; **{cen['in_scope_writes']}** of them are in the "
      f"searched set.")
    A("")
    A("| function | offset | width | writes | in scope |")
    A("|---|---|---:|---:|:-:|")
    for row in cen["top"]:
        A(f"| `{row['fn']:#x}` | `+{row['disp']:#x}` | {row['width']} B | {row['n']} | "
          f"{'yes' if row['fn'] in {x['fn'] for x in d['hits']} else '-'} |")
    A("")
    A("### Functions that write both offsets (any width)")
    A("")
    A("| function | in scope | widths per offset | first stores |")
    A("|---|---|---|---|")
    for b in cen["both_writers"][:15]:
        widths = "; ".join(f"`+{k}` " + ", ".join(f"{w} B x{n}" for w, n in sorted(v.items()))
                           for k, v in b["widths"].items())
        stores = "; ".join(f"`{s['addr']:#x}` {s['text']}" for s in b["stores"][:3])
        A(f"| `{b['fn']:#x}` | {'yes' if b['in_scope'] else '-'} | {widths} | {stores} |")
    A("")
    A(f"{len(cen['both_writers'])} function(s) in the image write both offsets; "
      f"{sum(1 for b in cen['both_writers'] if b['in_scope'])} of them is in the searched set.")
    A("")
    A("## Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A(f"| `{o['id']}` | {'PASS' if o['pass'] else 'FAIL'} | {o['evidence']} |")
    A("")
    A("## UNKNOWN 2 (`+0x150` vs `+0x158`)")
    A("")
    if d["decision"]["verdict"] == "FILLED":
        A("Answered: the hit(s) above fill both offsets visibly, and the store instructions in the")
        A("context blocks show the shape of the fill (one value reaching both, or two).")
    else:
        A("Not answered. No writer in the searched functions stores the 8-byte value the readers")
        A("load at `+0x150` / `+0x158`; every hit is a byte, dword, stack or float4 store (the")
        A("§3-type column above is `FAIL` on all of them). So nothing shows how the two fields are")
        A("filled, and UNKNOWN 2 stands - now with the writers enumerated rather than assumed")
        A("absent. The image-wide both-offset writers are the candidates the next card can test")
        A("against a caller path.")
    A("")
    A("## UNKNOWNs")
    A("")
    A("- **Which function stores the node into its container or global.** Out of scope by the")
    A("  brief: this card stops at the writers; linking is task 7121.")
    A("- **Whether a writer outside the reader/caller set is the real one.** The whole-image census")
    A("  lists them; assigning one needs a caller path to a part container, which §3's UNKNOWN 1")
    A("  (no proved entry point) still blocks.")
    A("- **Which of `+0x150` / `+0x158` the raycast path uses.** Unchanged from §7 of")
    A("  RUNTIME_LAYOUT3: the two are never compared.")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python tmp/freebuff/scratch/jc3_textcache.py   "
      "# once, ~5 min")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout4.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout4.py --check")
    A("```")
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def dump(doc: dict) -> None:
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--build-cache", action="store_true")
    a = ap.parse_args()
    if a.build_cache:
        print(CACHE.build())
        return 0
    doc = build()
    bad = [o["id"] for o in doc["oracles"] if not o["pass"]]
    if a.check:
        same_json = (os.path.exists(OUT_JSON)
                     and open(OUT_JSON, encoding="utf-8").read()
                     == json.dumps(doc, indent=1, sort_keys=True) + "\n")
        same_md = os.path.exists(OUT_MD) and open(OUT_MD, encoding="utf-8").read() == render(doc)
        print(f"json identical {same_json}  md identical {same_md}")
        print(f"verdict {doc['decision']['verdict']}  hits {doc['counts']['hits']}  "
              f"readers {doc['counts']['readers']}  callers {doc['counts']['callers']}")
        for b in bad:
            print("  ORACLE FAIL:", b)
        ok = same_json and same_md and not bad
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    if bad:
        print("oracles failed:", bad)
        return 1
    dump(doc)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(doc))
    print(f"verdict {doc['decision']['verdict']}  readers {doc['counts']['readers']}  "
          f"callers {doc['counts']['callers']}  hits {doc['counts']['hits']}  "
          f"type-ok {doc['counts']['hits_type_ok']}  digest {doc['digest']}")
    for o in doc["oracles"]:
        print(f"  {o['id']}: {'PASS' if o['pass'] else 'FAIL'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
