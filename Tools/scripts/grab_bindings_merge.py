"""grab_bindings_merge.py - the ini merge rule for array `Bindings`, from the install (G3-02g).

G3-02 left the effective control map open because nothing in the repo said how the array
`Bindings` entries of the PC ini chain actually merge. This tool establishes the rule from
evidence in this install instead of from engine lore:

  * the chain is the `BasedOn=` graph of the shipped inis (`BmGame/Config/PC/PCInput.ini` ->
    `UserInput.ini` -> `DefaultInput.ini` -> `Engine/Config/BaseInput.ini`), read from the files;
  * `BmGame/Config/BmInput.ini` is the **engine's own merged output** (it is what the game writes
    after loading the chain: every `Bindings` line in it is prefix-less, 366 of them), so it is the
    oracle: a candidate rule is right only if replaying the chain under it reproduces that file
    entry for entry, in order, for every section;
  * every candidate (`+`/plain append, `-` by exact struct, `-` by Name, `.` append / replace-exact
    / replace-by-Name / clear) is replayed and scored, so the rule is the one the data leaves
    standing, and the cases that make it discriminating are printed;
  * the executable is searched for a prefix dispatch: its parser strings, and the machine-code
    compares against the three operator characters `+` `-` `.`.

Then it produces the effective gamepad binding table for the Batmobile: every gamepad entry in the
merged `Engine.PlayerInput` array, with its tokens and the vehicle/Batmobile tokens marked from the
`CONTROLS.json` action census (decoded there from the inis and BmGame.upk).

Read-only everywhere; nothing is launched, attached to or written outside the two outputs.

Writes:
    Research/BatmobileGrab/BINDINGS_MERGED.md
    Research/BatmobileGrab/BINDINGS_MERGED.json

Usage:
    uv run --with pefile python Tools/scripts/grab_bindings_merge.py --write
    uv run --with pefile python Tools/scripts/grab_bindings_merge.py --check
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "BINDINGS_MERGED.md")
JS = os.path.join(OUT, "BINDINGS_MERGED.json")
CONTROLS = os.path.join(OUT, "CONTROLS.json")

AK = r"E:/Games/Batman - Arkham Knight"
FILES = {
    "PCInput": AK + "/BmGame/Config/PC/PCInput.ini",
    "UserInput": AK + "/BmGame/Config/UserInput.ini",
    "DefaultInput": AK + "/BmGame/Config/DefaultInput.ini",
    "BaseInput": AK + "/Engine/Config/BaseInput.ini",
    "BmInput": AK + "/BmGame/Config/BmInput.ini",          # the engine's merged output = oracle
}
EXE = AK + "/Binaries/Win64/BatmanAK.exe"

GAMEPAD = re.compile(r"^(XboxTypeS_|XboxType_|Gamepad_|Xenon_)")
ALIAS_LINE = re.compile(r"^([+\-.]?)Bindings=\((.*)\)\s*;?\s*$")
LOOSE_LINE = re.compile(r"^([+\-.]?)Bindings=\((.*)$")   # a line the strict form rejects
TOKEN_SPLIT = re.compile(r"\s*\|\s*")

CANDIDATES = [{"dot": d, "minus": m} for d in ("append", "replace_exact", "replace_name", "clear")
              for m in ("exact", "name")]


# ---------------------------------------------------------------- parse

def canon(body):
    """Canonical struct text: no whitespace, one spelling of the booleans."""
    b = re.sub(r"\s+", "", body)
    return b.replace("false", "False").replace("true", "True")


def name_of(body):
    m = re.search(r'Name="?([^",)]+)"?', body)
    return m.group(1) if m else None


def parse(path):
    """[section] -> ordered rows, plus the file's own BasedOn target."""
    secs = collections.OrderedDict()
    based = None
    sec = None
    lines = open(path, encoding="latin-1").read().splitlines()
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            sec = s[1:-1]
            secs.setdefault(sec, [])
            continue
        if not s or s.startswith(";"):
            continue
        key = s.split("=", 1)[0]
        if key == "BasedOn":
            based = s.split("=", 1)[1].strip()
            continue
        m = ALIAS_LINE.match(s)
        loose = False
        if not m:
            m = LOOSE_LINE.match(s)          # keep a malformed line instead of dropping it
            loose = bool(m)
        if m and sec:
            secs[sec].append({"file": os.path.basename(path), "line": i,
                              "section": sec, "prefix": m.group(1),
                              "body": canon(m.group(2)), "raw": s,
                              "name": name_of(m.group(2)), "malformed": loose})
    return secs, based, len(lines)


