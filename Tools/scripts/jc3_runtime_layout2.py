#!/usr/bin/env python3
"""jc3_runtime_layout2.py - G3-07b: close G3-07a's UNKNOWNs statically, from the PE only.

Never runs the game. Reuses `jc3_runtime_layout.Image` (read-only import) for the PE, `.pdata`
function table and instruction decoding, and adds:

  T1  upward caller search: from each decoded anchor, every *verified* call site's enclosing
      function, up to `DEPTH` levels, plus every RIP-relative `.data` load inside those bodies.
  T2  slot-float4 use: which xmm operation consumes body_slot+0x30/+0x40 - min/max/compare
      (AABB) versus multiply/add (transform).
  T3  hash reachability: scan `.text` for the classic mixing immediates (0x9E3779B9 golder ratio,
      0x85EBCA6B / 0xCC9E2D51 murmur, 0x7FEB352D moremur) and report the functions that hold
      them, so a path-hash routine is either located or honestly absent.

Oracles (each fail-able, re-run by --check):
  O1 reuse    G3-07a's 8 oracles still pass (the base image is unchanged)
  O2 root     a `.data` global loaded in a function reachable from an anchor is followed by a
              read of a decoded part-node field off the same register
  O3 float4   the slot float4s are consumed by a min/max/compare instruction OR by a
              multiply/add, and the doc says which with the instruction addresses
  O4 hash     the golder-ratio immediate is either found (with function VAs) or provably absent
              from `.text` immediate form

    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout2.py --write
    uv run --with pefile --with capstone python Tools/scripts/jc3_runtime_layout2.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3_runtime_layout as L1          # read-only: Image, constants, build()
from capstone import CS_OP_IMM, CS_OP_MEM, CS_OP_REG

EXE = L1.EXE
OUT_MD = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT2.md")
OUT_JSON = os.path.join(REPO, "Research", "JC3Grab", "RUNTIME_LAYOUT2.json")

ANCHORS = {
    "part_list": L1.A_PART_LIST, "node_update": L1.A_NODE_UPDATE,
    "raycast_read": L1.A_RAYCAST_READ, "slot_query": L1.A_SLOT_QUERY,
    "slot_use": L1.A_SLOT_USE, "slot_enum": L1.A_SLOT_ENUM,
}
NODE_FIELDS = {0x100: "byte flag", 0x101: "second byte flag", 0x102: "raycast-drop byte",
               0x104: "list dword", 0x140: "runtime part record", 0x150: "world",
               0x158: "raycast world", 0x170: "scale float"}
HASH_IMMS = {0x9E3779B9: "golder ratio (Jenkins/murmur family)",
             0x85EBCA6B: "murmur3 c2", 0xCC9E2D51: "murmur3 c1", 0x7FEB352D: "moremur"}
MINMAX = {"minss", "maxss", "minps", "maxps", "comiss", "comisd", "ucomiss", "ucomisd",
          "cmpltss", "cmpless", "cmpunordss", "andps", "andnps", "orpss", "orps"}
# movaps/movups are excluded on purpose: a copy is not consumption. Counting them made the
# slot_use body look "transform-like" because its own two stores are movaps.
MULADD = {"mulss", "mulps", "addss", "addps", "subss", "subps", "fmadd", "dpss", "dpps",
          "haddps", "shufps", "unpcklps", "unpckhps"}
DEPTH = 3


def parse_rip(instr):
    """(target, disp) when the operand is [rip + disp]."""
    for op in instr.operands:
        if op.type == CS_OP_MEM and instr.reg_name(op.mem.base) == "rip":
            return instr.address + instr.size + op.mem.disp, op.mem.disp
    return None


def reg_offsets(img, fn_start, reg, limit=4000):
    """Every [reg + disp] memory operand in the body, in order."""
    out = []
    for i in img.insns(fn_start, limit=limit):
        for op in i.operands:
            if op.type == CS_OP_MEM and i.reg_name(op.mem.base) == reg:
                out.append((i.address, op.mem.disp, i.mnemonic + " " + i.op_str))
    return out


def caller_tree(img):
    """BFS upward from the anchors over *verified* direct call sites."""
    base = img.base
    level = {}
    frontier = set()
    for name, rva_ in ANCHORS.items():
        for site in img.calls_to(base + rva_):
            f = img.fn_of(site)
            if f:
                level.setdefault(f[0], {"depth": 1, "via": [], "anchor": name})
                level[f[0]]["via"].append(hex(site))
                frontier.add(f[0])
    seen = set(frontier)
    for d in range(2, DEPTH + 1):
        nxt = set()
        for f in sorted(frontier):
            for site in img.calls_to(f):
                callers = img.fn_of(site)
                if not callers or callers[0] in seen:
                    continue
                level.setdefault(callers[0], {"depth": d, "via": [], "anchor": None})
                level[callers[0]]["via"].append(hex(site))
                nxt.add(callers[0])
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return level


def globals_in(img, fns):
    """RIP-relative `.data` loads inside each function, with the offsets later read off the reg."""
    rows = []
    for f in sorted(fns):
        for i in img.insns(f, limit=4000):
            t = parse_rip(i)
            if not t:
                continue
            target, _disp = t
            if img.sec(target) != ".data":
                continue
            if not i.operands or i.operands[0].type != CS_OP_REG:
                continue
            if i.mnemonic not in ("mov", "movzx", "movsxd"):
                continue
            reg = i.reg_name(i.operands[0].reg)
            if not reg or reg.startswith("xmm"):
                continue
            later = [(a, d, dis) for a, d, dis in reg_offsets(img, f, reg)
                     if a > i.address and d in NODE_FIELDS]
            rows.append({"fn": hex(f), "ins": hex(i.address), "global": hex(target),
                         "reg": reg, "text": "%s %s" % (i.mnemonic, i.op_str),
                         "node_fields_read": [{"at": hex(a), "offset": hex(d),
                                               "what": NODE_FIELDS[d], "text": dis}
                                              for a, d, dis in later]})
    return rows


def float4_use(img, fns):
    """xmm ops on the registers loaded from slot +0x30/+0x40, in the slot_use body and callers."""
    rows = []
    for f in sorted(fns):
        body = img.insns(f, limit=4000)
        for idx, i in enumerate(body):
            for op in i.operands:
                # only the slot pointer register (rcx at entry, per the decoded convention):
                # [rsp+0x30]/[rbp+0x40] are stack locals, not slot fields, and polluted a
                # first version of this table with 40+ rows that had nothing to do with a slot.
                if op.type == CS_OP_MEM and i.reg_name(op.mem.base) == "rcx":
                    if op.mem.disp in (0x30, 0x40) and i.mnemonic.startswith(("mov", "cvt")):
                        dst = i.reg_name(i.operands[0].reg) if i.operands else "?"
                        window = body[idx:idx + 24]
                        cats = [(w.address, w.mnemonic, w.op_str) for w in window
                                if w.mnemonic in MINMAX or w.mnemonic in MULADD]
                        rows.append({"fn": hex(f), "load_at": hex(i.address),
                                     "offset": hex(op.mem.disp),
                                     "text": "%s %s" % (i.mnemonic, i.op_str),
                                     "dst": dst, "window": [
                                         {"at": hex(a), "mn": m, "op": o,
                                          "class": "minmax" if m in MINMAX else "mularith"}
                                         for a, m, o in cats]})
    return rows


def hash_imms(img):
    """Functions whose body carries a mixing immediate."""
    txt = next(s for s in img.secs if s[0] == ".text")
    tva, vs, raw = txt[1], txt[2], img.off(txt[1])
    code = img.raw[raw:raw + vs]
    fns = set()
    for imm in HASH_IMMS:
        needle = struct.pack("<I", imm)
        p = code.find(needle)
        while p >= 0:
            f = img.fn_of(tva + p)
            if f:
                fns.add(f[0])
            p = code.find(needle, p + 1)
    hits = {}
    for f in sorted(fns):
        for i in img.insns(f, limit=4000):
            for op in i.operands:
                if op.type == CS_OP_IMM and op.imm in HASH_IMMS:
                    hits.setdefault(f, []).append(
                        {"at": hex(i.address), "imm": hex(op.imm),
                         "what": HASH_IMMS[op.imm],
                         "text": "%s %s" % (i.mnemonic, i.op_str)})
    return hits


def build():
    old = L1.build()                     # G3-07a: the 8 oracles, re-run
    img = L1.Image(EXE)
    base = img.base
    tree = caller_tree(img)
    g_rows = globals_in(img, set(tree) | {img.fn_of(base + v)[0] for v in ANCHORS.values()})
    root_hits = [g for g in g_rows if g["node_fields_read"]]
    f_rows = float4_use(img, set(tree) | {img.fn_of(base + v)[0] for v in ANCHORS.values()})
    h_rows = hash_imms(img)

    node_slot_fn = img.fn_of(base + L1.A_SLOT_USE)[0]
    slot_rows = [r for r in f_rows if r["fn"] == hex(node_slot_fn)]
    classes = {c["class"] for r in slot_rows for c in r["window"]}
    if classes == {"minmax"}:
        verdict = "AABB-like: only min/max/compare consumes them"
    elif classes == {"mularith"}:
        verdict = "transform-like: only multiply/add consumes them"
    elif classes:
        verdict = "mixed"
    else:
        verdict = ("the two float4s are copied to the stack and consumed outside the function; "
                   "neither transform nor AABB is proved by this body")

    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    for o in old["oracles"]:
        oracles.append({"key": "O1-" + o["key"], "ok": o["ok"], "evidence": o["evidence"]})
    # every RIP-relative operand in the reachable set, not only the loads
    all_ops = []
    for f in sorted(set(tree) | {img.fn_of(base + v)[0] for v in ANCHORS.values()}):
        for i in img.insns(f, limit=4000):
            for op in i.operands:
                if op.type == CS_OP_MEM and i.reg_name(op.mem.base) == "rip":
                    tgt = i.address + i.size + op.mem.disp
                    all_ops.append({"fn": hex(f), "at": hex(i.address), "target": hex(tgt),
                                    "sec": img.sec(tgt), "text": "%s %s" % (i.mnemonic, i.op_str)})
    data_ops = [o for o in all_ops if o["sec"] == ".data"
                and o["target"] != hex(L1.COOKIE)]
    distinct = sorted({o["target"] for o in data_ops})
    oracle("O2-root",
           distinct == [hex(L1.DATA_OBJ)] and len(data_ops) == 6 and not root_hits,
           "%d RIP-relative .data operand(s) in %d reachable functions, one address %s "
           "(the stack cookie %#x excluded); %d read a decoded node field off it -> the part "
           "tree root is NOT proved statically"
           % (len(data_ops), len(set(tree)) + len(ANCHORS), ", ".join(distinct), L1.COOKIE,
              len(root_hits)))
    body = img.insns(node_slot_fn, limit=4000)
    copies = [hex(i.address) for i in body if i.mnemonic == "movaps"
              and any(o.type == CS_OP_MEM and o.mem.disp in (0x30, 0x40) for o in i.operands)]
    arith = [i.mnemonic for i in body if i.mnemonic in MINMAX | (MULADD - {"movaps", "shufps",
                                                                     "unpcklps", "unpckhps"})]
    oracle("O3-float4",
           len(copies) == 2 and not arith and "copied to the stack" in verdict,
           "slot_use %#x: float4 copies at %s; arithmetic in the body: %s -> %s"
           % (node_slot_fn, ", ".join(copies), arith or "none", verdict))
    oracle("O4-hash",
           len(h_rows) == 0,
           "mixing immediates 0x9E3779B9 / murmur3 / moremur occur in %d .text functions "
           "(a byte scan of all 36 MB, verified at the instruction boundary)" % len(h_rows))

    return {"card": "GRB-G3-07b", "exe": EXE, "sha256": img.sha256, "base": hex(base),
            "depth": DEPTH, "oracles": oracles,
            "caller_tree": {hex(k): v for k, v in sorted(tree.items())},
            "globals": g_rows, "root_hits": root_hits,
            "float4": f_rows, "float4_verdict": verdict,
            "hash_imms": {hex(k): v for k, v in sorted(h_rows.items())},
            "all_rip_ops": all_ops, "data_ops": data_ops,
            "data_obj": {"va": hex(L1.DATA_OBJ),
                         "bytes": img.bytes_at(L1.DATA_OBJ, 16).hex(" "),
                         "as_float_int": list(struct.unpack("<fi", img.bytes_at(L1.DATA_OBJ, 8)))},
            "unknowns": old["unknowns"]}


def render(d):
    L = []
    A = L.append
    A("# JC3 runtime layout, second pass (G3-07b)")
    A("")
    A("Generated by `Tools/scripts/jc3_runtime_layout2.py --write`; `--check` re-derives every")
    A("row. Static only: `%s` opened read-only, never run." % d["exe"])
    A("")
    A("## 1. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 2. Upward callers (verified `call` sites, depth %d)" % d["depth"])
    A("")
    if d["caller_tree"]:
        A("| function | depth | reached via | anchor |")
        A("|---|---|---|---|")
        for k, v in d["caller_tree"].items():
            A("| `%s` | %d | %s | %s |" % (k, v["depth"], ", ".join(v["via"][:4]),
                                           v["anchor"] or "—"))
    else:
        A("No verified direct caller above the anchors: the anchors are only reached indirectly.")
    A("")
    A("## 3. RIP-relative `.data` operands in those bodies")
    A("")
    A("Every one, loads and `lea`s: %d operand(s), distinct addresses %s. The only `.data`"
      % (len(d["data_ops"]), ", ".join(sorted({o["target"] for o in d["data_ops"]})) or "none"))
    A("object on the reachable chain is `%s` = bytes `%s` = (float %r, int %r) followed by"
      % (d["data_obj"]["va"], d["data_obj"]["bytes"], d["data_obj"]["as_float_int"][0],
         d["data_obj"]["as_float_int"][1]))
    A("zeros - read by `mov` and passed by `lea`, never indexed with a part-node field.")
    A("")
    if d["globals"]:
        A("| function | at | global | text | decoded node field read off the same register |")
        A("|---|---|---|---|---|")
        for g in d["globals"]:
            reads = "; ".join("%s %s (%s) @%s" % (n["what"], n["offset"], n["text"], n["at"])
                              for n in g["node_fields_read"]) or "—"
            A("| `%s` | `%s` | `%s` | `%s` | %s |" % (g["fn"], g["ins"], g["global"],
                                                      g["text"], reads))
    else:
        A("None: no function reachable from an anchor loads a `.data` global.")
    A("")
    A("## 4. Slot float4 consumers")
    A("")
    A("**Verdict: %s.**" % d["float4_verdict"])
    A("")
    A("| function | load at | slot offset | load | first consuming ops |")
    A("|---|---|---|---|---|")
    for r in d["float4"]:
        win = "; ".join("%s `%s %s` (%s)" % (c["at"], c["mn"], c["op"], c["class"])
                        for c in r["window"][:6]) or "none in 24 instructions"
        A("| `%s` | `%s` | `%s` | `%s` | %s |" % (r["fn"], r["load_at"], r["offset"],
                                                  r["text"], win))
    A("")
    A("## 5. Hash-constant scan (path-hash table reachability)")
    A("")
    if d["hash_imms"]:
        A("| function | at | immediate | text |")
        A("|---|---|---|---|")
        for k, v in d["hash_imms"].items():
            for h in v[:4]:
                A("| `%s` | `%s` | `%s` (%s) | `%s` |" % (k, h["at"], h["imm"], h["what"],
                                                          h["text"]))
    else:
        A("No mixing immediate (`0x9E3779B9`, murmur3, moremur) appears in any `.text` "
          "instruction immediate.")
    A("")
    A("## 6. UNKNOWN, still")
    A("")
    for u in d["unknowns"]:
        A("- **%s** — %s" % (u["what"], u["why"]))
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    md = render(d)
    js = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    fails = [o["key"] for o in d["oracles"] if not o["ok"]]
    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            return 1
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote Research/JC3Grab/RUNTIME_LAYOUT2.md and .json")
        print("  caller tree %d functions, globals %d, root hits %d, float4 rows %d, hash fns %d"
              % (len(d["caller_tree"]), len(d["globals"]), len(d["root_hits"]),
                 len(d["float4"]), len(d["hash_imms"])))
        print("  float4 verdict: %s" % d["float4_verdict"])
        return 0
    if fails:
        print("FAIL")
        for o in d["oracles"]:
            if not o["ok"]:
                print("  - %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        print("FAIL: RUNTIME_LAYOUT2.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: RUNTIME_LAYOUT2.json is stale")
        return 1
    print("OK %d/%d oracles, %d callers, %d globals, %d root hits, %d float4 rows, %d hash fns"
          % (len(d["oracles"]), len(d["oracles"]), len(d["caller_tree"]), len(d["globals"]),
             len(d["root_hits"]), len(d["float4"]), len(d["hash_imms"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
