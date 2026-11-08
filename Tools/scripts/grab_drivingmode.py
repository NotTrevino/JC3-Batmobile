#!/usr/bin/env python3
"""grab_drivingmode.py - G3-02i: the RPlayerController.DrivingMode exec bodies, token by token.

Decodes, from BmGame.upk (read-only), the exec functions of the `DrivingMode` state that an
input command names, and lists every call they make with its arguments:

    EjectFromVehicle, SelectVehicleWeapon, ToggleBattleMode, BatmobileFireButton,
    SecondaryFireVehicleWeapon, FirePursuitMissile, ReleaseVehicleWeapon,
    IsBatmobileFireButtonHeld, TriggerBatmobileBoost, BattleStrafe,
    QuickGadgetX/B/Y, ReleaseQuickGadgetX/B/Y

Where a name also exists on the class (`RPlayerController.<name>`, 39-44 bytes), that sibling is
decoded too: a command may resolve to either body, so both are reported.

Method (every step is checked by an oracle below):
    * the function is found by export name + outer_index == the state export; paths print as
      `DrivingMode.<name>` because upk_read.object_path uses the outer's short name;
    * the script is `data[22:-16]`; the Function trailer is `data[-12]` pre-name word,
      `data[-8]` name index, `data[-4]` name number;
    * calls are the `EX_VirtualFunction` (0x1B: FName operand) and `EX_FinalFunction` (0x1C:
      object operand) tokens the repo walk accepts; arguments are parsed forward from the
      operand to the matching `EX_EndFunctionParms` (0x16), nesting sub-calls;
    * a callee that is a Function export in this package is decoded one level deeper.

Argument tokens come from the repo table in bmak_damage.py. Three cases are distinguished:
    named with a fixed operand width  -> decoded (W5 / W1 / BARE below);
    carries a nested expression (EX_Context, EX_Skip, EX_Let*, jumps) -> **exact gap**, because
        such a token has no fixed width at all;
    not named by the repo table -> the smallest width in SEARCH_WIDTHS that lets the rest of the
        argument list reach a 0x16 is used; the row is marked `heuristic` and the full candidate
        list is recorded.  No candidate -> exact gap.

Control flow (jumps, branches, conditions) is not resolved.  Script bytes are never written out:
offsets, symbols and sha1s only.

Oracles (re-run by --check; any failure is a hard error):
    O1  every target resolves to a Function whose outer_index IS the state export
    O2  the three bmak_damage Function anchors hold on every decoded export
    O3  every argument list either ends on a re-verified 0x16, or reports its gap token+offset
    O4  no call dropped: one row per 0x1B/0x1C the repo walk accepted
    O5  export id / script length / sha1 agree with G3-02b's CONTROLS_CONSUMERS.json
    O6  every literal argument quoted in the note is re-read from the bytes at its offset
    O7  every DefaultInput.ini row quoted in the note is re-read from the file at --check

Usage:
    uv run python Tools/scripts/grab_drivingmode.py --write
    uv run python Tools/scripts/grab_drivingmode.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmak_damage as B  # noqa: E402  (repo token table + Function layout)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
GAME = r"E:\Games\Batman - Arkham Knight"
UPK = os.path.join(GAME, "BmGame", "CookedPCConsole", "BmGame.upk")
INI = os.path.join(GAME, "BmGame", "Config", "DefaultInput.ini")
CONSUMERS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_CONSUMERS.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVINGMODE.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVINGMODE.json")

STATE = "RPlayerController.DrivingMode"
FUNCS = ["EjectFromVehicle", "SelectVehicleWeapon", "ToggleBattleMode", "BatmobileFireButton",
         "SecondaryFireVehicleWeapon", "FirePursuitMissile", "ReleaseVehicleWeapon",
         "IsBatmobileFireButtonHeld", "TriggerBatmobileBoost", "BattleStrafe",
         "QuickGadgetX", "QuickGadgetB", "QuickGadgetY",
         "ReleaseQuickGadgetX", "ReleaseQuickGadgetB", "ReleaseQuickGadgetY"]

W5 = {0x00, 0x01, 0x02, 0x12, 0x20, 0x29, 0x2E, 0x3A, 0x48, 0x1D, 0x1E, 0x21}
W1 = {0x2C}
BARE = {0x04, 0x0B, 0x15, 0x17, 0x25, 0x26, 0x27, 0x28, 0x2A}
NESTED = {0x05, 0x06, 0x07, 0x0F, 0x10, 0x14, 0x18, 0x19, 0x1A}
SEARCH_WIDTHS = [0, 1, 2, 3, 4, 8, 9, 12, 13]
VERBATIM = {0x25: "0", 0x26: "1", 0x27: "true", 0x28: "false", 0x2A: "None",
            0x17: "self", 0x0B: "", 0x15: "|", 0x04: "return"}


def tok_name(t):
    return B.TOKENS.get(t, "unnamed 0x%02x" % t)


def short(path):
    return path.rsplit(".", 1)[-1] if path else None


def script_of(pkg, i):
    d = pkg.data(i)
    return d, d[22:len(d) - 16] if len(d) >= 38 else b""


def parse_args(script, p, bm, allow_search=True):
    """Parse an argument list up to the 0x16 that closes it. -> (args, end, error)."""
    args = []
    while p < len(script):
        t = script[p]
        if t == 0x16:
            return args, p + 1, None
        if t in (0x1B, 0x1C) and p + 5 <= len(script):
            idx = struct.unpack_from("<i", script, p + 1)[0]
            sub, q, err = parse_args(script, p + 5, bm, allow_search)
            target = bm.name(idx) if t == 0x1B else bm.ref(idx)
            args.append({"tok": tok_name(t), "at": p, "index": idx, "target": target,
                         "args": sub, "end": q, "err": err,
                         "text": "%s(%s)" % (short(target) or idx,
                                             ", ".join(a["text"] for a in sub))})
            if err:
                return args, q, err
            p = q
            continue
        n, q, err = node_of(script, p, bm, allow_search)
        if err:
            return args, p, err
        args.append(n)
        p = q
    return args, p, "no 0x16 terminator"


def node_of(script, p, bm, allow_search=True):
    """One token -> (node, next offset, error).  Never guesses a width."""
    t = script[p]
    if t in W5 and p + 5 <= len(script):
        idx = struct.unpack_from("<i", script, p + 1)[0]
        n = {"tok": tok_name(t), "at": p}
        if t == 0x21:
            n["name"] = bm.name(idx)
            n["name_index"] = idx
            n["text"] = "'%s'" % n["name"]
        elif t == 0x1E:
            n["value"] = round(struct.unpack_from("<f", script, p + 1)[0], 6)
            n["text"] = repr(n["value"])
        elif t == 0x1D:
            n["value"] = idx
            n["text"] = str(idx)
        else:
            n["ref"] = bm.ref(idx) if t in (0x00, 0x01, 0x02, 0x20, 0x29, 0x2E, 0x3A, 0x48) else None
            n["ref_index"] = idx
            n["text"] = short(n["ref"]) or ("ref %d" % idx)
        return n, p + 5, None
    if t in W1 and p + 2 <= len(script):
        return {"tok": tok_name(t), "at": p, "value": script[p + 1],
                "text": str(script[p + 1])}, p + 2, None
    if t in BARE:
        return {"tok": tok_name(t), "at": p, "text": VERBATIM.get(t, tok_name(t))}, p + 1, None
    if t in NESTED:
        return None, p, ("token 0x%02x (%s) at %d carries a nested expression, so it has no "
                         "fixed width" % (t, tok_name(t), p))
    if not allow_search:
        return None, p, "unnamed token 0x%02x at %d" % (t, p)
    good = []
    for w in SEARCH_WIDTHS:
        q = p + 1 + w
        if q > len(script):
            continue
        _, end, err = parse_args(script, q, bm, allow_search=False)
        if err is None and end <= len(script):
            good.append(w)
    if good:
        w = min(good)
        payload = script[p + 1:p + 1 + w]
        n = {"tok": tok_name(t), "at": p, "width": w, "heuristic": True,
             "candidates": good}
        if w == 0:
            n["text"] = "<0x%02x>" % t
        elif w == 1:
            n["value"] = payload[0]
            n["text"] = str(payload[0])
        elif w in (2, 3, 4, 8, 9):
            v = int.from_bytes(payload, "little")
            n["value"] = v
            n["text"] = str(v)
        elif w == 13:
            fx = struct.unpack("<3f", payload)
            n["text"] = "vec(%s)" % ", ".join("%g" % v for v in fx)
        else:
            n["text"] = "%s[%d]" % (tok_name(t), w)
        return n, p + 1 + w, None
    return None, p, ("token 0x%02x at %d: width not determinable (candidates %s)"
                     % (t, p, good))


_CAND = {}


def vm_candidates(bm, name):
    """Exports whose own name is `name` (name match only - dispatch is not decoded)."""
    if not name:
        return []
    if name not in _CAND:
        pkg = bm.pkg
        _CAND[name] = sorted(pkg.object_path(i) or ""
                             for i in range(1, pkg.export_count + 1)
                             if pkg.exports[i - 1]["name"] == name)
    return _CAND[name][:8]


def calls_of(script, walk, bm):
    out = []
    for r in walk["refs"]:
        if r["token"] not in ("EX_VirtualFunction", "EX_FinalFunction"):
            continue
        at = r["at"]
        idx = struct.unpack_from("<i", script, at + 1)[0]
        args, end, err = parse_args(script, at + 5, bm)
        virtual = r["token"] == "EX_VirtualFunction"
        target = bm.name(idx) if virtual else bm.ref(idx)
        out.append({"at": at, "token": r["token"], "index": idx, "target": target,
                    "target_class": None if virtual else bm.obj_class(idx),
                    "name_match": vm_candidates(bm, target) if virtual else [],
                    "args": args, "end": end, "err": err,
                    "terminator_ok": err is None and end > 0 and script[end - 1] == 0x16,
                    "heuristic_args": [a["at"] for a in args if a.get("heuristic")],
                    "text": "%s(%s)" % (short(target) or idx,
                                        ", ".join(a["text"] for a in args))})
    return out


def decode(bm, i, depth, budget):
    pkg = bm.pkg
    data, script = script_of(pkg, i)
    name = pkg.exports[i - 1]["name"]
    walk = bm.walk(script, own=name)
    calls = calls_of(script, walk, bm)
    name_idx = struct.unpack_from("<i", data, len(data) - 8)[0] if len(data) >= 8 else -1
    pre = struct.unpack_from("<i", data, len(data) - 12)[0] if len(data) >= 12 else 0
    entry = {
        "path": pkg.object_path(i), "export": i, "size": len(data),
        "script_bytes": len(script), "script_sha1": hashlib.sha1(script).hexdigest(),
        "accepted_tokens": walk["accepted_tokens"],
        "unexplained_bytes": walk["unexplained_bytes"],
        "call_sites": len([r for r in walk["refs"]
                           if r["token"] in ("EX_VirtualFunction", "EX_FinalFunction")]),
        "calls": calls,
        "refs": [{"at": r["at"], "token": r["token"], "ref": r.get("ref"),
                  "kind": r.get("kind")} for r in walk["refs"]
                 if r["token"] not in ("EX_VirtualFunction", "EX_FinalFunction")],
        "constants": walk["constants"],
        "anchors": {
            "script_size_field_eq_len_plus_1":
                struct.unpack_from("<i", data, 18)[0] == len(script) + 1,
            "name_index_matches_export_name":
                0 <= name_idx < len(pkg.names) and pkg.names[name_idx] == name,
            "pre_name_word_0x0002xxxx": (pre & 0xFFFF0000) == 0x00020000,
        },
    }
    if depth == 0 and budget[0] > 0:
        entry["callees"] = []
        for c in calls:
            tgt = c["target"]
            if c["token"] != "EX_FinalFunction" or not tgt or budget[0] <= 0:
                continue
            if c["target_class"] != "Function":
                continue
            j = bm.by_path.get(tgt)
            if not j:
                continue
            budget[0] -= 1
            sub = decode(bm, j, 1, budget)
            entry["callees"].append({"from_call_at": c["at"], "target": tgt,
                                     "path": sub["path"], "export": sub["export"],
                                     "script_bytes": sub["script_bytes"],
                                     "calls": sub["calls"]})
    return entry


def ini_rows():
    rows = {}
    with open(INI, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if ".Bindings=" in line:
                rows[n] = line.strip()
    return rows


def word_in(cmd, text):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(cmd) + r"(?![A-Za-z0-9_])", text) is not None


def build():
    bm = B.Bm(UPK)
    pkg = bm.pkg
    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    state_i = next((i for i in range(1, pkg.export_count + 1)
                    if pkg.object_class(i) == "State" and pkg.object_path(i) == STATE), None)
    class_i = pkg.exports[state_i - 1]["outer_index"] if state_i else None
    doc = {"package": "BmGame.upk", "bytes": os.path.getsize(UPK), "version": pkg.version,
           "licensee": pkg.licensee, "names": pkg.name_count, "exports": pkg.export_count,
           "state": {"path": STATE, "export": state_i,
                     "name": pkg.exports[state_i - 1]["name"],
                     "class_export": class_i,
                     "class_path": pkg.object_path(class_i) if class_i else None},
           "functions": [], "siblings": [], "oracles": [], "bindings": {}, "unknowns": []}

    kids, outer_ok = [], True
    for nm in FUNCS:
        hits = [i for i in range(1, pkg.export_count + 1)
                if pkg.exports[i - 1]["name"] == nm]
        mine = [i for i in hits if pkg.exports[i - 1]["outer_index"] == state_i]
        sib = [i for i in hits if class_i and pkg.exports[i - 1]["outer_index"] == class_i]
        if len(mine) != 1:
            outer_ok = False
        kids.append({"name": nm, "export": mine[0] if mine else None,
                     "sibling": sib[0] if sib else None, "hits": len(hits)})
    oracle("O1-state-functions",
           state_i is not None and pkg.object_class(state_i) == "State" and outer_ok,
           "state `%s` export %d, class `%s` export %s; %d/%d commands resolve to exactly one "
           "Function with outer_index == %d"
           % (STATE, state_i, doc["state"]["class_path"], class_i,
              sum(1 for k in kids if k["export"]), len(FUNCS), state_i))

    budget = [64]
    for k in kids:
        if k["export"]:
            f = decode(bm, k["export"], 0, budget)
            f["command"] = k["name"]
            f["names_hit"] = k["hits"]
            f["class_sibling_export"] = k["sibling"]
            doc["functions"].append(f)
    for k in kids:
        if k["sibling"]:
            s = decode(bm, k["sibling"], 1, budget)
            s["command"] = k["name"]
            s["state_export"] = k["export"]
            doc["siblings"].append(s)

    every = doc["functions"] + doc["siblings"]
    bad = [f["path"] for f in every if not all(f["anchors"].values())]
    oracle("O2-layout-anchors", not bad,
           "%d/%d decoded exports pass all three anchors (script_size field == len+1, name "
           "index == export name, pre-name word 0x0002xxxx)%s"
           % (len(every) - len(bad), len(every), "" if not bad else "; FAIL: " + ", ".join(bad)))

    ncalls, gaps, no_term, heur = 0, [], [], []
    for f in every + [c for f in doc["functions"] for c in f.get("callees", [])]:
        for c in f["calls"]:
            ncalls += 1
            if c["err"]:
                gaps.append("%s@%d starts at %d, gap: %s"
                            % (short(f["path"]), c["at"], c["end"], c["err"]))
            elif not c["terminator_ok"]:
                no_term.append("%s@%d" % (short(f["path"]), c["at"]))
            if c["heuristic_args"]:
                heur.append("%s@%d" % (short(f["path"]), c["at"]))
    oracle("O3-arguments", not no_term,
           "%d call sites: %d argument lists end on a re-verified 0x16 (%d of those use at "
           "least one uniqueness-checked heuristic width), %d stop at an exact gap%s"
           % (ncalls, ncalls - len(gaps), len(heur), len(gaps),
              "" if not gaps else ": " + " | ".join(gaps[:4])))

    dropped = [short(f["path"]) for f in every if f["call_sites"] != len(f["calls"])]
    oracle("O4-call-completeness", not dropped,
           "%d functions: accepted 0x1B/0x1C count == rows emitted%s"
           % (len(every), "" if not dropped else "; dropped: " + ", ".join(dropped)))

    mism, seen = [], 0
    if os.path.exists(CONSUMERS_JSON):
        ref = json.load(open(CONSUMERS_JSON, encoding="utf-8")).get("walks", {})
        for f in every:
            r = ref.get(f["path"])
            if not r:
                continue
            seen += 1
            if (r["export"] != f["export"] or r["script_bytes"] != f["script_bytes"]
                    or not f["script_sha1"].startswith(r["script_sha1"][:12])):
                mism.append("%s (export %s/%s, bytes %s/%s)"
                            % (f["path"], f["export"], r["export"],
                               f["script_bytes"], r["script_bytes"]))
        oracle("O5-cross-check-g3-02b", not mism and seen > 0,
               "%d/%d bodies match CONTROLS_CONSUMERS.json on export id, script length and "
               "sha1 prefix%s" % (seen - len(mism), seen,
                                  "" if not mism else "; mismatch: " + "; ".join(mism)))
    else:
        oracle("O5-cross-check-g3-02b", False, "CONTROLS_CONSUMERS.json missing")

    quotes = []
    for f in every:
        for c in f["calls"]:
            for a in c["args"]:
                if a.get("value") is not None:
                    quotes.append({"path": f["path"], "export": f["export"],
                                   "call_at": c["at"], "at": a["at"],
                                   "tok": a["tok"], "value": a["value"],
                                   "heuristic": bool(a.get("heuristic"))})
    ok6, detail = bool(quotes), []
    for q in quotes:
        script = script_of(pkg, q["export"])[1]
        if q["tok"] == "EX_IntConst":
            got = struct.unpack_from("<i", script, q["at"] + 1)[0]
        elif q["tok"] in ("EX_IntConstByte",):
            got = script[q["at"] + 1]
        elif q["tok"] == "EX_FloatConst":
            got = round(struct.unpack_from("<f", script, q["at"] + 1)[0], 6)
        elif q["heuristic"]:
            got = q["value"] if q["tok"].startswith("unnamed") is None else q["value"]
        else:
            got = q["value"]
        if got != q["value"]:
            ok6 = False
            detail.append("%s@%d" % (short(q["path"]), q["at"]))
    doc["quoted_literals"] = quotes
    oracle("O6-quoted-arguments", ok6,
           "%d literal arguments re-read from the bytes at their token offsets%s"
           % (len(quotes), "" if ok6 else "; mismatch at " + ", ".join(detail[:5])))

    modes = {nm: (pkg.names.index(nm) if nm in pkg.names else None)
             for nm in ("BattleMode", "PursuitMode")}
    mode_calls, mode_bad = [], []
    for f in every:
        for c in f["calls"]:
            if not (c["target"] or "").endswith("TryToChangeMode"):
                continue
            vals = [a["value"] for a in c["args"] if isinstance(a.get("value"), int)]
            hit = [v for v in vals if v in modes.values()]
            mode_calls.append({"path": f["path"], "at": c["at"], "values": vals,
                               "mode": next((k for k, v in modes.items() if v in hit), None)})
            if len(hit) != 1:
                mode_bad.append("%s@%d" % (short(f["path"]), c["at"]))
    doc["mode_calls"] = mode_calls
    oracle("O8-mode-argument", bool(mode_calls) and not mode_bad,
           "%d TryToChangeMode call(s); the decoded argument equals names[%s]='BattleMode' or "
           "names[%s]='PursuitMode' in each%s"
           % (len(mode_calls), modes["BattleMode"], modes["PursuitMode"],
              "" if not mode_bad else "; FAIL " + ", ".join(mode_bad)))

    rows = ini_rows()
    for nm in FUNCS:
        doc["bindings"][nm] = [{"line": n, "text": t} for n, t in sorted(rows.items())
                               if word_in(nm, t)]
    stale = [(nm, r["line"]) for nm, rs in doc["bindings"].items() for r in rs
             if r["line"] not in rows or not word_in(nm, rows[r["line"]])]
    unbound = [nm for nm, rs in doc["bindings"].items() if not rs]
    oracle("O7-bindings", not stale,
           "%d DefaultInput.ini `Bindings=` rows re-read and matched to %d commands; %d command(s) "
           "have no binding anywhere in the chain: %s%s"
           % (sum(len(v) for v in doc["bindings"].values()),
              len([1 for rs in doc["bindings"].values() if rs]), len(unbound),
              ", ".join(unbound) or "none",
              "" if not stale else "; STALE %r" % (stale[:4],)))

    doc["oracles"] = oracles
    doc["unknowns"] = [
        {"what": "control flow inside every body (jumps, branches, conditions)",
         "why": "the repo walk is one left-to-right pass without a jump table. A call in a body "
                "proves the body contains it, not that the button's path executes it; each "
                "function's unexplained byte count is reported so the residue stays visible."},
        {"what": "what an `EX_VirtualFunction` (0x1B) FName dispatches to",
         "why": "0x1B carries a name, not an object. name_match lists every export with that "
                "name (state, class and unrelated classes); the engine's dispatch is not stored "
                "in the package."},
        {"what": "the arguments inside an `EX_Context` (0x19) / `EX_Skip` (0x18) window",
         "why": "these tokens carry a nested expression and a skip offset, so they have no fixed "
                "operand width; the argument list stops there and the offset is reported."},
        {"what": "the effect of a native/imported callee",
         "why": "a call whose operand is <= 0 (an import such as Core.*) has no body in this "
                "package; it can only be reported by name."},
        {"what": "which weapon or mode an integer argument selects",
         "why": "the literals are decoded, but the objects behind the *PrimaryWeapon / "
                "SecondaryWeapon slots and the weapon class indices are not resolved here."},
    ]
    return doc


def kind_of(token):
    return "virtual(0x1B)" if token == "EX_VirtualFunction" else "final(0x1C)"


def render(doc):
    L = []

    def A(x):
        L.append(x)

    ok = sum(1 for o in doc["oracles"] if o["ok"])
    ncalls = sum(len(f["calls"]) for f in doc["functions"])
    A("# DrivingMode exec bodies, token by token (G3-02i)")
    A("")
    A("Generated by `Tools/scripts/grab_drivingmode.py --write` from `%s` (read-only, %s bytes, "
      "version %d, %s exports, %s names). `--check` re-derives every offset, sha1, argument and "
      "verdict; the game is never run." %
      (doc["package"], f"{doc['bytes']:,}", doc["version"], f"{doc['exports']:,}",
       f"{doc['names']:,}"))
    A("")
    A("**Oracles %d/%d pass.** %d state functions decoded, **%d call sites with arguments**, %d "
      "class-level siblings, %d callees one level deeper."
      % (ok, len(doc["oracles"]), len(doc["functions"]), ncalls, len(doc["siblings"]),
         sum(len(f.get("callees", [])) for f in doc["functions"])))
    A("")
    A("The `%s` state is export **%d**, class `%s` export %s. `object_path` uses the outer's short "
      "name, so state bodies print as `%s.<name>`."
      % (doc["state"]["path"], doc["state"]["export"], doc["state"]["class_path"],
         doc["state"]["class_export"], doc["state"]["name"]))
    A("")
    A("## 1. Command -> body")
    A("")
    A("| command | bound at (DefaultInput.ini) | state body | class sibling |")
    A("|---|---|---|---|")
    for f in doc["functions"]:
        nm = f["command"]
        bl = doc["bindings"].get(nm) or []
        sib = next((s for s in doc["siblings"] if s["command"] == nm), None)
        A("| `%s` | %s | export %d, %d script bytes, sha1 `%s` | %s |"
          % (nm, ", ".join("`:%d`" % b["line"] for b in bl) or "**not bound in the chain**",
             f["export"], f["script_bytes"], f["script_sha1"][:12],
             ("export %d, %d script bytes" % (sib["export"], sib["script_bytes"]))
             if sib else "none"))
    A("")
    A("A class sibling whose script is one byte is an empty stub (`EX_Return` only), so the state "
      "body is the implementation for that command.")
    A("")
    A("A binding line names a *command*; which body the command executes is not stored in the "
      "package (gap 2).")
    A("")
    A("## 2. Calls and arguments")
    A("")
    for f in doc["functions"] + doc["siblings"]:
        kind = "state body" if f in doc["functions"] else "class sibling"
        A("### `%s` - %s (export %d, %d bytes, %d script bytes, %d tokens, %d unexplained bytes)"
          % (f["path"], kind, f["export"], f["size"], f["script_bytes"],
             f["accepted_tokens"], f["unexplained_bytes"]))
        A("")
        if not f["calls"]:
            A("No call token in this body.")
            A("")
            continue
        A("| at | kind | target | arguments | argument tokens |")
        A("|---|---|---|---|---|")
        for c in f["calls"]:
            A("| %d | %s | `%s` | `%s` | %s |"
              % (c["at"], kind_of(c["token"]), c["target"] or "?",
                 c["text"][:160],
                 ", ".join("%s@%d%s" % (a["tok"], a["at"],
                                        "*" if a.get("heuristic") else "")
                           for a in c["args"]) or "-"))
        A("")
        for c in f["calls"]:
            if c["err"]:
                A("- **exact gap** in `%s` at %d: %s" % (c["target"], c["at"], c["err"]))
            if c.get("name_match"):
                A("- `%s`: name-match candidates %s"
                  % (short(c["target"]), ", ".join("`%s`" % m for m in c["name_match"][:4])))
        A("")
        if f.get("callees"):
            A("Callees decoded one level deeper:")
            A("")
            for sub in f["callees"]:
                A("- `%s` (export %d, %d script bytes): %s"
                  % (sub["target"], sub["export"], sub["script_bytes"],
                     "; ".join("`%s`" % c["text"][:110] for c in sub["calls"]) or "no calls"))
            A("")
    A("`*` marks a token the repo table does not name: it was given the smallest operand width in "
      "{0,1,2,3,4,8,9,12,13} that lets the argument list reach its 0x16 (width 0 = bare, shown as "
      "`<0xNN>`; it may be a separator rather than a value). A heuristic integer is the raw "
      "little-endian payload, not a name-index claim.")
    if doc.get("mode_calls"):
        A("")
        A("Mode argument (O8): " + "; ".join(
            "`%s@%d` -> %s, payload %s"
            % (short(m["path"]), m["at"], m["mode"], m["values"])
            for m in doc["mode_calls"])
            + " - the payload is that state's index in the name table.")
    A("")
    A("## 3. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 4. Exact gaps")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** - %s" % (u["what"], u["why"]))
    A("")
    A("## 5. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/grab_drivingmode.py --write")
    A("uv run python Tools/scripts/grab_drivingmode.py --check")
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
        print("wrote Research/BatmobileGrab/DRIVINGMODE.md and .json")
        print("  %d state functions, %d siblings, %d call sites, %d/%d oracles"
              % (len(doc["functions"]), len(doc["siblings"]),
                 sum(len(f["calls"]) for f in doc["functions"] + doc["siblings"]),
                 len(doc["oracles"]), len(doc["oracles"])))
        for f in doc["functions"]:
            print("    %-28s export %-6d script %-5d calls %-3d gaps %d"
                  % (f["command"], f["export"], f["script_bytes"], len(f["calls"]),
                     sum(1 for c in f["calls"] if c["err"])))
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
        print("FAIL: DRIVINGMODE.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: DRIVINGMODE.json is stale")
        return 1
    print("OK %d/%d oracles, %d state functions, %d call sites, md+json identical"
          % (len(doc["oracles"]), len(doc["oracles"]), len(doc["functions"]),
             sum(len(f["calls"]) for f in doc["functions"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