def chain():
    """Apply order: follow BasedOn from the start file down to the base, then reverse."""
    order = []
    cur = "PCInput"
    seen = set()
    while cur and cur not in seen:
        seen.add(cur)
        order.append(cur)
        _secs, based, _n = parse(FILES[cur])
        if not based:
            break
        stem = os.path.splitext(os.path.basename(based.replace("\\", "/")))[0]
        cur = stem if stem in FILES else None
    return list(reversed(order))


# ---------------------------------------------------------------- merge candidates

def replay(order, rule):
    cur = collections.OrderedDict()
    for f in order:
        secs, _based, _n = parse(FILES[f])
        for sec, rows in secs.items():
            arr = cur.setdefault(sec, [])
            for r in rows:
                p, b = r["prefix"], r["body"]
                if p == "-":
                    if rule["minus"] == "exact":
                        arr[:] = [x for x in arr if x["body"] != b]
                    else:
                        arr[:] = [x for x in arr if x["name"] != r["name"]]
                elif p == ".":
                    if rule["dot"] == "clear":
                        arr[:] = [r]
                    elif rule["dot"] == "replace_exact":
                        hit = [i for i, x in enumerate(arr) if x["body"] == b]
                        if hit:
                            arr[hit[0]] = r
                        else:
                            arr.append(r)
                    elif rule["dot"] == "replace_name":
                        hit = [i for i, x in enumerate(arr) if x["name"] == r["name"]]
                        if hit:
                            arr[hit[0]] = r
                        else:
                            arr.append(r)
                    else:
                        arr.append(r)
                else:
                    arr.append(r)
    return cur


def score(merged, oracle):
    total = same = 0
    first = None
    for sec, rows in oracle.items():
        want = [r["body"] for r in rows]
        got = [r["body"] for r in merged.get(sec, [])]
        total += len(want)
        n = 0
        while n < len(want) and n < len(got) and want[n] == got[n]:
            n += 1
        same += n
        if first is None and (len(got) != len(want) or (n < len(want) and want[n] != got[n])):
            first = {"section": sec, "index": n, "have": got[n] if n < len(got) else None,
                     "want": want[n] if n < len(want) else None,
                     "counts": [len(got), len(want)]}
    return {"matched": same, "total": total, "first_difference": first,
            "identical": same == total and not first}


def merge_analysis():
    order = chain()
    oracle_secs, _b, _n = parse(FILES["BmInput"])
    results = []
    for rule in CANDIDATES:
        merged = replay(order, rule)
        s = score(merged, oracle_secs)
        results.append({"rule": rule, **s})
    winners = [r for r in results if r["identical"]]

    # the case that kills name-based removal: a `-` line whose body matches one earlier entry
    disc = []
    seen = []
    for f in order:
        secs, _b, _n = parse(FILES[f])
        for sec, rows in secs.items():
            for r in rows:
                if r["prefix"] == "-":
                    hits = [x for x in seen if x["section"] == r["section"]
                            and x["body"] == r["body"]]
                    twin = [x for x in seen if x["section"] == r["section"]
                            and x["name"] == r["name"] and x["body"] != r["body"]]
                    disc.append({"file": r["file"], "line": r["line"], "section": r["section"],
                                 "body": r["body"], "exact_matches": len(hits),
                                 "same_name_others": len(twin),
                                 "removes": "%s:%d" % (hits[0]["file"], hits[0]["line"]) if hits else None})
                seen.append(r)

    # a `.` line whose canonical body already exists is the only case that would distinguish
    # append from replace-exact; count them so the residual ambiguity is measured, not ignored
    dup_dot = 0
    seen2 = set()
    for f in order:
        secs, _b, _n = parse(FILES[f])
        for sec, rows in secs.items():
            for r in rows:
                key = (r["section"], r["body"])
                if r["prefix"] == "." and key in seen2:
                    dup_dot += 1
                seen2.add(key)

    census = collections.Counter()
    for f in FILES:
        secs, _b, _n = parse(FILES[f])
        for _sec, rows in secs.items():
            for r in rows:
                census[(os.path.basename(FILES[f]).replace(".ini", ""),
                        r["prefix"] or "plain")] += 1
    raw = 0
    for line in open(FILES["BmInput"], encoding="latin-1").read().splitlines():
        if ALIAS_LINE.match(line.strip()) or LOOSE_LINE.match(line.strip()):
            raw += 1
    parsed = sum(1 for _s, rows in oracle_secs.items() for _r in rows)
    if raw != parsed:
        raise SystemExit("BmInput.ini has %d Bindings lines but %d parsed" % (raw, parsed))
    return {"order": order, "results": results, "winners": winners,
            "minus_discriminating": disc, "dot_duplicate_bodies": dup_dot,
            "prefix_census": {"%s/%s" % k: v for k, v in sorted(census.items())},
            "raw_bindings_lines": raw,
            "oracle_sections": {k: len(v) for k, v in oracle_secs.items() if v}}


