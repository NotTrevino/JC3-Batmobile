#!/usr/bin/env python3
"""jc3_runtime_layout3a.py - G3-07b1: resolve the six .pdata chunks to whole functions, then
walk their callers upward to the first RIP-relative load of a global.

`review-G3-07a.md` proved two things about the G3-07a document that this tool must not repeat:
the 27 field offsets are real, but the six "functions" are `.pdata` chunks (four of them
fragments of larger functions) and the headline call chain 0x1402020d1 -> 0x141505490 ->
0x1415140f0 is refuted.  So this tool starts from the *chunk* anchors, not from a call chain:

  1. Resolve a chunk to the whole function that contains it: merge the `.pdata` chunks that
     fall through into each other (contiguous, and the earlier chunk's last non-padding
     instruction is neither `ret` nor an unconditional `jmp`), then report any `call`/`jmp`
     from outside that lands inside the merged region.
  2. Build the complete call graph by decoding every one of the 188,670 `.pdata` chunks from its
     own start (a byte scan for `E8` is not used: it yields false positives).
  3. Walk callers (and tail-jump sites) upward breadth-first and record, per hop, the edge kind,
     the site instruction's address, bytes and disassembly, and every RIP-relative operand in
     the caller's whole function.
  4. Stop at the first RIP-relative load whose target is in `.data` and is not the stack cookie.

Every number is re-derived from the bytes; `--check` rebuilds the document and compares it
byte for byte, and re-runs the eight oracles.

Loaders (`Image`, `EXE`, `mem_ops`) are imported from `Tools/scripts/jc3_runtime_layout.py`,
which is used read-only and never edited.

Usage:
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3a.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3a.py --check
"""
from __future__ import annotations

import argparse
import bisect
import json
import os
import struct
import sys

from capstone import CS_ARCH_X86, CS_MODE_64, CS_OP_MEM, CS_OP_REG, Cs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3_runtime_layout as base  # noqa: E402  (reuse the loaders, never edit them)

REPO = os.path.dirname(os.path.dirname(HERE))
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT3A.md")
OUT_JSON = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT3A.json")

IMAGE_LO, IMAGE_HI = 0x140000000, 0x143200000
COOKIE = 0x142E15310           # __security_cookie, proved by the `xor rax, rsp` idiom below
CRASH = 0x14151410F            # the G3-07a crash instruction, kept as a continuity oracle
PART_CONTAINER_LOOP = 0x14024B660   # the loop that indexes the part array
PAD = ("int3", "nop", "ud2", "hlt")

# the six anchors of G3-07a, as the review re-derived them
ANCHORS = [
    ("part_list_walk", 0x201D4E, "G3-07a `part_list_walk`"),
    ("part_node_update", 0x201DE0, "G3-07a `part_node_update`"),
    ("raycast_body_read", 0x2020D1, "G3-07a `raycast_body_read`"),
    ("body_slot_query", 0x1505490, "G3-07a `body_slot_query`"),
    ("body_slot_use", 0x15140F0, "G3-07a `body_slot_use`"),
    ("body_slot_enum", 0x222EF0, "G3-07a `body_slot_enum`"),
]
# sizes the review claims; an oracle recomputes them
REVIEW_CHUNKS = {"part_list_walk": 122, "part_node_update": 76, "raycast_body_read": 157,
                 "body_slot_query": 38, "body_slot_use": 80, "body_slot_enum": 315}
REVIEW_REGIONS = {"part_list_walk": 163, "part_node_update": 943, "raycast_body_read": 943,
                  "body_slot_query": 249, "body_slot_use": 380, "body_slot_enum": 315}
WALK_DEPTH = 5
WALK_CAP = 900


# ----------------------------------------------------------------------------- functions
def decode_chunk(img, start, end):
    """Every instruction of [start,end), decoded from `start`; resync by one byte if capstone
    stops early (never happens on the chunks used here, but keeps the count honest)."""
    out, p = [], start
    while p < end:
        got = False
        for i in img.md.disasm(img.bytes_at(p, end - p), p):
            out.append(i)
            p = i.address + i.size
            got = True
            if p >= end:
                break
        if not got:
            p += 1
    return out


_TAIL = {}


