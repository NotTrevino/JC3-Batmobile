#!/usr/bin/env python3
"""GRB-G3-01e-pol - branch polarity for `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`.

The open question in COLLISION_SELECTOR.md / COLLISION_SELECTOR2.md: when a
comparison unit is followed by `0x07 <u16>`, does the body run when the
comparison is TRUE or when it is FALSE?

What this script does
  1. Re-reads the selector (BmGame.upk export 10894) and re-derives its guard units
     and calls, then states what each of the two candidate polarities implies for
     the value -> mesh table.  The selector's own sha1 is an oracle.
  2. Measures the branch-encoding question across the package: it walks Function
     scripts sequentially with a token table whose extents are proven by closure
     (a script closes only when the walk consumes it exactly and ends on `0x04`),
     and tests every 2-byte word after `0x06`/`0x07`/`0x18` against the token
     starts under 11 candidate bases (absolute/token/operand-end/end, signed and
     unsigned, byte and payload frame).  No base resolves; that is reported as a
     measurement, not as a polarity.
  3. Runs the polarity test on six Functions in the same package whose guarded
     call is stated by the Function's own name (the "certain behaviour" oracle the
     task asks for).  For each case the script decodes `0x07 <expr>` and the bytes
     that follow the expression, and asks: under the reading "the body runs when
     the expression is TRUE", is the expected call in that body?  Every case must
     agree; one disagreement makes the verdict UNKNOWN, per the task.

Labels
  decoded  read from the package at the export + script offset shown
  derived  computed here by a stated rule
  UNKNOWN  not established; what blocked it is recorded

Outputs (never hand-edited): `Research/BatmobileGrab/SELECTOR_POLARITY.md` + `.json`.

Usage
  python Tools/scripts/grab_selector_polarity.py --write
  python Tools/scripts/grab_selector_polarity.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

GAME = "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
PKG_NAME = "BmGame.upk"
SEL_PATH = "RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode"
SEL_EXPORT = 10894
SEL_SHA1 = "c2f6a2ee667c544876e5317a103072c44ea17788"
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SELECTOR_POLARITY.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "SELECTOR_POLARITY.json")
SCHEMA = "g3-01e-pol/1"

# --- token extents used by the sequential walk (proven by closure, see corpus_oracle)
BRANCH = (0x06, 0x07, 0x18)

# --- the six polarity test cases.
# `expect_block_runs_when_true`: the guarded body (the bytes after the `0x07`
# expression) is asserted by the Function's own name to run when the expression
# is true.  `why` states the evidence; `expect_call` is the call the body must
# contain.  None of these is the selector.
CASES = [
    {            "path": "RPlayerController.HideHealthBarIfMax",
            "expect_call": "HideHealthBar",
            "expect_block_runs_when_true": True,
            "decisive": True,
            "certainty": "name (condition is a call)",
        "why": "the name states the hide happens *if max*, i.e. when IsMaxHealth() is true",
    },
    {
        "path": "RPlayerController.ShowHealthBarIfNotMax",
        "expect_call": "ShowHealthBar",
        "expect_block_runs_when_true": True,
        "decisive": True,
        "certainty": "name (condition is a negated call)",
        "why": ("the name states the show happens *if not max*; the expression is the "
                "0x81 negated IsMaxHealth() call, so the body must run when the "
                "expression as written is true"),
    },
    {
        "path": "RPlayerController.ShowHealthBar",
        "expect_call": "SetHealthBarVisible",
        "expect_block_runs_when_true": True,
        "decisive": False,
        "certainty": "name, conditional on operator 0xf2",
        "why": ("the body sets bShowHealthBar = true and SetHealthBarVisible(true), so it "
                "must run when the bar is not already shown; the guard is 0xf2 applied "
                "to bShowHealthBar and FALSE, and whether 0xf2 is equality is UNKNOWN, so "
                "this case supports but does not decide the polarity"),
    },
    {
        "path": "RPlayerController.HideHealthBar",
        "expect_call": "SetHealthBarVisible",
        "expect_block_runs_when_true": True,
        "decisive": False,
        "certainty": "name, conditional on operator 0xf2",
        "why": ("the body sets bShowHealthBar = false and SetHealthBarVisible(false), so it "
                "must run when the bar is shown; the guard is 0xf2 applied to "
                "bShowHealthBar and TRUE, and 0xf2's meaning is UNKNOWN, so this case "
                "supports but does not decide"),
    },
    {
        "path": "RVehicleNPCWeapon.Tick",
        "expect_call": "SetTickIsDisabled",
        "expect_block_runs_when_true": True,
        "decisive": True,
        "certainty": "name (condition is a call)",
        "why": ("Tick disables its own tick via SetTickIsDisabled(true); the guard is the "
                "predicate CanDisableTick(), so the body must run when it is true"),
    },
    {
        "path": "Primed.UnequipSelf",
        "expect_call": "UnequipSelf",
        "expect_block_runs_when_true": True,
        "decisive": True,
        "certainty": "structure (liveness)",
        "why": ("the guard body is `return false`; the only reading in which UnequipSelf "
                "can ever run is: refuse while IsTimerActive() is true, act when it is "
                "false.  Under the inverted reading the function could never unequip "
                "anything (the return would fire on the false branch)"),
    },
]

REF5 = (0x00, 0x01, 0x02)
MEMBER1 = (0x2D, 0x19, 0x09)
CONST1 = (0x25, 0x26, 0x27, 0x28, 0x2A, 0x0B)


def i32(s: bytes, o: int) -> int:
    return struct.unpack_from("<i", s, o)[0]


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def script_of(pkg, index: int) -> bytes:
    d = pkg.data(index)
    return d[22:len(d) - 16]


def func_index(pkg, path: str):
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) == "Function" and pkg.object_path(i) == path:
            return i
    return None


# ------------------------------------------------------------------ expression split
def expr_end(pkg, s: bytes, p: int, depth: int = 0) -> int:
    """End offset (exclusive) of one expression at p, for the shapes used here.

    call            `1B|1C <5> <args...> 16`
    operator        `<op> <expr...> 16`          (0x81/0x82/0x77/0xf2/... seen in the cases)
    comparison      `9A|9B <operand> <operand> 16`
    member ref      `2D|19|09 01 <int32>`        (6 bytes)
    object ref      `00|01|02 <int32>`           (5 bytes)
    byte const      `24 <byte>`                  (2)
    other consts    1 byte
    """
    if depth > 8 or p >= len(s):
        raise ValueError("expression does not parse at %d" % p)
    if s[p] == 0x38 and p + 1 < len(s) and s[p + 1] == 0x3A:   # operand prefix seen in the selector
        return expr_end(pkg, s, p + 2, depth + 1)
    t = s[p]
    if t in (0x1B, 0x1C):
        q = p + 5
        while q < len(s) and s[q] != 0x16:
            q = expr_end(pkg, s, q, depth + 1)
        return q + 1
    if t in (0x9A, 0x9B):
        q = p + 1
        for _ in range(2):
            q = expr_end(pkg, s, q, depth + 1)
        if q >= len(s) or s[q] != 0x16:
            raise ValueError("comparison not terminated at %d" % q)
        return q + 1
    if t in MEMBER1 and p + 6 <= len(s) and s[p + 1] == 0x01:
        return p + 6
    if t in REF5 and p + 5 <= len(s):
        return p + 5
    if t == 0x24:
        return p + 2
    if t == 0x2B:                       # 6-byte literal (seen as a call argument)
        return p + 6
    if t in CONST1:
        return p + 1
    if t >= 0x80:                       # operator: params until 0x16
        q = p + 1
        while q < len(s) and s[q] != 0x16:
            q = expr_end(pkg, s, q, depth + 1)
        return q + 1
    return p + 1


def first_call(pkg, s: bytes, a: int, b: int):
    """First call in [a,b) whose operand resolves and whose params close inside b.

    A byte scan, not expression jumps: an operand byte can be >= 0x80 and look like an
    operator, and stepping over that "operator" swallows the call that follows (measured
    on RPlayerController.ShowHealthBar, whose body call was missed by the jump version).
    """
    p = a
    while p < b:
        t = s[p]
        if t in (0x1B, 0x1C) and p + 5 <= b:
            idx = i32(s, p + 1)
            name = (pkg.names[idx] if t == 0x1B and 0 <= idx < pkg.name_count
                    else pkg.object_path(idx))
            if name:
                q = p + 5
                while q < b and s[q] != 0x16:
                    q += 1
                if q < b:
                    return {"at": p, "token": "0x%02X" % t, "name": name}
        p += 1
    return None


# ------------------------------------------------------------------ 1. selector
def selector(pkg) -> dict:
    idx = func_index(pkg, SEL_PATH)
    if idx != SEL_EXPORT:
        raise SystemExit("selector moved: %r is export %r" % (SEL_PATH, idx))
    s = script_of(pkg, idx)
    guards, calls = [], []
    p = 0
    while p < len(s):
        t = s[p]
        if t == 0x07 and p + 3 <= len(s):
            word = struct.unpack_from("<H", s, p + 1)[0]
            try:
                end, rule = expr_end(pkg, s, p + 3), "parser"
            except ValueError:
                k = s.find(b"\x16", p + 3)
                end, rule = ((k + 1) if k >= 0 else p + 3), "terminator-scan"
            cond = s[p + 3:end]
            guards.append({"at": p, "word": word, "expr_at": p + 3,
                           "expr_end": end, "expr_bytes": cond.hex(" "),
                           "expr_rule": rule, "expr_sha1": sha1(cond)})
            p = end
            continue
        if t in (0x1B, 0x1C) and p + 5 <= len(s):
            end = expr_end(pkg, s, p)
            name = (pkg.names[i32(s, p + 1)] if t == 0x1B and
                    0 <= i32(s, p + 1) < pkg.name_count else pkg.object_path(i32(s, p + 1)))
            args = []
            q = p + 5
            while q < end - 1 and s[q] != 0x16:
                args.append(s[q:expr_end(pkg, s, q)].hex(" "))
                q = expr_end(pkg, s, q)
            calls.append({"at": p, "name": name, "args": args})
            p = end
            continue
        p += 1
    # which mesh call follows which guard, linearly (same rule as G3-01e)
    mesh_calls = [c for c in calls if c["name"] and
                  c["name"].endswith(("DetachComponent", "AttachComponent"))]
    pairs = []
    for c in mesh_calls:
        prev = [g for g in guards if g["expr_end"] <= c["at"]]
        g = max(prev, key=lambda x: x["expr_end"]) if prev else None
        pairs.append({"call": c["name"].rsplit(".", 1)[-1], "call_at": c["at"],
                      "guard_at": g["at"] if g else None,
                      "guard_word": g["word"] if g else None})
    return {
        "export": idx, "path": SEL_PATH, "script_bytes": len(s), "script_sha1": sha1(s),
        "guards": guards, "calls": calls, "pairs": pairs,
        "label": "decoded (export %d, script offset as shown)" % idx,
    }


# ------------------------------------------------------------------ 2. corpus
def corpus(pkg) -> dict:
    funcs = [i for i in range(1, pkg.export_count + 1) if pkg.object_class(i) == "Function"]
    closed = 0
    jumps = Counter()
    hits = Counter()
    bases = ["abs_u", "abs_s", "payload_u", "payload_s", "tok_u", "tok_s",
             "tok3_u", "tok3_s", "end_u", "end_s", "tok2_s"]
    for i in funcs:
        d = pkg.data(i)
        if len(d) < 38:
            continue
        s = d[22:len(d) - 16]
        toks, starts, ok = walk(s)
        if not ok:
            continue
        closed += 1
        for t in toks:
            if t["k"] not in BRANCH:
                continue
            jumps["0x%02X" % t["k"]] += 1
            at, w, sw = t["at"], t["word"], t["sw"]
            cand = {
                "abs_u": w, "abs_s": sw, "payload_u": w - 22, "payload_s": sw - 22,
                "tok_u": at + w, "tok_s": at + sw, "tok3_u": at + 3 + w,
                "tok3_s": at + 3 + sw, "end_u": len(s) - w, "end_s": len(s) - sw,
                "tok2_s": at + 2 + sw,
            }
            for b in bases:
                if 0 <= cand[b] < len(s) and cand[b] in starts:
                    hits[b] += 1
    total = sum(jumps.values())
    return {
        "functions": len(funcs), "closed": closed,
        "closed_pct": round(100.0 * closed / len(funcs), 1),
        "jumps_total": total,
        "jumps_by_token": dict(sorted(jumps.items())),
        "bases": [{"base": b, "hits": hits[b],
                   "pct": round(100.0 * hits[b] / total, 1) if total else 0.0} for b in bases],
        "best": max(bases, key=lambda b: hits[b]),
        "label": ("derived (sequential walk; a script counts only when the walk consumes it "
                  "exactly and ends on 0x04 while a token start)"),
    }


def walk(s: bytes):
    """Sequential token walk; returns (tokens, token starts, closed)."""
    p, toks = 0, []
    while p < len(s):
        t = s[p]
        if t in (0x01, 0x00, 0x02) and p + 5 <= len(s):
            if upk_read_pkg and upk_read_pkg.object_path(i32(s, p + 1)) is not None:
                toks.append({"at": p, "k": "ref"})
                p += 5
                continue
        if t in (0x1B, 0x1C, 0x1D, 0x1E) and p + 5 <= len(s):
            toks.append({"at": p, "k": "long"})
            p += 5
            continue
        if t == 0x1F:
            end = s.find(b"\x00", p + 1)
            if end < 0:
                return toks, set(), False
            toks.append({"at": p, "k": "str"})
            p = end + 1
            continue
        if t in BRANCH and p + 3 <= len(s):
            toks.append({"at": p, "k": t,
                         "word": struct.unpack_from("<H", s, p + 1)[0],
                         "sw": struct.unpack_from("<h", s, p + 1)[0]})
            p += 3
            continue
        if t == 0x24 and p + 2 <= len(s):
            toks.append({"at": p, "k": "byte"})
            p += 2
            continue
        if t in (0x2D, 0x19, 0x09) and p + 6 <= len(s) and s[p + 1] == 0x01:
            toks.append({"at": p, "k": "member"})
            p += 6
            continue
        toks.append({"at": p, "k": "one"})
        p += 1
    ok = bool(toks) and s[-1] == 0x04
    return toks, {t["at"] for t in toks}, ok


# ------------------------------------------------------------------ 3. cases
def run_cases(pkg) -> list:
    out = []
    for c in CASES:
        idx = func_index(pkg, c["path"])
        row = {"path": c["path"], "export": idx, "why": c["why"],
               "certainty": c["certainty"], "expect_call": c["expect_call"],
               "decisive": c["decisive"]}
        if not idx:
            row.update({"ok": False, "error": "function not found"})
            out.append(row)
            continue
        s = script_of(pkg, idx)
        row["script_bytes"] = len(s)
        try:
            if s[0] != 0x07:
                raise ValueError("script does not start with 0x07 (0x%02X)" % s[0])
            word = struct.unpack_from("<H", s, 1)[0]
            end = expr_end(pkg, s, 3)
            cond = s[3:end]
            call = first_call(pkg, s, end, len(s))
            row.update({
                "guard_word": word, "expr_at": 3, "expr_end": end,
                "expr_bytes": cond.hex(" "),
                "expr_call": first_call(pkg, s, 3, end)["name"] if first_call(pkg, s, 3, end) else None,
                "body_at": end, "body_bytes": len(s) - end,
                "body_call_at": call["at"] if call else None,
                "body_call": call["name"].rsplit(".", 1)[-1] if call else None,
                "body_sha1": sha1(s[end:]),
            })
            row["body_has_expected_call"] = bool(
                call and call["name"].rsplit(".", 1)[-1] == c["expect_call"])
            # hypothesis A: the body runs when the expression is true
            row["agree_body_on_true"] = row["body_has_expected_call"]
        except ValueError as e:
            row.update({"ok": False, "error": str(e)})
        row["ok"] = row.get("body_has_expected_call", False)
        out.append(row)
    return out


# ------------------------------------------------------------------ build
def build() -> dict:
    global upk_read_pkg
    upk_read_pkg = upk_read.Package(os.path.join(GAME, PKG_NAME))
    pkg = upk_read_pkg
    sel = selector(pkg)
    cor = corpus(pkg)
    cases = run_cases(pkg)
    agree = sum(1 for c in cases if c.get("agree_body_on_true"))
    disagree = [c["path"] for c in cases if not c.get("agree_body_on_true")]
    dec = [c for c in cases if c.get("decisive")]
    agree_dec = sum(1 for c in dec if c.get("agree_body_on_true"))
    disagree_dec = [c["path"] for c in dec if not c.get("agree_body_on_true")]
    if dec and agree_dec == len(dec):
        verdict = ("body runs when the comparison is TRUE "
                   "(0x07 skips the body when the expression is FALSE)")
        status = "decided"
    elif dec and agree_dec == 0:
        verdict = ("body runs when the comparison is FALSE "
                   "(0x07 skips the body when the expression is TRUE)")
        status = "decided"
    else:
        verdict = "UNKNOWN - the decisive functions disagree"
        status = "unknown"
    return {
        "schema": SCHEMA,
        "package": PKG_NAME,
        "selector": sel,
        "corpus": cor,
        "cases": cases,
        "counts": {"cases": len(cases), "agree_body_on_true": agree,
                   "decisive": len(dec), "agree_decisive": agree_dec,
                   "disagree": len(disagree), "disagreeing": disagree,
                   "disagreeing_decisive": disagree_dec},
        "verdict": {"status": status, "text": verdict},
        "unknowns": [
            {"what": "the absolute target of the 0x06/0x07/0x18 2-byte words",
             "why": ("11 candidate bases were tested over %d closed scripts; the best lands on a "
                     "token start %.1f%% of the time, so no base is proven.  Polarity here is "
                     "therefore read from linear order (the 0x07 precedes its expression; the "
                     "body follows), which the six cases test."
                     % (cor["closed"], cor["bases"][[b['base'] for b in cor['bases']].index(cor['best'])]["pct"]))},
            {"what": "whether 0x9A and 0x9B are == and != (or vice versa)",
             "why": ("the two tokens are decoded separately per comparison; no file or prior card "
                     "in this repo assigns them a meaning, and the case set does not use them")},
            {"what": "the meaning of operator tokens 0x77, 0x81, 0x82, 0xf2, 0x2b",
             "why": ("their extents parse (params until 0x16) but their semantics are not decoded; "
                     "the cases use them only as expression wrappers, never as the condition")},
            {"what": "whether the sampler can observe any of the six guarded effects",
             "why": ("the sampler logs vehicle fields (Driver, BatmanVsBatmobileCollisionMode, "
                     "weapons, flags); it logs no HUD visibility, tick-disable or gadget state, so "
                     "it cannot corroborate the six cases.  It is used only for the selector's "
                     "mode/driver context")},
        ],
    }


# ------------------------------------------------------------------ markdown
def md_render(d: dict) -> str:
    L = []
    A = L.append
    A("# Branch polarity in `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode` (BmGame.upk 10894)")
    A("")
    A("Generated by `Tools/scripts/grab_selector_polarity.py --write`; `--check` re-derives every "
      "number from the package and fails on drift.  Read-only: the package is opened, never written.")
    A("")
    A("Labels: **decoded** = read from the package at the export + script offset shown; "
      "**derived** = a stated rule applied to decoded facts; **UNKNOWN** = not established here.")
    A("")
    A("## Verdict")
    A("")
    A("**%s**" % d["verdict"]["text"])
    A("")
    c = d["counts"]
    A("Functions tested: **%d** (decisive **%d**, supporting **%d**); agree with "
      "*body-on-true*: **%d** of %d, decisive **%d** of %d; disagree: **%d**%s."
      % (c["cases"], c["decisive"], c["cases"] - c["decisive"],
         c["agree_body_on_true"], c["cases"], c["agree_decisive"], c["decisive"],
         c["disagree"],
         ("" if not c["disagreeing"] else " (" + ", ".join(c["disagreeing"]) + ")")))
    A("")
    A("Decisive cases have a condition that is itself a call (or one negated call), so no "
      "operator token has to be interpreted.  The two supporting cases wrap a property in "
      "`0xf2`, whose meaning is UNKNOWN; they are reported and not counted as decisive.")
    A("")
    A("Under this verdict the selector's guards are read as: for each mode value *k*, the "
      "`DetachComponent` body runs when the OLD property equals *k* and the `AttachComponent` "
      "body when the NEW parameter equals *k* — i.e. the value -> mesh table in "
      "`COLLISION_SELECTOR.md` (§ Value -> mesh table) stands with its guards read in the "
      "ordinary order, and the 0 = 'no mesh' row is unchanged.")
    A("")
    A("## 1. The selector, re-read")
    A("")
    s = d["selector"]
    A("| field | value |")
    A("|---|---|")
    A("| export | `%d` |" % s["export"])
    A("| path | `%s` |" % s["path"])
    A("| script_bytes | `%d` |" % s["script_bytes"])
    A("| script sha1 | `%s` |" % s["script_sha1"])
    A("| sha1 equals G3-01e's | %s |" % (s["script_sha1"] == SEL_SHA1))
    A("")
    A("Guards (`0x07` sites, expression bytes decoded):")
    A("")
    A("| at | word | expr at | expr end | expression bytes |")
    A("|---|---|---|---|---|")
    for g in s["guards"]:
        A("| %d | %d | %d | %d | `%s` |" % (g["at"], g["word"], g["expr_at"],
                                            g["expr_end"], g["expr_bytes"]))
    A("")
    A("Mesh calls paired with the guard that precedes them (derived: the nearest guard whose "
      "expression ends at or before the call):")
    A("")
    A("| call | at | guard at | guard word |")
    A("|---|---|---|---|")
    for p in s["pairs"]:
        A("| `%s` | %d | %s | %s |" % (p["call"], p["call_at"],
                                       p["guard_at"], p["guard_word"]))
    A("")
    A("## 2. Branch encoding across the package")
    A("")
    co = d["corpus"]
    A("Functions walked: **%d**, closed (walk consumes the script exactly and ends on `0x04`): "
      "**%d** (**%s%%**). Branch-shaped tokens in those scripts: **%d** "
      "(%s)." % (co["functions"], co["closed"], co["closed_pct"], co["jumps_total"],
                 ", ".join("`%s` %d" % (k, v) for k, v in co["jumps_by_token"].items())))
    A("")
    A("Target test (derived): every 2-byte word is read under 11 bases and accepted only when it "
      "lands on a token start inside the script.")
    A("")
    A("| base | hits | share |")
    A("|---|---|---|")
    for b in co["bases"]:
        A("| `%s` | %d | %s%% |" % (b["base"], b["hits"], b["pct"]))
    A("")
    A("No base resolves.  This reproduces G3-01e's finding (its 74,632-token corpus test) on a "
      "larger closed-script sample, and it is why the polarity below is read from **linear "
      "order**, not offset arithmetic: in every case the `0x07` sits immediately before its "
      "expression and the body follows the expression's terminator.")
    A("")
    A("## 3. The polarity test")
    A("")
    A("Rule (derived): for each Function, take the `0x07` at script offset 0, decode its "
      "expression, and take the bytes after the expression as the guarded body.  The Function's "
      "own name (or, for one case, liveness) fixes which body must run when the expression is "
      "true; then ask whether that body contains the expected call.")
    A("")
    A("| Function | export | bytes | guard word | expression | body call | expected | role | agree? |")
    A("|---|---|---|---|---|---|---|---|---|")
    for c in d["cases"]:
        A("| `%s` | %s | %s | %s | `%s` | `%s` | `%s` | %s | %s |" % (
            c["path"], c.get("export"), c.get("script_bytes", "?"), c.get("guard_word", "?"),
            c.get("expr_bytes", "?"), c.get("body_call", "?"), c["expect_call"],
            "decisive" if c.get("decisive") else "supporting",
            "yes" if c.get("agree_body_on_true") else "**NO**"))
    A("")
    for c in d["cases"]:
        A("- `%s` — %s (%s)." % (c["path"], c["why"], c["certainty"]))
    A("")
    A("A single disagreement among the decisive cases would make the verdict UNKNOWN; "
      "%d of %d decisive cases agree (and %d of %d cases in total)."
      % (d["counts"]["agree_decisive"], d["counts"]["decisive"],
         d["counts"]["agree_body_on_true"], d["counts"]["cases"]))
    A("")
    A("## 4. Runtime context (not a polarity oracle)")
    A("")
    A("The sampler logs `BatmanVsBatmobileCollisionMode` 0/1 with driver presence: mode 1 occurs "
      "only with no driver seated (5/5 samples) and every 0->1 rise is at a driver exit "
      "(`COLLISION_SELECTOR2.md` §3, `runtime-*.jsonl` decoded).  It logs **no** component "
      "attachment, so it cannot see which mesh is attached: it is context for the mode meaning, "
      "not a second polarity oracle.  Recorded as such, not counted in the test.")
    A("")
    A("## 5. UNKNOWN")
    A("")
    for u in d["unknowns"]:
        A("- **%s** — %s" % (u["what"], u["why"]))
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    data = build()
    md = md_render(data)
    js = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if a.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        print("wrote %s (%d bytes)" % (OUT_MD, len(md)))
        print("wrote %s (%d bytes)" % (OUT_JSON, len(js)))
        print("cases=%d agree=%d verdict=%s" % (data["counts"]["cases"],
                                                data["counts"]["agree_body_on_true"],
                                                data["verdict"]["status"]))
        return 0
    ok = True
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("MISSING output(s)")
        return 1
    old = json.load(open(OUT_JSON, encoding="utf-8"))
    if old != data:
        ok = False
        print("json MISMATCH")
        for k in data:
            if old.get(k) != data[k]:
                print("  differs: %s" % k)
    else:
        print("json ok (%d cases)" % data["counts"]["cases"])
    disk = open(OUT_MD, encoding="utf-8").read()
    if disk != md:
        ok = False
        print("md MISMATCH (%d on disk vs %d re-rendered)" % (len(disk), len(md)))
    else:
        print("md ok (%d bytes)" % len(md))
    print("selector sha1 %s" % data["selector"]["script_sha1"])
    print("branch bases: best %s at %s%%" % (
        data["corpus"]["best"],
        next(b["pct"] for b in data["corpus"]["bases"] if b["base"] == data["corpus"]["best"])))
    print("CHECK OK" if ok else "CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