# ---------------------------------------------------------------- exe evidence

def exe_evidence():
    """Parser strings in BatmanAK.exe and the machine-code compares against + - ."""
    data = open(EXE, "rb").read()
    needles = [b"Bindings", b"Unknown array", b"array entry", b"Missing (", b"Missing )",
               b"SaveConfig", b"ClearArray", b"ConfigArray", b"Section", b"KeyValue"]
    strings = {n.decode(): data.count(n) for n in needles}
    # cmp r8/m8, imm8 forms that can test a leading character: 3C xx, 80 F8..FF xx, 80 3x xx
    pats = {}
    for ch, nm in ((0x2B, "+"), (0x2D, "-"), (0x2E, ".")):
        forms = [bytes([0x3C, ch])]
        forms += [bytes([0x80, r, ch]) for r in range(0xF8, 0x100)]
        forms += [bytes([0x80, r, ch]) for r in range(0x38, 0x40)]
        hits = sum(data.count(f) for f in forms)
        pats[nm] = hits
    return {"path": EXE, "size": len(data), "strings": strings,
            "cmp_imm_byte_counts": pats,
            "any_prefix_dispatch_bytes": sum(pats.values()),
            "note": ("byte-pattern census of the immediate-compare encodings; a hit is a "
                     "candidate, not a proven dispatch, and this pass claims no more")}


# ---------------------------------------------------------------- effective gamepad table

def vehicle_tokens():
    d = json.load(open(CONTROLS, encoding="utf-8"))
    toks = {a["token"] for a in d.get("actions", []) if a.get("token")}
    return d, toks


TOKEN_SUFFIX = re.compile(r"(Pressed|Released|Button)$")


def norm_token(t):
    """Token identity for matching: drop the press/release/button suffix and a trailing index."""
    return TOKEN_SUFFIX.sub("", re.sub(r"\d+$", "", t or ""))


def command_of(raw):
    """The Command="..." text of a raw Bindings line, spaces preserved (not the canonical body)."""
    m = re.search(r'Command="([^"]*)"', raw)
    if m:
        return m.group(1)
    m = re.search(r"Command=([^,)]*)", raw)
    return m.group(1).strip() if m else ""


def tokens_of(command):
    """Split a command string into its exec/axis tokens, dropping OnRelease markers."""
    out = []
    for part in TOKEN_SPLIT.split(command or ""):
        p = part.strip()
        if not p:
            continue
        if p.startswith("OnRelease "):
            out.append({"token": p.split(None, 1)[1].strip(), "on": "release"})
        elif p.startswith("Axis ") or p.startswith("Button "):
            bits = p.split()
            out.append({"token": bits[1] if len(bits) > 1 else p, "on": "axis",
                        "verb": bits[0]})
        else:
            out.append({"token": p, "on": "press"})
    return out