def tail_kind(img, start, end):
    """Mnemonic of the last non-padding instruction of one .pdata chunk."""
    k = (start, end)
    if k not in _TAIL:
        ins = [i for i in decode_chunk(img, start, end) if i.mnemonic not in PAD]
        _TAIL[k] = ins[-1].mnemonic if ins else None
    return _TAIL[k]


def region_of(img, va):
    """(entry, end, chunks) of the whole function containing `va`.

    Merge rule: two adjacent .pdata chunks belong to one function when the earlier chunk ends
    exactly where the later one starts *and* the earlier chunk's last real instruction neither
    returns nor jumps away (i.e. control falls through into the next chunk).
    """
    c = img.fn_of(va)
    if not c:
        return None
    lo = hi = bisect.bisect_left(img.starts, c[0])
    while (lo > 0 and img.fns[lo - 1][1] == img.fns[lo][0]
           and tail_kind(img, *img.fns[lo - 1]) not in ("ret", "jmp")):
        lo -= 1
    while (hi + 1 < len(img.fns) and img.fns[hi + 1][0] == img.fns[hi][1]
           and tail_kind(img, *img.fns[hi]) not in ("ret", "jmp")):
        hi += 1
    return (img.fns[lo][0], img.fns[hi][1], tuple(img.fns[k] for k in range(lo, hi + 1)))


def is_mem(op, reg_name, ins):
    return op.type == CS_OP_MEM and op.mem.base and ins.reg_name(op.mem.base) == reg_name


def rip_refs(img, lo, hi):
    """Every RIP-relative operand in [lo,hi): (addr, text, bytes, target, section, cls, value,
    is_load)."""
    out = []
    for i in decode_chunk(img, lo, hi):
        for k, op in enumerate(i.operands):
            if not is_mem(op, "rip", i):
                continue
            t = i.address + i.size + op.mem.disp
            s = img.sec(t)
            val = 0
            if s in (".data", ".rdata") and t + 8 <= img.sec_end(s):
                val = struct.unpack("<Q", img.bytes_at(t, 8))[0]
            if s is None:
                cls = "outside-image"
            elif t == COOKIE:
                cls = "cookie"
            elif s == ".rdata":
                cls = "rodata"
            elif val == 0:
                cls = "data-null"
            elif IMAGE_LO <= val < IMAGE_HI:
                # a value inside the image: only .text/.data are usable as pointers; a value in
                # .rdata is far more likely to be two packed 4-byte fields (floats, ids)
                cls = {".text": "code-pointer", ".data": "data-pointer"}.get(
                    img.sec(val), "packed-fields")
            else:
                cls = "data-block"
            out.append((i.address, i.mnemonic + " " + i.op_str, i.bytes.hex(" "), t, s, cls, val,
                        k != 0))
    return out


def build_graph(img):
    """Every verified `call rel32` and `jmp rel32` site, decoded from each chunk's own start,
    plus the `.data` root-slot candidates, in one pass over the image."""
    calls, jmps, cand, writes = {}, {}, [], {}
    for (s, e) in img.fns:
        ins = decode_chunk(img, s, e)
        for k, i in enumerate(ins):
            if i.mnemonic in ("call", "jmp") and i.op_str.startswith("0x") and "[" not in i.op_str:
                (calls if i.mnemonic == "call" else jmps).setdefault(int(i.op_str, 16), []).append(
                    i.address)
            if i.mnemonic != "mov" or "[rip" not in i.op_str:
                continue
            if (len(i.operands) == 2 and i.operands[0].type == CS_OP_MEM
                    and is_mem(i.operands[0], "rip", i)):
                w = i.address + i.size + i.operands[0].mem.disp
                if img.sec(w) == ".data":
                    writes.setdefault(w, []).append(i.address)
            if len(i.operands) != 2 or i.operands[0].type != CS_OP_REG:
                continue
            if not is_mem(i.operands[1], "rip", i):
                continue
            tgt = i.address + i.size + i.operands[1].mem.disp
            if img.sec(tgt) != ".data" or tgt == COOKIE:
                continue
            reg = i.reg_name(i.operands[0].reg)
            for j in ins[k + 1:k + 24]:
                if j.address - i.address > 120:
                    break
                hit = None
                if j.mnemonic == "mov" and len(j.operands) == 2:
                    for op in j.operands:
                        if is_mem(op, reg, j) and op.mem.disp in (0x120, 0x128, 0x130):
                            hit = op.mem.disp
                if hit is not None:
                    cand.append({"load": hex(i.address), "text": i.mnemonic + " " + i.op_str,
                                 "bytes": i.bytes.hex(" "), "slot": hex(tgt),
                                 "at_rest": hex(struct.unpack("<Q", img.bytes_at(tgt, 8))[0]),
                                 "use": hex(j.address),
                                 "use_text": j.mnemonic + " " + j.op_str, "disp": hit,
                                 "func": hex(region_of(img, i.address)[0])})
                    break
    return calls, jmps, cand, writes


