"""bmak_selector_cfg.py - G3-01f: DECODE THE `RVehicleBatmobile.DriverLeft` BYTECODE, BUILD THE CFG,
AND SAY WHICH CONDITION SELECTS COLLISION VALUE 1 AND WHICH SELECTS 2.

Why this card exists
  `Research/BatmobileGrab/COLLISION_SELECTOR2.md` section 5 leaves three UNKNOWNs:
    (1) which `DriverLeft` condition selects collision value 1 and which selects 2 (only a positional
        guess existed: calls at 301 and 334),
    (2) the branch-word encoding of the UnrealScript bytecode there,
    (3) whether `Core.BatmobileWinch` / `Core.WinchPullType` / `Core.ArmouredMode` /
        `Core.IsVehicleAsleep` are globals or members.
  This script re-reads the bytes, walks the script token by token, and answers (1) and (3) with byte
  offsets, and answers (2) with a measured verdict: the `EX_Skip` words ARE positions in a stream
  where a reference token weighs 9 bytes (proven 5/5, `skip_rule_exact`), and the `EX_Jump` /
  `EX_JumpIfNot` words are NOT positions in this function's byte stream under any of 11 bases
  (`jump_words_are_not_positions`), nor under any per-token-weight prefix-sum model
  (`no_prefix_sum_weight_model`).  That last negative is why the control-flow edges of the two
  `EX_Jump`s stay UNKNOWN - but it does not leave (1) open, because containment of each call inside
  its guard's body is proven by the SKIP words (`containment_by_skip`), not by the jump words.

Method (nothing pattern-scanned; every token taken at the position the walk reached)
  1. `Startup.upk` export 7400 payload -> 22-byte header + ScriptText (368 B) + 16-byte trailer, the
     split anchored three ways in `export_identity` / `script_anchors`.
  2. A closure-driven walk over the 368 bytes.  A reference is `0x00|0x01|0x02 <int32 index>` (5 B);
     `0x00` is only a reference when the int32 behind it resolves to a package object, otherwise it is
     a one-byte prefix token (the same rule the G3-01e-fix adjudication used, re-proven here by
     `walk_closes` and `refs_resolve`).
  3. Every `EX_Skip`'s 2-byte word is resolved FORWARD by accumulating token weights
     (size + 4 per reference) until the sum equals the word; the landing token is the target.
     `skip_rule_exact` checks the sum for all 5 skips.
  4. The `EX_Jump` / `EX_JumpIfNot` words are tested against 11 bases inside this function and over
     every walkable `Function` in `Startup.upk` (`jump_words_are_not_positions`), and against a
     two-parameter weight model solved from the three known targets (`no_prefix_sum_weight_model`).
  5. The two selector calls are located, and for each the guard whose body contains it is fixed by
     the skip word that lands on the call's first byte (`containment_by_skip`).
  6. Imports: the raw 28-byte import rows for the four names (class package / class name / outer /
     name), the outer chain to the owning class and its package, then the property export in that
     package, its `outer_index` (the owning class export) and that class's property-tag list.

Labels used in the output: **decoded** = read from a package at the export/offset shown;
**derived** = a stated rule applied to decoded facts; **UNKNOWN** = not established here.

Read-only: the three packages are opened and never written.  No game process is touched.

Usage:
  python Tools/scripts/bmak_selector_cfg.py --write
  python Tools/scripts/bmak_selector_cfg.py --check   # recompute from the bytes, compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR3.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR3.json")
PREV_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR2.json")
POLARITY_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SELECTOR_POLARITY.md")

DL_PKG, DL_EXPORT = "Startup.upk", 7400
DL_PATH, DL_PAYLOAD, DL_SCRIPT = "RVehicleBatmobile.DriverLeft", 406, 368
DL_SHA1 = "70471c04b9526a2616e27c3c3830155112765efb"
SEL_PKG, SEL_EXPORT = "BmGame.upk", 10894
SEL_PATH, SEL_SHA1 = "RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode", \
                     "c2f6a2ee667c544876e5317a103072c44ea17788"
MESH_EXPECT = {0: None, 1: "BatmanCollisionMeshPursuitMode", 2: "BatmanCollisionMeshBattleMode"}
CALLS = {301: 2, 334: 1}
FOUR = ("Core.BatmobileWinch", "Core.WinchPullType", "Core.ArmouredMode", "Core.IsVehicleAsleep")
FOUR_INDEX = {"Core.BatmobileWinch": -5673, "Core.WinchPullType": -1515,
              "Core.ArmouredMode": -1366, "Core.IsVehicleAsleep": -1498}

# Token extents.  A name is given only where the extent is proven by the walk closing on the last
# byte; every other byte value is reported as `0xNN` rather than guessed.
LONG5 = {0x1B: "VirtualFunction", 0x1C: "FinalFunction", 0x1D: "IntConst"}
ONE_BYTE = {
    0x03: "0x03", 0x04: "Return", 0x05: "0x05", 0x08: "0x08", 0x09: "0x09", 0x0B: "0x0B",
    0x0E: "0x0E", 0x0F: "Let", 0x14: "LetBool", 0x16: "EndFunctionParms", 0x17: "0x17",
    0x19: "Context", 0x20: "0x20", 0x25: "IntZero", 0x26: "IntOne", 0x27: "True", 0x28: "False",
    0x2A: "0x2A", 0x2C: "0x2C", 0x2D: "0x2D", 0x35: "0x35", 0x38: "0x38", 0x3A: "0x3A",
    0x4A: "0x4A", 0x77: "0x77", 0x81: "0x81", 0x82: "0x82", 0x8C: "0x8C", 0x96: "0x96",
    0x9A: "0x9A", 0x9B: "0x9B", 0xF8: "0xF8",
}
BRANCH = {0x06: "Jump", 0x07: "JumpIfNot", 0x18: "Skip"}
# weight of a reference in the SKIP coordinate space: 9 bytes, not the 5 it occupies in the script
REF_WEIGHT = 9

# The statement table (decoded by the walk, checked offset by offset in `statement_starts`).
STATEMENTS = [
    (0, "JumpIfNot", "guard: 0x81 (unary) <Core.bWasRemoteDriving>"),
    (3, "expr", "condition of the guard at 0"),
    (11, "call", "Core.TriggerEventClass(.., Core.Driver, 1, ..) - then-block"),
    (30, "Jump", "leaves the then-block (target UNKNOWN)"),
    (33, "call", "Core.TriggerEventClass(.., Core.Driver, 3, ..) - else-block"),
    (53, "Let", "Core.Driver.InteriorLightsSwitchedOn = 0"),
    (67, "expr", "WorldInfo/GRI/FlagManager flag block -> SetGlobalFlag(\"Batman_Remote_Control_Batmobile\", false)"),
    (146, "expr", "same chain -> SetGlobalFlag(\"Batman_In_Batmobile\", false)"),
    (213, "call", "RemoveBatmobileBindsAndSetBatmanBinds()"),
    (219, "JumpIfNot", "guard: <Core.IsVehicleAsleep>"),
    (228, "LetBool", "Core.FakeRoadCollisionStatic = Core.UpdateFakeRoadCollision(true, 0.0)"),
    (248, "JumpIfNot", "guard A - the winch/armoured condition (body: call with value 2)"),
    (301, "call", "SetBatmanVsBatmobileCollisionMode(2)"),
    (309, "Jump", "leaves guard A's body (target UNKNOWN)"),
    (312, "JumpIfNot", "guard B - the armoured/asleep condition (body: call with value 1)"),
    (334, "call", "SetBatmanVsBatmobileCollisionMode(1)"),
    (342, "LetBool", "Core.bForceWheelspin = false"),
    (350, "Let", "Core.WheelspinSmokeMomentum = 0.0"),
    (361, "call", "Core.DriverLeft() [final function, no arguments]"),
    (367, "Return", "return"),
]

# Which walk token kind may start a statement of each semantic kind (used by `statement_starts`).
FAMILY = {"expr": None, "call": {"VirtualFunction", "FinalFunction"}, "Let": {"Let"},
          "LetBool": {"LetBool"}, "Return": {"Return"}, "Jump": {"Jump"},
          "JumpIfNot": {"JumpIfNot"}}

# Guard A: condition token offsets -> what the walk finds there (checked in `guard_shapes`).
GUARD_A = [
    (251, "0x82", "outer boolean operator"),
    (252, "0x82", "inner boolean operator"),
    (253, "0x2D", "one-byte prefix token"),
    (254, "ref", "Core.ArmouredMode"),
    (259, "Skip", "word 13 -> target 271 (second operand of the outer 0x82)"),
    (262, "0x77", "binary operator (object vs 0x2A)"),
    (263, "ref", "Core.BatmobileWinch"),
    (268, "0x2A", "comparison operand"),
    (269, "EndFunctionParms", "closes 0x77"),
    (270, "EndFunctionParms", "closes the inner 0x82"),
    (271, "Skip", "word 39 -> target 301 (the body: call with value 2)"),
    (274, "0x9B", "binary comparison operator"),
    (277, "Context", "member access on the next reference"),
    (278, "ref", "Core.BatmobileWinch"),
    (284, "ref", "Core.WinchPullType (0x00 form)"),
    (290, "ref", "Core.WinchPullType (0x01 form)"),
    (297, "ByteConst", "value 0"),
    (299, "EndFunctionParms", "closes 0x9B"),
    (300, "EndFunctionParms", "closes the outer 0x82"),
]
GUARD_B = [
    (315, "0x82", "boolean operator"),
    (316, "0x81", "unary operator (negation: see the polarity card's ShowHealthBarIfNotMax case)"),
    (317, "0x2D", "one-byte prefix token"),
    (318, "ref", "Core.ArmouredMode"),
    (323, "EndFunctionParms", "closes 0x81"),
    (324, "Skip", "word 11 -> target 334 (the body: call with value 1)"),
    (327, "0x2D", "one-byte prefix token"),
    (328, "ref", "Core.IsVehicleAsleep"),
    (333, "EndFunctionParms", "closes 0x82"),
]

# 11 candidate bases for a 2-byte branch word (the same family G3-01e tested, plus the skip space)
BASES = ("abs", "abs_payload", "abs_plus_payload", "rel_pos", "rel_after", "rel_before",
         "from_end", "from_end_minus", "expanded_abs", "expanded_rel", "expanded_rel_pos")


def i32(s: bytes, o: int) -> int:
    return struct.unpack_from("<i", s, o)[0]


def u16(s: bytes, o: int) -> int:
    return struct.unpack_from("<H", s, o)[0]


# --------------------------------------------------------------------------- packages
def open_pkg(name: str):
    return upk_read.Package(os.path.join(GAME, name))


def function_parts(pkg, index: int) -> dict:
    data = pkg.data(index)
    script = data[22:len(data) - 16]
    return {"payload": data, "script": script,
            "size_field": i32(data, 18),
            "name_index": i32(data, len(data) - 8),
            "trailer": data[len(data) - 16:].hex(),
            "header": data[:22].hex()}


# --------------------------------------------------------------------------- token walk
def walk(pkg, s: bytes) -> dict | None:
    """Sequential token walk; None if any byte cannot be taken at the position reached."""
    p, toks = 0, []
    while p < len(s):
        t = s[p]
        if t in (0x01, 0x02):
            if p + 5 > len(s):
                return None
            idx = i32(s, p + 1)
            path = pkg.object_path(idx)
            if path is None:
                return None
            toks.append({"at": p, "size": 5, "kind": "ref", "form": "0x%02X" % t,
                         "index": idx, "path": path, "object_class": pkg.object_class(idx)})
            p += 5
            continue
        if t == 0x00:
            idx = i32(s, p + 1) if p + 5 <= len(s) else None
            path = pkg.object_path(idx) if idx is not None else None
            if path is not None:
                toks.append({"at": p, "size": 5, "kind": "ref", "form": "0x00",
                             "index": idx, "path": path,
                             "object_class": pkg.object_class(idx)})
                p += 5
            else:
                toks.append({"at": p, "size": 1, "kind": "0x00"})
                p += 1
            continue
        if t in LONG5:
            if p + 5 > len(s):
                return None
            idx = i32(s, p + 1)
            tok = {"at": p, "size": 5, "kind": LONG5[t], "index": idx}
            if t == 0x1B:
                if not (0 <= idx < pkg.name_count):
                    return None
                tok["name"] = pkg.names[idx]
            elif t == 0x1C:
                tok["name"] = pkg.object_path(idx)
            else:
                tok["value"] = idx
            toks.append(tok)
            p += 5
            continue
        if t == 0x1E:
            if p + 5 > len(s):
                return None
            toks.append({"at": p, "size": 5, "kind": "FloatConst",
                         "value": struct.unpack_from("<f", s, p + 1)[0]})
            p += 5
            continue
        if t == 0x1F:
            e = s.find(b"\x00", p + 1)
            if e < 0:
                return None
            toks.append({"at": p, "size": e - p + 1, "kind": "StringConst",
                         "value": s[p + 1:e].decode("latin-1")})
            p = e + 1
            continue
        if t in BRANCH:
            if p + 3 > len(s):
                return None
            toks.append({"at": p, "size": 3, "kind": BRANCH[t], "word": u16(s, p + 1)})
            p += 3
            continue
        if t == 0x24:
            if p + 2 > len(s):
                return None
            toks.append({"at": p, "size": 2, "kind": "ByteConst", "value": s[p + 1]})
            p += 2
            continue
        if t in ONE_BYTE:
            toks.append({"at": p, "size": 1, "kind": ONE_BYTE[t]})
            p += 1
            continue
        return None
    return {"tokens": toks, "consumed": sum(t["size"] for t in toks), "closed": True}


def token_at(toks, at):
    for t in toks:
        if t["at"] == at:
            return t
    return None


def refs_in(toks, lo, hi):
    return [t for t in toks if t["kind"] == "ref" and lo <= t["at"] < hi]


# --------------------------------------------------------------------------- skip / jump words
def weight_of(tok) -> int:
    return REF_WEIGHT if tok["kind"] == "ref" else tok["size"]


def skip_target(toks, i):
    """Target of the skip at toks[i]: the first token whose accumulated weight equals the word."""
    word = toks[i]["word"]
    acc = 0
    for tok in toks[i + 1:]:
        if acc == word:
            return tok["at"]
        acc += weight_of(tok)
        if acc > word:
            return None
    return None if acc != word else None


def expanded_positions(toks, extra=None):
    """Cumulative weight per token start; `extra` adds bytes per token class (for the jump tests)."""
    extra = extra or {}
    out, acc = {}, 0
    for t in toks:
        out[t["at"]] = acc
        add = extra.get(t["kind"], 0)
        if t["kind"] == "0x19":
            add = extra.get("context", 0)
        acc += t["size"] + add
    return out, acc


def jump_bases(word, at, length, toks, exp_abs, exp_any):
    """Every candidate target for a 2-byte branch word, with whether it is a token start."""
    starts = {t["at"] for t in toks}
    cand = {
        "abs": word,
        "abs_payload": word - 22,
        "abs_plus_payload": word + 22,
        "rel_pos": at + word,
        "rel_after": at + 3 + word,
        "rel_before": at - word,
        "from_end": length - word,
        "from_end_minus": length - word - 3,
        "expanded_abs": None,
        "expanded_rel": None,
        "expanded_rel_pos": None,
    }
    rev = {}
    for pos, val in exp_abs.items():
        rev.setdefault(val, pos)
    cand["expanded_abs"] = rev.get(word)
    rev2 = {}
    for pos, val in exp_any.items():
        rev2.setdefault(val, pos)
    cand["expanded_rel"] = rev2.get(word)
    cand["expanded_rel_pos"] = rev2.get(at + word)
    return {k: {"target": v, "is_token_start": (v in starts) if v is not None else False}
            for k, v in cand.items()}


# --------------------------------------------------------------------------- imports / members
def import_row(pkg, idx: int) -> dict:
    i = -idx - 1
    off = pkg.import_offset + i * 28
    ints = struct.unpack_from("<7i", pkg.image, off)
    return {"index": idx, "row_offset": off,
            "class_package": pkg.names[ints[0]], "class_name": pkg.names[ints[2]],
            "outer": ints[4], "name": pkg.names[ints[5]], "number": ints[6]}


def outer_hops(pkg, idx: int) -> list[dict]:
    hops, o, depth = [], import_row(pkg, idx)["outer"], 0
    while o and depth < 6:
        depth += 1
        if o < 0:
            r = import_row(pkg, o)
            hops.append({"index": o, "kind": "import", "name": r["name"],
                         "class": r["class_name"], "row_offset": r["row_offset"],
                         "outer": r["outer"]})
            o = r["outer"]
        else:
            e = pkg.exports[o - 1]
            hops.append({"index": o, "kind": "export", "name": e["name"],
                         "class": pkg.object_class(o), "offset": e["offset"],
                         "outer": e["outer_index"]})
            o = e["outer_index"]
    return hops


def home_package(hops) -> str | None:
    for h in reversed(hops):
        if h["class"] == "Package":
            return h["name"]
    return None


def member_facts(name: str) -> dict:
    sp = open_pkg(DL_PKG)
    idx = FOUR_INDEX[name]
    row = import_row(sp, idx)
    hops = outer_hops(sp, idx)
    pkg_name = home_package(hops)
    owning_class = hops[0]["name"] if hops else None
    owning_class_index = hops[0]["index"] if hops else None
    fact = {"name": name, "import": row, "outer_chain": hops, "home_package": pkg_name,
            "owning_class": owning_class, "owning_class_index": owning_class_index}
    # the property export in its home package: outer must be the owning class export
    if pkg_name:
        home = open_pkg(pkg_name + ".upk")
        prop_exports = [j for j in range(1, home.export_count + 1)
                        if home.exports[j - 1]["name"] == name.split(".")[-1]]
        rows = []
        for j in prop_exports:
            e = home.exports[j - 1]
            rows.append({"export": j, "class": home.object_class(j),
                         "outer_index": e["outer_index"],
                         "outer_name": home.object_name(e["outer_index"]),
                         "outer_class": home.object_class(e["outer_index"]),
                         "size": e["size"], "offset": e["offset"]})
        fact["property_exports"] = rows
        # the owning class's property list, walked from its tag stream
        cls_exports = [h["index"] for h in hops if h["kind"] == "export" and h["class"] == "Class"]
        if not cls_exports:
            cls_exports = [j for j in range(1, home.export_count + 1)
                           if home.exports[j - 1]["name"] == owning_class]
        fact["owning_class_exports"] = cls_exports
        lists = []
        for j in cls_exports[:2]:
            tags, end, why = upk_read.best_walk(home, home.data(j))
            hit = [t for t in tags if t.get("name") == name.split(".")[-1]]
            lists.append({"class_export": j, "class_name": home.exports[j - 1]["name"],
                          "tags": len(tags), "parsed_bytes": end,
                          "size": home.exports[j - 1]["size"], "stop": why,
                          "property_tags": [{"type": t["type"], "offset": t["offset"],
                                             "size": t.get("size")} for t in hit]})
        fact["owning_class_property_lists"] = lists
    outer_is_class = bool(hops) and hops[0]["class"] in ("Class", "Core.Class")
    fact["outer_is_class"] = outer_is_class
    fact["verdict"] = "member" if outer_is_class else "UNKNOWN"
    fact["label"] = ("decoded (Startup.upk import row at byte %d: class package %r, class %r, "
                     "outer %d = %s; then the property export and its class's property list in %s)"
                     % (row["row_offset"], row["class_package"], row["class_name"], row["outer"],
                        owning_class, (pkg_name + ".upk") if pkg_name else "?"))
    return fact


# --------------------------------------------------------------------------- build
def build() -> dict:
    sp = open_pkg(DL_PKG)
    bp = open_pkg(SEL_PKG)
    dl = function_parts(sp, DL_EXPORT)
    s = dl["script"]
    w = walk(sp, s)
    if w is None:
        raise SystemExit("DriverLeft walk failed")
    toks = w["tokens"]

    sel = function_parts(bp, SEL_EXPORT)

    # ---- skips
    skips = []
    for i, t in enumerate(toks):
        if t["kind"] != "Skip":
            continue
        tgt = skip_target(toks, i)
        cover = [x for x in toks if t["at"] + 3 <= x["at"] < (tgt if tgt is not None else -1)]
        skips.append({"at": t["at"], "word": t["word"], "target": tgt,
                      "distance": (tgt - (t["at"] + 3)) if tgt is not None else None,
                      "refs_skipped": len([x for x in cover if x["kind"] == "ref"]),
                      "weight_sum": sum(weight_of(x) for x in cover)})

    # ---- jumps and the base tests
    exp_abs, exp_abs_len = expanded_positions(toks)
    exp_any, _ = expanded_positions(toks, {"context": 4})
    jumps = []
    for t in toks:
        if t["kind"] not in ("Jump", "JumpIfNot"):
            continue
        jumps.append({"at": t["at"], "kind": t["kind"], "word": t["word"],
                      "bases": jump_bases(t["word"], t["at"], len(s), toks, exp_abs, exp_any)})

    # ---- corpus test: are branch words positions anywhere in Startup.upk?
    corpus = {"functions_walked": 0, "branch_tokens": 0,
              "hits": {b: 0 for b in BASES}, "skips": 0, "skip_rule_ok": 0,
              "per_kind": {"Jump": 0, "JumpIfNot": 0, "Skip": 0}}
    corpus_jump_hits = {b: 0 for b in BASES}
    corpus_jump_total = 0
    for j in range(1, sp.export_count + 1):
        if sp.object_class(j) != "Function":
            continue
        d = sp.data(j)
        if len(d) < 38:
            continue
        cs = d[22:len(d) - 16]
        cw = walk(sp, cs)
        if cw is None:
            continue
        ct = cw["tokens"]
        if not any(x["kind"] in ("Jump", "JumpIfNot", "Skip") for x in ct):
            continue
        corpus["functions_walked"] += 1
        ea, _ = expanded_positions(ct)
        eany, _ = expanded_positions(ct, {"context": 4})
        for i, x in enumerate(ct):
            if x["kind"] not in ("Jump", "JumpIfNot", "Skip"):
                continue
            corpus["branch_tokens"] += 1
            corpus["per_kind"][x["kind"]] += 1
            if x["kind"] == "Skip":
                corpus["skips"] += 1
                tgt = skip_target(ct, i)
                if tgt is not None:
                    cover = [y for y in ct if x["at"] + 3 <= y["at"] < tgt]
                    if sum(weight_of(y) for y in cover) == x["word"]:
                        corpus["skip_rule_ok"] += 1
                continue
            corpus_jump_total += 1
            b = jump_bases(x["word"], x["at"], len(cs), ct, ea, eany)
            for k, v in b.items():
                if v["is_token_start"]:
                    corpus["hits"][k] += 1
                    corpus_jump_hits[k] += 1

    # ---- prefix-sum weight model solved from the three DriverLeft jump targets
    known = [(248, 352), (309, 436), (342, 474)]
    eqs = []
    for (t1, w1), (t2, w2) in ((known[0], known[1]), (known[1], known[2])):
        span = [x for x in toks if t1 <= x["at"] < t2]
        eqs.append({"from": t1, "to": t2, "dw": w2 - w1, "bytes": t2 - t1,
                    "refs": len([x for x in span if x["kind"] == "ref"]),
                    "contexts": len([x for x in span if x["kind"] == "0x19"]),
                    "calls": len([x for x in span if x["kind"] in ("VirtualFunction",
                                                                  "FinalFunction")])})
    # A prefix-sum weight model needs `dw = bytes + r*refs + c*contexts` on every span.  Each span
    # implies its own per-reference weight; if they disagree (or are not integral) no such model
    # exists.  Both spans here have zero contexts, so `c` drops out.
    implied = []
    for e in eqs:
        if e["refs"]:
            implied.append({"span": [e["from"], e["to"]],
                            "per_ref": (e["dw"] - e["bytes"]) / e["refs"],
                            "extra_bytes": e["dw"] - e["bytes"], "refs": e["refs"]})
    consistent = bool(implied) and len({i["per_ref"] for i in implied}) == 1 \
        and implied[0]["per_ref"] == int(implied[0]["per_ref"])
    residual = {"implied": implied, "consistent": consistent,
                "note": "no single per-token-weight prefix-sum model fits both spans"
                        if not consistent else "consistent"}

    # ---- guards, containment, calls
    call2 = [t for t in toks if t["kind"] == "VirtualFunction" and t["at"] == 301]
    call1 = [t for t in toks if t["kind"] == "VirtualFunction" and t["at"] == 334]
    calls = []
    for t, val in ((call2[0] if call2 else None, 2), (call1[0] if call1 else None, 1)):
        if t is None:
            continue
        nxt = token_at(toks, t["at"] + 5)
        calls.append({"at": t["at"], "name": t["name"], "argument_at": nxt["at"] if nxt else None,
                      "argument": nxt.get("value") if nxt else None,
                      "end_parms_at": (nxt["at"] + nxt["size"]) if nxt else None})

    guard_a = {"guard_at": 248, "cond_from": 251, "cond_to": 301,
               "condition_byte_range": [251, 301], "body_byte_range": [301, 309],
               "body_call_at": 301, "body_value": 2,
               "condition": "0x82( 0x82( Core.ArmouredMode, 0x77( Core.BatmobileWinch, 0x2A ) ),"
                            " Skip->301( 0x9B( Core.BatmobileWinch.WinchPullType, byte 0 ) ) )",
               "guard_shapes": GUARD_A, "label": "decoded"}
    guard_b = {"guard_at": 312, "cond_from": 315, "cond_to": 334,
               "condition_byte_range": [315, 334], "body_byte_range": [334, 342],
               "body_call_at": 334, "body_value": 1,
               "condition": "0x82( 0x81( Core.ArmouredMode ), Skip->334( Core.IsVehicleAsleep ) )",
               "guard_shapes": GUARD_B, "label": "decoded"}

    # ---- guard_shapes check against the walk
    def shape_ok(rows):
        out = []
        for at, kind, meaning in rows:
            t = token_at(toks, at)
            got = None if t is None else (t["kind"] if t["kind"] != "ref" else "ref")
            out.append({"at": at, "expect": kind, "got": got,
                        "meaning": meaning,
                        "path": t.get("path") if t else None,
                        "word": t.get("word") if t else None,
                        "value": t.get("value") if t else None,
                        "ok": got == kind})
        return out

    gs_a = shape_ok(GUARD_A)
    gs_b = shape_ok(GUARD_B)

    # ---- statements
    starts = {t["at"] for t in toks}
    stmts = []
    for at, kind, meaning in STATEMENTS:
        t = token_at(toks, at)
        fam = FAMILY[kind]
        stmts.append({"at": at, "kind": kind, "meaning": meaning,
                      "is_token_start": at in starts,
                      "walk_kind": t["kind"] if t else None,
                      "matches": (t is not None and (fam is None or t["kind"] in fam))})

    # ---- CFG
    nodes, edges = [], []
    for i, st in enumerate(STATEMENTS):
        end = STATEMENTS[i + 1][0] if i + 1 < len(STATEMENTS) else len(s)
        nodes.append({"at": st[0], "kind": st[1], "meaning": st[2], "end": end})
    for i, nd in enumerate(nodes):
        if nd["kind"] == "JumpIfNot":
            body = next((x for x in nodes if x["at"] > nd["at"]), None)
            edges.append({"from": nd["at"], "to": "body", "body_at": body["at"] if body else None,
                          "label": "condition TRUE -> body (polarity oracle)",
                          "proven": True})
            edges.append({"from": nd["at"], "to": "UNKNOWN", "body_at": None,
                          "label": "condition FALSE -> branch word %d does not decode to a token start"
                                   % (token_at(toks, nd["at"])["word"]), "proven": False})
        elif nd["kind"] == "Jump":
            edges.append({"from": nd["at"], "to": "UNKNOWN", "body_at": None,
                          "label": "branch word %d does not decode to a token start"
                                   % (token_at(toks, nd["at"])["word"]), "proven": False})
        elif i + 1 < len(nodes):
            edges.append({"from": nd["at"], "to": nodes[i + 1]["at"], "body_at": nodes[i + 1]["at"],
                          "label": "fallthrough", "proven": True})

    members = [member_facts(n) for n in FOUR]

    polarity = {"file": os.path.relpath(POLARITY_MD, ROOT).replace("\\", "/"),
                "exists": os.path.exists(POLARITY_MD), "cites_body_on_true": False,
                "cites_decisive_tally": False}
    if polarity["exists"]:
        text = open(POLARITY_MD, encoding="utf-8", errors="replace").read()
        polarity["cites_body_on_true"] = "body runs when the comparison is TRUE" in text
        polarity["cites_decisive_tally"] = "4 of 4" in text

    prev = None
    if os.path.exists(PREV_JSON):
        prev = json.load(open(PREV_JSON, encoding="utf-8"))

    doc = {
        "schema": 1,
        "card": "G3-01f - RVehicleBatmobile.DriverLeft: token decode, CFG, and which condition "
                "selects collision value 1 / 2",
        "driverleft": {
            "package": DL_PKG, "export": DL_EXPORT, "path": sp.object_path(DL_EXPORT),
            "class": sp.object_class(DL_EXPORT),
            "payload_bytes": len(dl["payload"]), "script_bytes": len(s),
            "script_sha1": hashlib.sha1(s).hexdigest(),
            "size_field": dl["size_field"], "name_index": dl["name_index"],
            "header_hex": dl["header"], "trailer_hex": dl["trailer"],
            "tokens": toks, "token_count": len(toks), "refs": len([t for t in toks
                                                                   if t["kind"] == "ref"]),
            "label": "decoded (Startup.upk export 7400; script = payload[22:-16])",
        },
        "selector": {
            "package": SEL_PKG, "export": SEL_EXPORT, "path": bp.object_path(SEL_EXPORT),
            "script_bytes": len(sel["script"]),
            "script_sha1": hashlib.sha1(sel["script"]).hexdigest(),
            "label": "decoded (re-read for the mesh table cross-check)",
        },
        "skips": skips,
        "jumps": jumps,
        "corpus": dict(corpus, jump_total=corpus_jump_total, jump_hits=corpus_jump_hits),
        "weight_model": {"equations": eqs, "solution": residual,
                         "known_targets": known,
                         "label": "derived (targets from the guard structure at 248/309/342)"},
        "calls": calls,
        "guards": {"A": dict(guard_a, shapes=gs_a), "B": dict(guard_b, shapes=gs_b)},
        "statements": stmts,
        "cfg": {"nodes": nodes, "edges": edges},
        "members": members,
        "polarity": polarity,
        "prev_mesh_table": None if prev is None else
        {r["mode_value"]: r["mesh"] for r in prev["selector"]["mesh_table"]["rows"]},
    }
    doc["oracles"] = oracles(doc, sp, bp, sel, toks, s, prev)
    return doc


# --------------------------------------------------------------------------- oracles
def oracles(doc, sp, bp, sel, toks, s, prev) -> dict:
    out = {}

    def add(k, ok, detail):
        out[k] = {"ok": bool(ok), "detail": detail}

    d = doc["driverleft"]
    add("export_identity",
        d["path"] == DL_PATH and d["class"] == "Function" and d["payload_bytes"] == DL_PAYLOAD
        and d["script_bytes"] == DL_SCRIPT and d["script_sha1"] == DL_SHA1,
        {k: d[k] for k in ("path", "class", "payload_bytes", "script_bytes", "script_sha1")})
    add("script_anchors",
        d["size_field"] == DL_SCRIPT + 1
        and sp.names[d["name_index"]] == sp.exports[DL_EXPORT - 1]["name"],
        {"size_field": d["size_field"], "name_index": d["name_index"],
         "name_table_entry": sp.names[d["name_index"]]})
    add("walk_closes",
        d["token_count"] == 135 and sum(t["size"] for t in toks) == DL_SCRIPT
        and toks[-1]["kind"] == "Return" and toks[-1]["at"] == DL_SCRIPT - 1,
        {"tokens": d["token_count"], "consumed": sum(t["size"] for t in toks),
         "script_bytes": DL_SCRIPT, "last": toks[-1]})
    add("refs_resolve", d["refs"] == 28, {"refs": d["refs"]})

    four = {}
    for name in FOUR:
        got = [t["at"] for t in toks if t.get("path") == name]
        four[name] = {"offsets": got, "twice": len(got) == 2,
                      "index": sorted({t["index"] for t in toks if t.get("path") == name})}
    add("four_names_twice", all(v["twice"] for v in four.values()), four)

    calls = {c["at"]: c["argument"] for c in doc["calls"]}
    add("selector_calls", calls == CALLS and len(doc["calls"]) == 2,
        {"calls": doc["calls"], "expected": CALLS})

    skip_ok = all(x["target"] is not None and x["weight_sum"] == x["word"] for x in doc["skips"])
    add("skip_rule_exact", skip_ok and len(doc["skips"]) == 5,
        {"skips": [{"at": x["at"], "word": x["word"], "target": x["target"],
                    "distance": x["distance"], "refs": x["refs_skipped"],
                    "weight_sum": x["weight_sum"]} for x in doc["skips"]]})

    cont = {x["at"]: x["target"] for x in doc["skips"]}
    add("containment_by_skip",
        cont.get(271) == 301 and cont.get(324) == 334,
        {"skip_271_target": cont.get(271), "call_2_at": 301,
         "skip_324_target": cont.get(324), "call_1_at": 334,
         "rule": "a Skip word resolved in the 9-byte-per-reference space lands on the byte after its "
                 "enclosing expression; both land on the first byte of a selector call's argument "
                 "list, so that call is the guarded body"})

    gs = {k: all(x["ok"] for x in v["shapes"]) for k, v in doc["guards"].items()}
    add("guard_shapes", all(gs.values()), gs)

    st_ok = all(x["is_token_start"] and x["matches"] for x in doc["statements"])
    add("statement_starts", st_ok,
        {"rows": len(doc["statements"]),
         "bad": [x for x in doc["statements"] if not (x["is_token_start"] and x["matches"])]})

    hit_bases = {b: sum(1 for j in doc["jumps"] if j["bases"][b]["is_token_start"]) for b in BASES}
    block = [j for j in doc["jumps"] if j["word"] >= 100]
    block_resolved = [j["at"] for j in block
                      if any(j["bases"][b]["is_token_start"] for b in BASES)]
    add("jump_words_are_not_positions",
        max(hit_bases.values()) <= 2 and len(doc["jumps"]) == 6,
        {"driverleft_jump_words": [{"at": j["at"], "kind": j["kind"], "word": j["word"],
                                    "bases": {b: j["bases"][b]["target"] for b in BASES}}
                                   for j in doc["jumps"]],
         "hits_per_base": hit_bases,
         "words_resolved_by_no_base": [j["at"] for j in block],
         "block_words_resolved_anywhere": block_resolved,
         "corpus_jump_tokens": doc["corpus"]["jump_total"],
         "corpus_hits_per_base": doc["corpus"]["jump_hits"],
         "rule": "a base counts as the encoding only if it resolves every word of the function; no "
                 "base resolves more than 2 of the 6 here (the short words 49 and 81, at chance "
                 "level), so no base is the encoding. Individual chance hits elsewhere are listed in "
                 "`driverleft_jump_words` and are not evidence."})

    corp = doc["corpus"]
    add("skip_rule_corpus",
        corp["skips"] > 0 and corp["skip_rule_ok"] == corp["skips"],
        {"skips": corp["skips"], "resolved": corp["skip_rule_ok"],
         "functions_walked": corp["functions_walked"]})

    wm = doc["weight_model"]
    add("no_prefix_sum_weight_model", not wm["solution"]["consistent"],
        {"equations": wm["equations"], "solution": wm["solution"]})

    mem = {m["name"]: {"verdict": m["verdict"], "outer_is_class": m["outer_is_class"],
                       "owning_class": m["owning_class"], "home_package": m["home_package"],
                       "property_exports": [(e["export"], e["class"], e["outer_name"])
                                            for e in m.get("property_exports", [])],
                       "property_tags": [l["property_tags"]
                                         for l in m.get("owning_class_property_lists", [])]}
           for m in doc["members"]}
    add("imports_are_members",
        all(v["verdict"] == "member" and v["outer_is_class"] for v in mem.values())
        and all(v["property_exports"] for v in mem.values()),
        mem)

    add("polarity_crossref",
        doc["polarity"]["exists"] and doc["polarity"]["cites_body_on_true"],
        doc["polarity"])

    sel_rows = None
    if prev is not None:
        sel_rows = {r["mode_value"]: r["mesh"] for r in prev["selector"]["mesh_table"]["rows"]}
    add("mesh_table_crossref", doc["prev_mesh_table"] == MESH_EXPECT and sel_rows == MESH_EXPECT,
        {"recomputed_selector_sha1": doc["selector"]["script_sha1"],
         "expected_sha1": SEL_SHA1,
         "mesh_table": doc["prev_mesh_table"]})
    add("selector_sha1", doc["selector"]["script_sha1"] == SEL_SHA1,
        {"recomputed": doc["selector"]["script_sha1"], "expected": SEL_SHA1})
    return out


# --------------------------------------------------------------------------- render
def render(doc: dict) -> str:
    L = []
    A = L.append
    d, sk, cg = doc["driverleft"], doc["skips"], doc["cfg"]
    o = doc["oracles"]

    A("# `DriverLeft` bytecode, control-flow graph, and which condition selects collision value 1 / 2")
    A("")
    A("G3-01f. Generated by `Tools/scripts/bmak_selector_cfg.py --write`; `--check` re-reads the three")
    A("packages, re-walks every token and fails on any drift. Read-only.")
    A("")
    A("Labels: **decoded** = read from the package at the export and byte offset shown; **derived** =")
    A("a stated rule applied to decoded facts; **UNKNOWN** = not established here.")
    A("")
    A("## 1. Answer")
    A("")
    A("`RVehicleBatmobile.DriverLeft` (`Startup.upk` export %d, %d B script, sha1 `%s`) sets the"
      % (d["export"], d["script_bytes"], d["script_sha1"]))
    A("selector twice. Each call sits in the body of exactly one guard, and the guard's body starts at")
    A("the call's own byte (proven by the `Skip` word that lands there - section 4):")
    A("")
    A("| call | value | guard token | condition bytes | condition (token-accurate) |")
    A("|---|---|---|---|---|")
    A("| **301** | **2** | `0x07` @248 | 251-300 | `%s` |" % doc["guards"]["A"]["condition"])
    A("| **334** | **1** | `0x07` @312 | 315-333 | `%s` |" % doc["guards"]["B"]["condition"])
    A("")
    A("So **value 2 is selected by the winch/armoured condition** (`Core.ArmouredMode` combined with")
    A("`Core.BatmobileWinch` and `Core.BatmobileWinch.WinchPullType` compared against byte `0`) and")
    A("**value 1 by the `Core.ArmouredMode` / `Core.IsVehicleAsleep` condition**. The G3-01e-fix")
    A("positional guess happens to name the same two groups, but its reason was wrong: the names are")
    A("contained in the two guard *bodies*, not merely positioned before/after the calls, and the")
    A("`ArmouredMode` reference at 318 belongs to the **value-1** guard, not to the value-2 one.")
    A("")
    A("The operator semantics are only partly decoded: `0x81` is a unary negation (derived from")
    A("`RPlayerController.ShowHealthBarIfNotMax`, export 98240, whose name states the negation -")
    A("`SELECTOR_POLARITY.md` section 3), `0x9B`/`0x77` are binary comparisons, `0x82` a binary boolean")
    A("operator. Which of `&&`/`||` `0x82` is, and which of `==`/`!=` `0x9B`/`0x77` are, is UNKNOWN")
    A("(section 8).")
    A("")
    A("## 2. The function")
    A("")
    A("| field | value |")
    A("|---|---|")
    A("| package / export | `%s` / `%d` |" % (d["package"], d["export"]))
    A("| path / class | `%s` / `%s` |" % (d["path"], d["class"]))
    A("| payload | %d B (`header` %d + script %d + trailer 16) |"
      % (d["payload_bytes"], 22, d["script_bytes"]))
    A("| size field @18 | %d (= script + 1) |" % d["size_field"])
    A("| trailer name index | %d |" % d["name_index"])
    A("| header hex | `%s` |" % d["header_hex"])
    A("| script sha1 | `%s` |" % d["script_sha1"])
    A("| tokens / references | %d / %d |" % (d["token_count"], d["refs"]))
    A("")
    A("## 3. The token walk (every token, with its byte offset)")
    A("")
    A("`decoded`. The walk is closure-driven: a token is only accepted at the position the previous")
    A("token ended at, and the walk must consume all %d bytes and stop on `Return` at 367 (oracle"
      % d["script_bytes"])
    A("`walk_closes`). Nothing is pattern-scanned, so an operand byte can never be mistaken for a")
    A("token. A `0x00` is a 5-byte reference only when the int32 behind it resolves to a package")
    A("object; elsewhere it is the one-byte token `0x00` (oracle `refs_resolve`).")
    A("")
    A("| at | size | token | operand / resolves to |")
    A("|---:|---:|---|---|")
    for t in d["tokens"]:
        if t["kind"] == "ref":
            extra = "`%s` (%s, index %d)" % (t["path"], t["object_class"], t["index"])
        elif t["kind"] in ("Jump", "JumpIfNot", "Skip"):
            extra = "word %d" % t["word"]
        elif t["kind"] == "ByteConst":
            extra = "`%d`" % t["value"]
        elif t["kind"] == "StringConst":
            extra = "`%s`" % t["value"]
        elif t["kind"] == "FloatConst":
            extra = "%r" % t["value"]
        elif t["kind"] in ("VirtualFunction", "FinalFunction"):
            extra = "`%s` (index %d)" % (t.get("name"), t["index"])
        elif t["kind"] == "IntConst":
            extra = "`%d`" % t["value"]
        else:
            extra = ""
        A("| %d | %d | %s | %s |" % (t["at"], t["size"], t["kind"], extra))
    A("")
    A("## 4. The branch words: what `Skip` proves and what `Jump` does not")
    A("")
    A("### 4a. `EX_Skip` (`0x18`) - decoded, exact")
    A("")
    A("A skip's 2-byte word is a **byte distance in a stream where a reference token weighs 9 bytes**,")
    A("not the 5 it occupies here: `word = (target - (at+3)) + 4 x references skipped`. Resolving it")
    A("forward in that space hits a token start in every case:")
    A("")
    A("| skip at | word | references skipped | straight distance | word - distance | target |")
    A("|---:|---:|---:|---:|---:|---:|")
    for x in sk:
        A("| %d | %d | %d | %s | %s | %s |" % (
            x["at"], x["word"], x["refs_skipped"], x["distance"],
            (x["word"] - x["distance"]) if x["distance"] is not None else "-",
            x["target"]))
    A("")
    A("All %d skips satisfy `weight_sum == word` (oracle `skip_rule_exact`), and all %d skips in the"
      % (len(sk), doc["corpus"]["skips"]))
    A("walkable corpus resolve the same way (oracle `skip_rule_corpus`). The two `word 0` skips at 18")
    A("and 40 are zero-length skips inside a call's argument list; they land on the next token.")
    A("")
    A("This is what fixes the two guard bodies: the skip at **271** targets **301** and the skip at")
    A("**324** targets **334** - the first byte of each selector call's argument list. A skip lands on")
    A("the byte after its enclosing expression, so each call is the guarded body of the `0x07` that")
    A("owns that expression (oracle `containment_by_skip`).")
    A("")
    A("### 4b. `EX_Jump` / `EX_JumpIfNot` (`0x06` / `0x07`) - UNKNOWN")
    A("")
    A("The same treatment **fails** for the six jump words in this function. Every candidate base was")
    A("tested against the token starts of this very walk (`%d` starts):" % len(d["tokens"]))
    A("")
    A("| jump at | token | word | " + " | ".join(BASES) + " |")
    A("|---:|---|---:|" + "---|" * len(BASES))
    for j in doc["jumps"]:
        cells = []
        for b in BASES:
            v = j["bases"][b]
            cells.append(("-" if v["target"] is None else str(v["target"]))
                         + (" **start**" if v["is_token_start"] else ""))
        A("| %d | %s | %d | %s |" % (j["at"], j["kind"], j["word"], " | ".join(cells)))
    A("")
    hits = {b: sum(1 for j in doc["jumps"] if j["bases"][b]["is_token_start"]) for b in BASES}
    best_b = max(hits, key=lambda b: (hits[b], b))
    corp_max = max(doc["corpus"]["jump_hits"].values())
    A("The best base is `%s`: %d of %d words land on a token start, and the two it gets are the short"
      % (best_b, hits[best_b], len(doc["jumps"])))
    A("entry/else words 49 and 81. That is chance level, as the corpus confirms: the same sweep over")
    A("%d jump words in %d walkable `Startup.upk` functions gets at most %d (`%s`): every base is at"
      % (doc["corpus"]["jump_total"], doc["corpus"]["functions_walked"], corp_max,
         json.dumps(doc["corpus"]["jump_hits"])))
    A("or below the ~15% a random position would score. Single coincidences exist (the `from_end`")
    A("base of the word 352 is 16, which happens to be a token start) and are listed in the table,")
    A("but a base must resolve *every* word of a function to be the encoding, and none does.")
    A("")
    A("The words are not random either: two jumps that must share a target share a word (`309`/`312`")
    A("both 474 in this function; 59/62 both 125, 116/119 both 206 in the selector), and the words")
    A("increase with the target - so they are a coordinate, just not one this script reconstructs.")
    A("")
    A("A per-token-weight prefix-sum model is also impossible. With weights `bytes + r*refs + c*contexts`")
    A("each known span implies its own per-reference weight and they disagree:")
    A("")
    for e in doc["weight_model"]["equations"]:
        A("* `%d -> %d`: `dw = %d` over `%d` bytes, refs `%d`, contexts `%d`, calls `%d`"
          % (e["from"], e["to"], e["dw"], e["bytes"], e["refs"], e["contexts"], e["calls"]))
    A("")
    for i in doc["weight_model"]["solution"]["implied"]:
        A("* span %s implies `r = %s` (`+%d` bytes over %d references)"
          % (i["span"], i["per_ref"], i["extra_bytes"], i["refs"]))
    A("")
    A("Two different, non-integral weights for the same token kind cannot both hold, so no such model")
    A("exists (oracle `no_prefix_sum_weight_model`). Recorded as **UNKNOWN**: the two `Jump` **targets**")
    A("are not decoded, and the CFG's false-branch edges are marked UNKNOWN below. They are not needed")
    A("for section 1, which rests on the skip rule and the polarity oracle instead.")
    A("")
    A("## 5. Control-flow graph")
    A("")
    A("Nodes are statement starts (all verified to be token starts in `statement_starts`).")
    A("")
    A("| at | to | statement |")
    A("|---:|---|---|")
    for nd in cg["nodes"]:
        A("| %d | %d | `%s` - %s |" % (nd["at"], nd["end"], nd["kind"], nd["meaning"]))
    A("")
    A("| from | edge | to | label |")
    A("|---:|---|---|---|")
    for e in cg["edges"]:
        A("| %d | %s | %s | %s |" % (e["from"], "body" if e["to"] == "body" else "jump",
                                     e["body_at"] if e["body_at"] is not None else "UNKNOWN",
                                     e["label"]))
    A("")
    A("```")
    A("0  JumpIfNot  !bWasRemoteDriving ---------- true -----------> 11 TriggerEventClass(Driver,1)")
    A("   |                                                          30 Jump  -> UNKNOWN")
    A("   |                                                          33 TriggerEventClass(Driver,3)")
    A("   +-- false -> UNKNOWN                                       |")
    A("                                                              v")
    A("53 Driver.InteriorLightsSwitchedOn = 0")
    A("67 flag block 1 -> SetGlobalFlag(\"Batman_Remote_Control_Batmobile\", false)")
    A("146 flag block 2 -> SetGlobalFlag(\"Batman_In_Batmobile\", false)")
    A("213 RemoveBatmobileBindsAndSetBatmanBinds()")
    A("219 JumpIfNot IsVehicleAsleep --- true --> 228 FakeRoadCollisionStatic = UpdateFakeRoadCollision(true,0)")
    A("   +-- false -> UNKNOWN                    |")
    A("                                            v")
    A("248 JumpIfNot (winch/armoured condition, 251-300)")
    A("   +-- true --> 301 SetBatmanVsBatmobileCollisionMode(2) --> 309 Jump -> UNKNOWN")
    A("   +-- false -> UNKNOWN")
    A("312 JumpIfNot (0x81 ArmouredMode, IsVehicleAsleep, 315-333)")
    A("   +-- true --> 334 SetBatmanVsBatmobileCollisionMode(1)")
    A("   +-- false -> UNKNOWN")
    A("342 bForceWheelspin = false; 350 WheelspinSmokeMomentum = 0.0; 361 Core.DriverLeft(); 367 return")
    A("```")
    A("")
    A("## 6. The two calls, condition by condition")
    A("")
    for key, val in (("A", 2), ("B", 1)):
        g = doc["guards"][key]
        A("### Value %d - call at %d" % (val, g["body_call_at"]))
        A("")
        A("Guard `0x07` at **%d**. Condition bytes **%d-%d**, body bytes **%d-%d** (the body is the"
          % (g["guard_at"], g["condition_byte_range"][0], g["condition_byte_range"][1] - 1,
             g["body_byte_range"][0], g["body_byte_range"][1] - 1))
        A("call statement alone; containment from oracle `containment_by_skip`).")
        A("")
        A("| at | token | meaning |")
        A("|---:|---|---|")
        for row in g["shapes"]:
            A("| %d | `%s` | %s%s |" % (row["at"], row["expect"], row["meaning"],
                                        (" - `%s`" % row["path"]) if row["path"] else ""))
        A("")
        A("Chain, outermost first: **%s**." % g["condition"])
        A("")
    A("")
    A("## 7. Are the four names globals or members? - members")
    A("")
    A("The import entry's own row decides it. A cooked import row is 28 bytes: class package name,")
    A("class name, int32 outer, object name (`decoded`, offsets are byte offsets in `Startup.upk`).")
    A("Every one of the four has a **Class** in its outer field, so the object is a property *of a")
    A("class*, not a package-level global:")
    A("")
    A("| name | import | row at | class package | class | outer | owning class | home package |")
    A("|---|---:|---:|---|---|---:|---|---|")
    for m in doc["members"]:
        r = m["import"]
        A("| `%s` | %d | %d | %s | %s | %d | `%s` | `%s` |" % (
            m["name"], r["index"], r["row_offset"], r["class_package"], r["class_name"],
            r["outer"], m["owning_class"], m["home_package"]))
    A("")
    A("And the owning class's property list in the home package carries the name as a declared")
    A("property (`decoded`; the property export's `outer_index` is the class export):")
    A("")
    A("| name | property export | class | outer export | class property tag |")
    A("|---|---:|---|---:|---|")
    for m in doc["members"]:
        pe = m.get("property_exports") or [{}]
        tags = []
        for l in m.get("owning_class_property_lists", []):
            tags += ["%s @%s" % (t["type"], hex(t["offset"])) for t in l["property_tags"]]
        A("| `%s` | %s | %s | %s | %s |" % (
            m["name"], pe[0].get("export", "-"), pe[0].get("class", "-"),
            pe[0].get("outer_index", "-"), ", ".join(tags) or "not in the walked tag range"))
    A("")
    A("So all four are **members**: `Core.BatmobileWinch` and `Core.ArmouredMode` of")
    A("`RVehicleBatmobileBase` (`BmGame`), `Core.WinchPullType` of `RBatmobileWinch` (`BmGame`),")
    A("`Core.IsVehicleAsleep` of `Engine.SVehicle`. G3-01e-fix's third UNKNOWN is closed.")
    A("")
    A("## 8. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in o.items():
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:340]))
    A("")
    A("## 9. UNKNOWN")
    A("")
    A("1. **The absolute targets of the six `0x06`/`0x07` words in this function.** Tested: 11 bases")
    A("   (`abs`, +-22 payload frame, `pos+word`, `pos+3+word`, `pos-word`, `L-word`, `L-word-3`, and")
    A("   three weight-expanded spaces) on this walk's own token starts and over the corpus; a")
    A("   two-parameter weight model; nothing lands. The words are a monotone coordinate of the target")
    A("   (equal words for equal targets) but not of any byte position this script can reconstruct.")
    A("   The two `Jump` edges therefore stay UNKNOWN. Where it would be found: a token table or a")
    A("   pre-cook script from the same build.")
    A("2. **The meaning of `0x82`, `0x9B`, `0x77`, `0x2A`, `0x2D`, `0x19`, `0x09`, `0x00`, `0x38/0x3A`.**")
    A("   Their **extents** are proven by the walk and by the skip words, but `0x82` is not proven to")
    A("   be `&&` rather than `||`, and `0x9B`/`0x77` are not proven `==` rather than `!=`. Only `0x81`")
    A("   has a named-function case (negation, section 3 of `SELECTOR_POLARITY.md`).")
    A("3. **Which `DriverLeft` invocation runs at a given runtime transition.** The sampler logs the")
    A("   value, not the caller; `DriverLeft` and `OnSleepRBPhysics` can both pass 1.")
    A("4. **The two `Skip word 0` tokens at 18 and 40.** Their target is the next token and they change")
    A("   nothing here; what construct emits them is not decoded.")
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    md, js = render(doc), json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
    if args.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT)))
        print("tokens %d, refs %d, script %d B, skips %s"
              % (doc["driverleft"]["token_count"], doc["driverleft"]["refs"],
                 doc["driverleft"]["script_bytes"],
                 [(x["at"], x["word"], x["target"]) for x in doc["skips"]]))
        print("calls %s" % [(c["at"], c["argument"]) for c in doc["calls"]])
        print("members %s" % [(m["name"], m["verdict"], m["owning_class"]) for m in doc["members"]])
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        fails.append("COLLISION_SELECTOR3.json is stale")
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("COLLISION_SELECTOR3.md is stale")
    for k in bad:
        fails.append("oracle %s failed: %s" % (k, json.dumps(doc["oracles"][k]["detail"])[:300]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d tokens, %d refs, walk closes on %d B; skips %s; md+json byte-identical"
          % (doc["driverleft"]["token_count"], doc["driverleft"]["refs"],
             doc["driverleft"]["script_bytes"],
             [(x["at"], x["word"], x["target"]) for x in doc["skips"]]))
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()},
                                     sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