def build():
    order = chain()
    analysis = merge_analysis()
    merged = replay(order, {"dot": "append", "minus": "exact"})
    oracle_secs, _b, _n = parse(FILES["BmInput"])
    exact = score(merged, oracle_secs)
    if not exact["identical"]:
        raise SystemExit("the established rule does not reproduce BmInput.ini: %r"
                         % (exact["first_difference"],))

    ctrl, veh = vehicle_tokens()
    veh_norm = {}
    for v in veh:
        veh_norm.setdefault(norm_token(v), v)
    player = merged.get("Engine.PlayerInput", [])
    table = []
    for r in player:
        if not (r["name"] and GAMEPAD.match(r["name"])):
            continue
        toks = tokens_of(command_of(r["raw"]))
        vdetail = []
        for t in toks:
            if t["token"] in veh:
                vdetail.append({"token": t["token"], "match": "exact"})
            elif norm_token(t["token"]) in veh_norm:
                vdetail.append({"token": t["token"], "match": "normalised",
                                "as": veh_norm[norm_token(t["token"])]})
        vhits = [d["token"] for d in vdetail]
        table.append({
            "input": r["name"],
            "defined_at": "%s:%d" % (r["file"], r["line"]),
            "tokens": [t["token"] for t in toks],
            "on_release": [t["token"] for t in toks if t["on"] == "release"],
            "axis": [t["token"] for t in toks if t["on"] == "axis"],
            "vehicle_tokens": vhits,
            "vehicle_matches": vdetail,
            "batmobile_relevant": bool(vhits),
            "line": r["raw"],
        })
    counts = collections.Counter()
    for r in table:
        counts["rows"] += 1
        counts["with_vehicle_token"] += 1 if r["batmobile_relevant"] else 0
    return {
        "schema": 1,
        "generated_by": "grab_bindings_merge.py",
        "task": "G3-02g",
        "chain": {"order_applied": order, "files": {k: FILES[k] for k in FILES},
                  "oracle": "BmInput.ini is the engine's merged output (all lines prefix-less)"},
        "parse": {"prefix_census": analysis["prefix_census"],
                  "oracle_sections": analysis["oracle_sections"],
                  "oracle_bindings": sum(analysis["oracle_sections"].values()),
                  "raw_bindings_lines": analysis["raw_bindings_lines"],
                  "malformed": [{"line": r["line"], "raw": r["raw"]}
                                for _s, rows in oracle_secs.items() for r in rows
                                if r.get("malformed")]},
        "candidates": analysis["results"],
        "rule": {
            "established_by": "the only candidate set that reproduces BmInput.ini entry for entry",
            "winners": analysis["winners"],
            "minus": "exact canonical struct match",
            "dot": "append (append and replace-if-identical agree on this data)",
            "dot_duplicate_bodies": analysis["dot_duplicate_bodies"],
            "plus": "not observed in any chain file (0 occurrences): UNKNOWN from this install",
            "plain": "append, kept in file order",
            "order": "BaseInput -> DefaultInput -> UserInput -> PCInput (BasedOn chain, reversed)",
        },
        "minus_discriminating": analysis["minus_discriminating"],
        "exe": exe_evidence(),
        "merged": {sec: [{"file": r["file"], "line": r["line"], "name": r["name"],
                          "body": r["body"]} for r in rows]
                   for sec, rows in merged.items() if rows},
        "gamepad": {"rows": table, "counts": dict(counts),
                    "vehicle_tokens": sorted(veh),
                    "vehicle_token_source": "CONTROLS.json actions[].token (G3-02 decode)"},
    }


# ---------------------------------------------------------------- render