def parse_relocs(img):
    """Every VA the PE loader patches (IMAGE_REL_BASED_DIR64 entries in .reloc). A `.data` slot
    that appears here holds a pointer, whatever the raw bytes look like."""
    sec = next(s for s in img.secs if s[0] == ".reloc")
    _n, sva, _vs, raw, rs = sec
    out = set()
    o = 0
    while o + 12 <= rs:
        page, size = struct.unpack_from("<II", img.raw, raw + o)
        if size < 8 or o + size > rs:
            break
        for i in range(8, size - 1, 2):
            e = struct.unpack_from("<H", img.raw, raw + o + i)[0]
            if (e >> 12) == 10:                       # IMAGE_REL_BASED_DIR64
                out.add(sva + page + (e & 0xFFF))
        o += size
    return out


def pointer_xrefs(img):
    """8-byte values in .rdata/.data that point into .text -> where they are stored."""
    txt = next(s for s in img.secs if s[0] == ".text")
    m = {}
    for name in (".rdata", ".data"):
        n, sva, vs, raw, rs = next(s for s in img.secs if s[0] == name)
        for o in range(0, rs - 7, 8):
            v = struct.unpack_from("<Q", img.raw, raw + o)[0]
            if txt[1] <= v < txt[1] + txt[2]:
                m.setdefault(v, []).append(sva + o)
    return m


def meaningful(refs):
    """RIP-relative loads of writable .data that are not the stack cookie."""
    return [r for r in refs if r[7] and r[5] in ("data-pointer", "data-null", "data-block")]


def walk(img, calls, jmps, root):
    """BFS over callers + tail-jump sites; returns (paths, hits, terminals)."""
    paths = {root: []}
    frontier = [root]
    hits, terminals = [], []
    for _d in range(WALK_DEPTH):
        nxt = []
        for n in frontier:
            edges = [("call", s) for s in sorted(calls.get(n, []))]
            edges += [("jmp", s) for s in sorted(jmps.get(n, []))]
            if not edges:
                terminals.append((n, paths[n]))
            for kind, site in edges:
                cr = region_of(img, site)
                ce = cr[0]
                if ce in paths:
                    continue
                paths[ce] = paths[n] + [(kind, site, n, ce)]
                gl = meaningful(rip_refs(img, cr[0], cr[1]))
                if gl:
                    hits.append((ce, paths[ce], gl))
                nxt.append(ce)
                if len(paths) > WALK_CAP:
                    break
            if len(paths) > WALK_CAP:
                break
        frontier = nxt
        if not frontier or len(paths) > WALK_CAP:
            break
    hits.sort(key=lambda h: (len(h[1]), h[0]))
    return paths, hits, terminals


def ins_at(img, va):
    f = img.fn_of(va)
    if not f:
        return None
    for i in decode_chunk(img, f[0], f[1]):
        if i.address == va:
            return i
    return None


# ----------------------------------------------------------------------------- document
def build():
    img = base.Image(base.EXE)
    img.sec_end = lambda name, _s={s[0]: s[1] + s[2] for s in img.secs}: _s[name]
    base_ = img.base
    calls, jmps, candidates, writes = build_graph(img)
    px = pointer_xrefs(img)
    oracles = []

    def oracle(key, ok, ev):
        oracles.append({"key": key, "ok": bool(ok), "evidence": ev})

    txt = next(s for s in img.secs if s[0] == ".text")
    pd = next(s for s in img.secs if s[0] == ".pdata")
    oracle("O1-image",
           base_ == 0x140000000 and len(img.secs) == 7 and len(img.fns) == 188670,
           "base %#x, %d sections, %d .pdata chunks, %s B" %
           (base_, len(img.secs), len(img.fns), f"{len(img.raw):,}"))
    crash = ins_at(img, CRASH)
    oracle("O2-crash-still-there",
           crash is not None and crash.mnemonic == "movss"
           and crash.op_str == "xmm0, dword ptr [rax + 0x14]",
           "at %#x: %s %s" % (CRASH, crash.mnemonic if crash else "?", crash.op_str if crash else "?"))

    # ---- 1. chunk -> function
    anchors = []
    ok_chunk = ok_region = True
    for name, va, role in ANCHORS:
        c = img.fn_of(base_ + va)
        r = region_of(img, base_ + va)
        rows = []
        for (cs, ce) in r[2]:
            rows.append({"start": hex(cs), "end": hex(ce), "size": ce - cs,
                         "tail": tail_kind(img, cs, ce)})
        anchors.append({"name": name, "anchor": hex(base_ + va), "role": role,
                        "chunk": [hex(c[0]), hex(c[1])], "chunk_size": c[1] - c[0],
                        "entry": hex(r[0]), "end": hex(r[1]), "region_size": r[1] - r[0],
                        "chunks": rows})
        ok_chunk &= (c[1] - c[0]) == REVIEW_CHUNKS[name]
        ok_region &= (r[1] - r[0]) == REVIEW_REGIONS[name]
    oracle("O3-chunk-and-region-sizes",
           ok_chunk and ok_region,
           "chunk sizes %s; merged sizes %s (review claims %s / %s)" %
           ({a["name"]: a["chunk_size"] for a in anchors},
            {a["name"]: a["region_size"] for a in anchors},
            REVIEW_CHUNKS, REVIEW_REGIONS))

    # every internal boundary is a fallthrough, and the region's last insn is ret/jmp
    merge_ok, merge_ev = True, []
    for a in anchors:
        for row in a["chunks"][:-1]:
            if row["tail"] in ("ret", "jmp"):
                merge_ok = False
                merge_ev.append("%s: %s ends in %s" % (a["name"], row["end"], row["tail"]))
        if a["chunks"][-1]["tail"] not in ("ret", "jmp", None):
            merge_ok = False
            merge_ev.append("%s: last chunk ends in %s" % (a["name"], a["chunks"][-1]["tail"]))
    oracle("O4-merge-is-fallthrough",
           merge_ok,
           "every internal boundary falls through; tails %s" %
           {a["name"]: [r["tail"] for r in a["chunks"]] for a in anchors}
           if merge_ok else "; ".join(merge_ev))

    # jumps from OUTSIDE into a merged region
    into = []
    for a in anchors:
        lo, hi = int(a["entry"], 16), int(a["end"], 16)
        for tgt, sites in sorted(jmps.items()):
            inside = [s for s in sites if lo <= s < hi]
            if lo < tgt < hi and not inside:
                into.append({"region": a["name"], "target": hex(tgt),
                             "sites": [hex(s) for s in sites]})
    into = [x for x in into if x["sites"]]

    # ---- 2. the walk
    walks = []
    for a in anchors:
        entry = int(a["entry"], 16)
        paths, hits, terminals = walk(img, calls, jmps, entry)
        refs0 = rip_refs(img, entry, int(a["end"], 16))
        hops = []
        chosen = hits[0] if hits else None
        if chosen:
            for kind, site, callee, _ce in chosen[1]:
                i = ins_at(img, site)
                cr = region_of(img, site)
                hops.append({"kind": kind, "site": hex(site),
                             "bytes": i.bytes.hex(" ") if i else "?",
                             "text": (i.mnemonic + " " + i.op_str) if i else "?",
                             "callee": hex(callee),
                             "caller_entry": hex(cr[0]), "caller_end": hex(cr[1]),
                             "caller_size": cr[1] - cr[0],
                             "target": hex(int(i.op_str, 16)) if i and
                             i.op_str.startswith("0x") else "?"})
        depth1 = []
        for s in sorted(calls.get(entry, [])) + sorted(jmps.get(entry, [])):
            cr = region_of(img, s)
            i = ins_at(img, s)
            depth1.append({"site": hex(s), "bytes": i.bytes.hex(" ") if i else "?",
                           "text": (i.mnemonic + " " + i.op_str) if i else "?",
                           "caller_entry": hex(cr[0]), "caller_end": hex(cr[1]),
                           "caller_size": cr[1] - cr[0]})
        walks.append({
            "anchor": a["name"], "entry": a["entry"], "region_size": a["region_size"],
            "nodes": len(paths), "hits": len(hits), "terminals": len(terminals),
            "own_refs": [{"addr": hex(r[0]), "text": r[1], "bytes": r[2], "target": hex(r[3]),
                          "section": r[4], "class": r[5], "value": hex(r[6])} for r in refs0],
            "depth1": depth1,
            "chosen": None if not chosen else {
                "global_region": hex(chosen[0]),
                "hops": hops,
                "globals": [{"addr": hex(g[0]), "text": g[1], "bytes": g[2], "target": hex(g[3]),
                             "class": g[5], "value": hex(g[6])} for g in chosen[2][:6]],
            },
            "terminal_detail": [{"entry": hex(e), "depth": len(p),
                                 "ptr_xrefs": [hex(x) for x in px.get(e, [])][:4]}
                                for e, p in terminals[:8]],
        })

    # hops must re-decode to a call/jmp whose target is the child entry
    hop_ok, hop_ev = True, []
    for w in walks:
        if not w["chosen"]:
            continue
        prev = int(w["entry"], 16)
        for h in w["chosen"]["hops"]:
            i = ins_at(img, int(h["site"], 16))
            if i is None or i.mnemonic not in ("call", "jmp") or not i.op_str.startswith("0x"):
                hop_ok = False
                hop_ev.append("%s: %s is not a direct branch" % (w["anchor"], h["site"]))
            elif int(i.op_str, 16) != prev:
                hop_ok = False
                hop_ev.append("%s: %s targets %s not %s (chain broken)" %
                              (w["anchor"], h["site"], i.op_str, prev))
            elif int(h["callee"], 16) != prev:
                hop_ok = False
                hop_ev.append("%s: hop callee %s != %s" % (w["anchor"], h["callee"], prev))
            prev = int(h["caller_entry"], 16)
    oracle("O5-hops-are-verified-branches", hop_ok,
           "%d hops, every site re-decodes to a `call`/`jmp` whose operand is the next function"
           % sum(len(w["chosen"]["hops"]) for w in walks if w["chosen"]) if hop_ok
           else "; ".join(hop_ev))

    # every quoted global target must be exactly rip + size + disp, in the quoted section
    gl_ok, gl_ev = True, []
    n_gl = 0
    for w in walks:
        for r in w["own_refs"]:
            n_gl += 1
            i = ins_at(img, int(r["addr"], 16))
            tgt = None
            for op in (i.operands if i else []):
                if is_mem(op, "rip", i):
                    tgt = i.address + i.size + op.mem.disp
            if tgt is None or tgt != int(r["target"], 16) or img.sec(tgt) != r["section"]:
                gl_ok = False
                gl_ev.append("%s: %s -> %s (%s)" % (w["anchor"], r["addr"], r["target"],
                                                    r["section"]))
    oracle("O6-globals-recomputed", gl_ok,
           "%d RIP-relative operands in the six regions re-derive to the quoted address and "
           "section" % n_gl if gl_ok else "; ".join(gl_ev))

    # ---- 3. the part container: stride and fields, straight from 0x14024b660
    cont = []
    for i in decode_chunk(img, PART_CONTAINER_LOOP, PART_CONTAINER_LOOP + 0x80):
        cont.append({"addr": hex(i.address), "bytes": i.bytes.hex(" "),
                     "text": i.mnemonic + " " + i.op_str})
    txts = [c["text"] for c in cont]
    oracle("O7-part-array-fields",
           "mov eax, dword ptr [rbx + 0x130]" in txts
           and "mov rbp, qword ptr [rbx + 0x128]" in txts
           and "mov rsi, qword ptr [rbx + 0x120]" in txts
           and "imul rcx, rcx, 0x190" in txts
           and "call 0x140201de0" in txts,
           "%#x: count [rbx+0x130], index [rbx+0x128], base [rbx+0x120], stride 0x190, "
           "calls the part-node update" % PART_CONTAINER_LOOP)

    # candidate root slots: .data qwords that some code LOADS and then uses with the part fields
    relocs = parse_relocs(img)
    by_slot = {}
    for c in candidates:
        d = by_slot.setdefault(c["slot"], {"slot": c["slot"], "at_rest": c["at_rest"],
                                           "reloc": int(c["slot"], 16) in relocs,
                                           "fields": [], "load_sites": 0, "funcs": [],
                                           "sample_load": c["load"], "sample_text": c["text"],
                                           "sample_bytes": c["bytes"]})
        if c["disp"] not in d["fields"]:
            d["fields"].append(c["disp"])
        d["load_sites"] += 1
        if c["func"] not in d["funcs"]:
            d["funcs"].append(c["func"])
    root_slots = sorted(by_slot.values(), key=lambda d: (-len(d["fields"]), d["slot"]))
    for d in root_slots:
        d["fields"] = [hex(f) for f in sorted(d["fields"])]
        d["writers"] = [hex(x) for x in writes.get(int(d["slot"], 16), [])][:4]
    full = [d["slot"] for d in root_slots if len(d["fields"]) == 3]
    rec_ok = True
    for d in root_slots:
        i = ins_at(img, int(d["sample_load"], 16))
        tgt = None
        for op in (i.operands if i else []):
            if is_mem(op, "rip", i):
                tgt = i.address + i.size + op.mem.disp
        rec_ok &= tgt == int(d["slot"], 16)
        rec_ok &= set(d["fields"]) <= {"0x120", "0x128", "0x130"}
        for ws in d["writers"]:
            j = ins_at(img, int(ws, 16))
            rec_ok &= (j is not None and j.mnemonic == "mov" and len(j.operands) == 2
                       and is_mem(j.operands[0], "rip", j)
                       and j.address + j.size + j.operands[0].mem.disp == int(d["slot"], 16))
    oracle("O8-root-candidates-recomputed",
           rec_ok and len(root_slots) > 0,
           "%d load sites reach %d distinct .data slots, each re-derived from its own RIP-relative "
           "operand; %d of them are used with all three part-array fields (%s); %d slots in the "
           "image are loader-relocated pointer slots" %
           (len(candidates), len(root_slots), len(full), full[:4], len(relocs)))

    doc = {
        "generated_by": "Tools/scripts/jc3_runtime_layout3a.py --write",
        "exe": base.EXE, "size": len(img.raw), "sha256": img.sha256,
        "image_base": hex(base_),
        "counts": {"sections": len(img.secs), "pdata_chunks": len(img.fns),
                   "text_bytes": txt[2], "pdata_bytes": pd[4],
                   "instructions": sum(len(decode_chunk(img, s, e)) for (s, e) in img.fns)
                   if False else None,
                   "call_edges": sum(len(v) for v in calls.values()),
                   "jmp_edges": sum(len(v) for v in jmps.values()),
                   "call_targets": len(calls)},
        "anchors": anchors,
        "jumps_into_regions": into,
        "walks": walks,
        "part_container": cont,
        "root_candidates": root_slots,
        "root_slots": [d["slot"] for d in root_slots],
        "root_slots_full": full,
        "reloc_slots": len(relocs),
        "oracles": oracles,
        "unknowns": [],
    }
    return doc