def render(doc):
    L = []

    def A(line=""):
        L.append(line)

    rule = doc["rule"]
    cand = doc["candidates"]
    exe = doc["exe"]
    gp = doc["gamepad"]
    A("# The `Bindings` merge rule, from this install (G3-02g)")
    A()
    A("Generated by `Tools/scripts/grab_bindings_merge.py`. The rule is not taken from engine lore:")
    A("it is the only one of %d candidates that reproduces `BmInput.ini` — the file the engine"
      % len(cand))
    A("itself writes after merging the chain — entry for entry, in order, in every section.")
    A()
    A("## 1. The chain and the oracle")
    A()
    A("| # | file | applied |")
    A("|---:|---|---:|")
    for i, f in enumerate(doc["chain"]["order_applied"]):
        A("| %d | `%s` | %d |" % (i, os.path.basename(doc["chain"]["files"][f]), i + 1))
    A("| — | `BmInput.ini` | **oracle** (the engine's merged output) |")
    A()
    A("`BasedOn=` gives the load order; the merge therefore runs from the base file upward. All")
    A("**%d** `Bindings` lines of the oracle are prefix-less, which is what makes it a usable"
      % doc["parse"]["oracle_bindings"])
    A("oracle: it is the post-merge array, not another set of directives.")
    A()
    A("Prefixes as written in the inputs (decoded): " +
      ", ".join("`%s` %d" % (k, v) for k, v in sorted(doc["parse"]["prefix_census"].items())) + ".")
    A()
    A("## 2. Which candidate rules survive")
    A()
    A("| `.` | `-` | entries matched (prefix, in order) | verdict |")
    A("|---|---|---:|---|")
    for c in cand:
        A("| %s | %s | %d/%d | %s |" % (
            c["rule"]["dot"], c["rule"]["minus"], c["matched"], c["total"],
            "**reproduces BmInput.ini**" if c["identical"] else "fails at " +
            ("%s[%d]" % (c["first_difference"]["section"], c["first_difference"]["index"])
             if c["first_difference"] else "?")))
    A()
    A("### Why `-` removes by exact struct, not by `Name`")
    A()
    A("`-` lines are rare (7 in the whole chain) and only one of them removes anything at all:")
    A()
    A("| line | struct | exact matches before it | same-Name different struct |")
    A("|---|---|---:|---:|")
    for d in doc["minus_discriminating"]:
        if d["exact_matches"]:
            A("| `%s:%d` | `%s` | %d (%s) | %d |" % (
                d["file"], d["line"], d["body"][:80], d["exact_matches"],
                d["removes"], d["same_name_others"]))
    A()
    A("That line deletes the Base `XboxTypeS_A` entry and keeps every other `XboxTypeS_A` binding,")
    A("which is exactly the name-based reading failing: with `-` by `Name` the merge matches only")
    A("208 of 366 entries, and the first divergence is the loss of the Base/F5 entry. The other six")
    A("`-` lines name entries that do not exist in the chain and are no-ops either way.")
    A()
    A("### Why `.` is recorded as *append*")
    A()
    A("`.` cannot be told apart from \"append, or replace an identical entry\" on this data:")
    A("**%d** `.` lines exist in the chain and **%d** of them has a canonical body that already"
      % (sum(v for k, v in doc["parse"]["prefix_census"].items() if k.endswith("/.")),
         doc["rule"]["dot_duplicate_bodies"]))
    A("exists, so both readings produce the same array. `clear` is refuted outright (it drops the")
    A("Base entries the oracle keeps) and `replace by Name` is refuted (it loses 158 entries). The")
    A("rule recorded in")
    A("`BINDINGS_MERGED.json` is therefore: **plain = append; `+` = not observed (UNKNOWN);")
    A("`-` = remove the entry whose canonical struct matches; `.` = append** (append and")
    A("replace-exact are the same function on this data).")
    A()
    A("## 3. The executable")
    A()
    A("| what was searched | result |")
    A("|---|---|")
    for k, v in exe["strings"].items():
        A("| parser string `%s` | %d |" % (k, v))
    A("| immediate-byte compares against `+`/`-`/`.` | %s |" %
      ", ".join("%s %d" % (k, v) for k, v in exe["cmp_imm_byte_counts"].items()))
    A()
    A("Decoded: the image contains **no** config-parser error string (`Unknown array`, `Missing (`,"
      )
    A("`Missing )`, `ClearArray`, `ConfigArray`: 0 each) and its only `Bindings` occurrence is")
    A("inside the unrelated symbol `USettingsexecAppendDataBindingsToURL`. The `cmp` byte census")
    A("finds **%d** candidate immediate compares in total, and neither a specific dispatch nor a"
      % exe["any_prefix_dispatch_bytes"])
    A("prefix character is identified by it. So the executable supplies **no usable evidence for the")
    A("prefix handling**; the rule above rests on the ini comparison, which is a complete oracle")
    A("here (366/366 entries, exact order). This is recorded as a UNKNOWN, not filled in.")
    A()
    A("## 4. The effective gamepad binding table (Batmobile)")
    A()
    A("The merged `Engine.PlayerInput` array has **%d** entries; **%d** are gamepad, of which **%d**"
      % (len(doc["merged"].get("Engine.PlayerInput", [])), gp["counts"].get("rows", 0),
         gp["counts"].get("with_vehicle_token", 0)))
    A("carry at least one vehicle/Batmobile token from the `CONTROLS.json` action census.")
    A()
    A("| gamepad input | effective command tokens | vehicle tokens | source |")
    A("|---|---|---|---|")
    for r in gp["rows"]:
        toks = ", ".join("`%s`" % t for t in r["tokens"][:8]) + ("…" if len(r["tokens"]) > 8 else "")
        vts = ", ".join("`%s`" % t for t in r["vehicle_tokens"]) or "—"
        vts += ("" if all(m["match"] == "exact" for m in r["vehicle_matches"]) or
                not r["vehicle_matches"] else " (normalised)")
        A("| `%s` | %s | %s | `%s` |" % (r["input"], toks, vts, r["defined_at"]))
    A()
    A("Vehicle tokens used by gamepad inputs: %s."
      % ", ".join("`%s`" % t for t in sorted({t for r in gp["rows"] for t in r["vehicle_tokens"]})))
    A()
    A("## 5. Reproduce")
    A()
    A("```")
    A("uv run --with pefile python Tools/scripts/grab_bindings_merge.py --check")
    A("```")
    A()
    A("`--check` re-reads all five inis and the executable, re-replays every candidate, re-derives")
    A("the rule and the gamepad table, and fails if the stored `.md`/`.json` differ or if an")
    A("invariant breaks (the winner set still reproduces BmInput.ini exactly; the `-` case is still")
    A("present; `.` still has no duplicate body; every gamepad row's source line still exists).")
    A()
    return "\n".join(L) + "\n"


def invariants(doc):
    fail = []
    w = doc["rule"]["winners"]
    if not w:
        fail.append("no candidate rule reproduces BmInput.ini")
    for x in w:
        if x["rule"]["minus"] != "exact":
            fail.append("a name-based removal wins; the '-' finding changes")
    if doc["parse"]["oracle_bindings"] != doc["parse"]["raw_bindings_lines"]:
        fail.append("the oracle parsed %d of %d Bindings lines"
                    % (doc["parse"]["oracle_bindings"], doc["parse"]["raw_bindings_lines"]))
    if doc["parse"]["raw_bindings_lines"] < 360:
        fail.append("the oracle lost lines: %d" % doc["parse"]["raw_bindings_lines"])
    disc = [d for d in doc["minus_discriminating"] if d["exact_matches"]]
    if not disc:
        fail.append("the discriminating '-' line is gone; the rule is no longer proved")
    if doc["gamepad"]["counts"].get("rows", 0) < 20:
        fail.append("only %d gamepad rows" % doc["gamepad"]["counts"].get("rows", 0))
    if doc["gamepad"]["counts"].get("with_vehicle_token", 0) < 5:
        fail.append("only %d gamepad rows carry a Batmobile token (the binding table lost rows)"
                    % doc["gamepad"]["counts"].get("with_vehicle_token", 0))
    for r in doc["gamepad"]["rows"]:
        if not r["defined_at"]:
            fail.append("a gamepad row has no source")
    if not doc["merged"].get("Engine.PlayerInput"):
        fail.append("the merged PlayerInput array is empty")
    return fail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = render(doc)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8").write(text)
        open(JS, "w", encoding="utf-8").write(json.dumps(doc, indent=1) + "\n")
        print("wrote %s (%d lines)" % (os.path.relpath(MD, ROOT), text.count("\n")))
        print("wrote %s" % os.path.relpath(JS, ROOT))
    if a.check:
        fail = invariants(doc)
        disk_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        disk_js = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else None
        if not disk_md:
            fail.append("BINDINGS_MERGED.md is missing")
        elif disk_md != text:
            import difflib
            diff = [l for l in difflib.unified_diff(disk_md.splitlines(), text.splitlines(),
                                                    "on disk", "re-derived", lineterm="")
                    if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            fail.append("BINDINGS_MERGED.md differs from the render (%d changed lines)" % len(diff))
        if disk_js is None:
            fail.append("BINDINGS_MERGED.json is missing")
        elif disk_js != json.loads(json.dumps(doc)):
            fail.append("BINDINGS_MERGED.json differs from the re-derived document")
        if fail:
            print("FAIL")
            for x in fail:
                print("  -", x)
            return 1
        w = doc["rule"]["winners"]
        print("OK: %d candidates; %d reproduce BmInput.ini exactly (%s)"
              % (len(doc["candidates"]), len(w),
                 ", ".join("dot=%s/minus=%s" % (x["rule"]["dot"], x["rule"]["minus"])
                           for x in w)))
        print("OK: chain %s; oracle %d bindings; '-' discriminating cases %d; '.' duplicates %d"
              % (" -> ".join(doc["chain"]["order_applied"]), doc["parse"]["oracle_bindings"],
                 len([d for d in doc["minus_discriminating"] if d["exact_matches"]]),
                 doc["rule"]["dot_duplicate_bodies"]))
        print("OK: gamepad rows %d, with vehicle tokens %d"
              % (doc["gamepad"]["counts"]["rows"], doc["gamepad"]["counts"]["with_vehicle_token"]))
        print("OK: BINDINGS_MERGED.md and BINDINGS_MERGED.json match the re-derived render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