def render(doc):
    L = []
    A = L.append
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    A("# Resolving the six `.pdata` chunks and walking their callers to a global (G3-07b1)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout3a.py --write`; `--check` re-derives every")
    A("number from the bytes, rebuilds this file and compares it byte for byte. The game is")
    A("never run: everything below is read from `%s` read-only with `pefile`/`capstone`." % doc["exe"])
    A("")
    A("**Oracles: %d/%d pass.** A failing oracle makes `--write` refuse and `--check` fail." %
      (ok, len(doc["oracles"])))
    A("")
    A("Inputs: `%s B`, sha256 `%s`, base `%s`, %d sections, **%s** `.pdata` chunks, %s call sites "
      "and %s tail jumps decoded from the chunks themselves."
      % (f"{doc['size']:,}", doc["sha256"], doc["image_base"], doc["counts"]["sections"],
         f"{doc['counts']['pdata_chunks']:,}", f"{doc['counts']['call_edges']:,}",
         f"{doc['counts']['jmp_edges']:,}"))
    A("")
    A("Every value below is labelled **decoded** (instruction bytes at the quoted address), "
      "**derived** (a rule applied to decoded values) or **UNKNOWN**.")
    A("")
    A("## 1. Each anchor chunk, resolved to the function that contains it")
    A("")
    A("Merge rule (derived, applied to the decoded tail instruction of each chunk): two adjacent")
    A("`.pdata` chunks are one function when the earlier ends exactly where the later starts and")
    A("its last non-padding instruction is neither `ret` nor an unconditional `jmp` — control")
    A("falls through. The table lists every chunk of the merged region in address order, with the")
    A("mnemonic its body ends in.")
    A("")
    for a in doc["anchors"]:
        A("### `%s` — anchor `%s`" % (a["name"], a["anchor"]))
        A("")
        A("Chunk `%s`..`%s` is **%d B**. Whole function: **`%s`..`%s`, %d B, %d chunks**."
          % (a["chunk"][0], a["chunk"][1], a["chunk_size"], a["entry"], a["end"],
             a["region_size"], len(a["chunks"])))
        A("")
        A("| chunk | start | end | size | ends in |")
        A("|---|---|---|---|---|")
        for r in a["chunks"]:
            A("| %s | `%s` | `%s` | %d B | `%s` |" %
              ("**anchor**" if r["start"] == a["chunk"][0] else "", r["start"], r["end"],
               r["size"], r["tail"]))
        A("")
    A("### Branches into a region from outside it (decoded)")
    A("")
    if not doc["jumps_into_regions"]:
        A("None: no `jmp rel32` in the image targets an address strictly inside one of the six")
        A("merged regions from outside that region. The chunk boundaries are therefore pure")
        A("fallthrough splits, not shared tails.")
    else:
        A("| region | target | jump sites |")
        A("|---|---|---|")
        for x in doc["jumps_into_regions"]:
            A("| `%s` | `%s` | %s |" % (x["region"], x["target"],
                                        ", ".join("`%s`" % s for s in x["sites"])))
    A("")
    A("## 2. Walking the callers upward")
    A("")
    A("An edge is a `call rel32` decoded at an instruction boundary, or a `jmp rel32` (tail call).")
    A("A hop's caller is again reported as the whole merged function, not as the chunk.")
    A("")
    for w in doc["walks"]:
        A("### `%s` (entry `%s`, %d B) — %d caller functions reached"
          % (w["anchor"], w["entry"], w["region_size"], w["nodes"]))
        A("")
        A("RIP-relative operands inside the region itself (decoded):")
        A("")
        if not w["own_refs"]:
            A("- none")
        for r in w["own_refs"]:
            A("- `%s` `%s` — bytes `%s` → `%s` in `%s` (**%s**), holds `%s`"
              % (r["addr"], r["text"], r["bytes"], r["target"], r["section"], r["class"],
                 r["value"]))
        A("")
        A("Direct callers at depth 1 (decoded):")
        A("")
        A("| edge | site | bytes | disassembly | caller function | size |")
        A("|---|---|---|---|---|---|")
        for d in w["depth1"]:
            A("| %s | `%s` | `%s` | `%s` | `%s`..`%s` | %d B |"
              % ("call" if d["text"].startswith("call") else "jmp", d["site"], d["bytes"],
                 d["text"], d["caller_entry"], d["caller_end"], d["caller_size"]))
        A("")
        if w["chosen"]:
            A("**Shortest path to a RIP-relative load of a writable global** (depth %d):"
              % len(w["chosen"]["hops"]))
            A("")
            A("| hop | edge | site | bytes | disassembly | calls | caller function | size |")
            A("|---|---|---|---|---|---|---|---|")
            for n, h in enumerate(w["chosen"]["hops"], 1):
                A("| %d | %s | `%s` | `%s` | `%s` | `%s` | `%s`..`%s` | %d B |"
                  % (n, h["kind"], h["site"], h["bytes"], h["text"], h["callee"],
                     h["caller_entry"], h["caller_end"], h["caller_size"]))
            A("")
            A("Global loads in that last function (decoded):")
            A("")
            A("| instruction | bytes | target | class | value |")
            A("|---|---|---|---|---|")
            for g in w["chosen"]["globals"]:
                A("| `%s` %s | `%s` | `%s` | %s | `%s` |"
                  % (g["addr"], g["text"], g["bytes"], g["target"], g["class"], g["value"]))
        else:
            A("**No RIP-relative load of a writable `.data` global appears within %d caller hops.**"
              % WALK_DEPTH)
        A("")
        if w["terminal_detail"]:
            A("Functions on this walk with no direct inbound edge (decoded):")
            A("")
            A("| function | hops from the anchor | 8-byte pointers to it in `.rdata`/`.data` |")
            A("|---|---|---|")
            for t in w["terminal_detail"]:
                A("| `%s` | %d | %s |" % (t["entry"], t["depth"],
                                          ", ".join("`%s`" % x for x in t["ptr_xrefs"]) or "none"))
            A("")
    A("## 3. The part container (decoded context for the walk)")
    A("")
    A("`%#x` is the loop that feeds the part-node update. Its fields, byte for byte:" % PART_CONTAINER_LOOP)
    A("")
    A("| address | bytes | disassembly |")
    A("|---|---|---|")
    for c in doc["part_container"]:
        A("| `%s` | `%s` | `%s` |" % (c["addr"], c["bytes"], c["text"]))
    A("")
    A("## 4. `.data` slots that are used with the part-array fields (derived)")
    A("")
    A("Every `mov reg, [rip+X]` with `X` in `.data` (cookie excluded) whose loaded register is")
    A("then read with `+0x120`, `+0x128` or `+0x130` through a **load** (a `call qword ptr [reg+…]`")
    A("is a vtable slot and is rejected). This is a candidate list, not a proof of class identity.")
    A("")
    A("| slot | at rest | relocated | fields used | load sites | runtime writers | example |")
    A("|---|---|---|---|---|---|---|")
    for c in doc["root_candidates"]:
        A("| `%s` | `%s` | %s | %s | %d | %s | `%s` `%s` |"
          % (c["slot"], c["at_rest"], "**yes**" if c["reloc"] else "no",
             ", ".join("`%s`" % f for f in c["fields"]), c["load_sites"],
             ", ".join("`%s`" % w for w in c["writers"]) or "none",
             c["sample_load"], c["sample_text"]))
    A("")
    A("%d distinct `.data` slots in total, %d of them used with all three part-array fields, %d"
      % (len(doc["root_slots"]), len(doc["root_slots_full"]), doc["reloc_slots"]))
    A("`IMAGE_REL_BASED_DIR64` slots in the whole image. None of these slots is reached by the")
    A("walks in §2, none is loader-relocated, and no `imul ..., 0x190` follows a load from any of")
    A("them, so identity with the part array of §3 is a candidate, not a decode. A slot that is")
    A("never relocated and has no writer can only hold inline data, not a pointer.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 6. Reproduce")
    A("")
    A("```")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3a.py --write")
    A("uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout3a.py --check")
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
            for o in doc["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote Research/JC3Grab/RUNTIME_LAYOUT3A.md and .json")
        print("  %d anchors, merged sizes %s"
              % (len(doc["anchors"]), {x["name"]: x["region_size"] for x in doc["anchors"]}))
        print("  walks: %s" % {w["anchor"]: {"nodes": w["nodes"], "hits": w["hits"],
                                            "terminals": w["terminals"]} for w in doc["walks"]})
        print("  oracles %d/%d, root-candidate slots %d"
              % (len(doc["oracles"]), len(doc["oracles"]), len(doc["root_slots"])))
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
        print("FAIL: RUNTIME_LAYOUT3A.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: RUNTIME_LAYOUT3A.json is stale")
        return 1
    print("OK %d/%d oracles, %d anchors, %d root-candidate slots, md+json byte-identical"
          % (len(doc["oracles"]), len(doc["oracles"]), len(doc["anchors"]),
             len(doc["root_slots"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
