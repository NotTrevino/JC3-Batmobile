#!/usr/bin/env python3
"""t_fx16_term.py - which search term produces T-FX16's "0 of 955"?

T-FX16 (cannon round trail) is a named omission whose proof cell says "0 of 955 match over
all distinct `.effc` paths" but does not name the term. This script finds the term where it
actually lives - the `match` list of the T-FX16 rule in `Tools/scripts/t17_fx.py` - and then
runs that term plus every plausible reconstruction over the same 955 distinct `.effc` paths,
reporting the count for each.

The 955 (and the 589 vehicle-carried subset) are re-derived from `FX_TABLE.jsonl` with
`t17_fx.py`'s own rule: one record per distinct `path` with `ext == ".effc"`, a path is
vehicle-carried when any of its containers contains `/jc_vehicles/`.

Matching is a case-insensitive substring test on the full effect path, which is what
`t17_fx.py` does (`any(m in p for m in rule["match"])`, paths already lowercase in the table).

Out: `Working/Translation/FX16_TERM.md`. `--check` re-runs every count, asserts the constants
below and compares the document byte-for-byte. No row, ledger or existing output is written.

    python Tools/scripts/t_fx16_term.py --write
    python Tools/scripts/t_fx16_term.py --check
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FX_TABLE = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
RULE_SCRIPT = os.path.join(ROOT, "Tools", "scripts", "t17_fx.py")
ROW_JSON = os.path.join(ROOT, "Working", "Translation", "t17_fx.json")
ROW_MD = os.path.join(ROOT, "Working", "Translation", "T13_FX.md")
OUT = os.path.join(ROOT, "Working", "Translation", "FX16_TERM.md")

# (candidate, provenance, expected all-count, expected vehicle-count)
CANDIDATES: list[tuple[str, str, int, int]] = [
    ("canon_trail", "decoded: the T-FX16 `match` list in `t17_fx.py`", 0, 0),
    ("shell_trail", "decoded: the same `match` list", 0, 0),
    ("cannon", "row text: the feature is `cannon round trail`", 0, 0),
    ("trail", "the shared word of the feature, the row and the BmAK group `projectile-trail`", 84, 46),
    ("bullet", "row text: JC3 draws the round as a `tracer` on the bullet (T-FX12)", 23, 16),
    ("projectile", "the BmAK group name `projectile-trail`", 1, 0),
    ("round", "row text: `the round is represented by the tracer texture`", 11, 10),
    ("rocket", "BmAK name `Batmobile_JokersRocket_Trail`", 5, 5),
    ("mud", "BmAK name `Batmobile_Mud_Trail`", 1, 0),
    ("canon", "the one-n spelling that does occur (control, shows the spelling trap)", 1, 1),
    ("tracer", "the T-FX12 cross-reference in the row's `propose` (control)", 0, 0),
    ("spark_trail", "T-FX19's term, a different row (control)", 8, 3),
    ("exhaust", "T-FX7/T-FX8's family, a different row (control)", 39, 37),
    ("smoke", "control: the fleet's smoke vocabulary", 29, 20),
    ("missile", "control: T-FX14's family", 30, 25),
]


def load_fx() -> dict[str, set[str]]:
    rec: dict[str, set[str]] = {}
    with open(FX_TABLE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["ext"] != ".effc":
                continue
            rec.setdefault(r["path"], set()).add(r["container"])
    return rec


def decoded_needles(script: str) -> tuple[list[str], int]:
    m = re.search(r'dict\(id="T-FX16".*?match=\[([^\]]*)\]', script, re.S)
    if not m:
        return [], 0
    needles = re.findall(r'"([^"]+)"', m.group(1))
    line = script[:m.start()].count("\n") + 1
    return needles, line


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    rec = load_fx()
    paths = sorted(rec)
    veh = [p for p in paths if any("/jc_vehicles/" in c for c in rec[p])]

    def count(term: str) -> tuple[int, int, str]:
        a = [p for p in paths if term in p]
        v = [p for p in veh if term in p]
        return len(a), len(v), (a[0] if a else "")

    script = open(RULE_SCRIPT, encoding="utf-8").read()
    needles, rule_line = decoded_needles(script)
    row_json = json.load(open(ROW_JSON, encoding="utf-8"))
    row = next(r for r in row_json["rows"] if r["id"] == "T-FX16")
    md = open(ROW_MD, encoding="utf-8").read()

    ok(len(paths) == 955, f"FX_TABLE.jsonl holds 955 distinct .effc paths ({len(paths)})", str(len(paths)))
    ok(len(veh) == 589, f"589 of them are vehicle-carried ({len(veh)})", str(len(veh)))
    ok(row_json["summary"]["fleet_effc"] == 955 and row_json["summary"]["fleet_vehicle_effc"] == 589,
       "t17_fx.json's own summary agrees (fleet_effc 955, fleet_vehicle_effc 589)")
    ok(needles == ["canon_trail", "shell_trail"],
       f"T-FX16's `match` list in t17_fx.py is {needles}", str(needles))
    ok(rule_line > 0, f"the rule is at t17_fx.py line {rule_line}")
    ok(row["absence"] == {"test": "no_paths", "matches": 0, "candidates": []},
       "t17_fx.json records the omission as no_paths with 0 matches and no candidates",
       json.dumps(row["absence"], sort_keys=True))

    # the row itself must not name the needle - that is the defect being explained
    def row_names(term: str) -> bool:
        return term in json.dumps(row, ensure_ascii=False) or term in md.split("| T-FX16 |")[1].split("\n")[0]
    for term in ("canon_trail", "shell_trail"):
        ok(not row_names(term), f"the T-FX16 row/doc does not name `{term}` (the defect)")
    ok("0 of 955 match over all distinct `.effc` paths" in md,
       "T13_FX.md carries the unqualified proof string for T-FX16")

    counts = {}
    for term, _prov, exp_all, exp_veh in CANDIDATES:
        a, v, first = count(term)
        counts[term] = (a, v, first)
        ok((a, v) == (exp_all, exp_veh),
           f"`{term}` matches {exp_all} of 955 ({exp_veh} vehicle-carried)",
           f"got {a}/{v}")

    union = [p for p in paths if any(t in p for t in needles)]
    ok(len(union) == 0, "the union of the decoded needles is 0 of 955 - the row's count reproduces",
       str(len(union)))
    zeros = [t for t, _p, a, _v in CANDIDATES if a == 0]
    ok(set(needles) <= set(zeros), f"every decoded needle is in the zero set {zeros}")
    ok("trail" in counts and counts["trail"][0] > 0,
       f"the broad word `trail` does not reproduce 0 ({counts['trail'][0]} hits)")

    # ------------------------------------------------------------------ the document
    hit_zero = [t for t in zeros]
    L: list[str] = []
    ap = L.append
    ap("# T-FX16: which search term gives \"0 of 955\"?")
    ap("")
    ap("**Verdict: the term is `canon_trail` plus `shell_trail` - the `match` list of the T-FX16")
    ap("rule in `Tools/scripts/t17_fx.py` line "
       f"{rule_line} - and each needle, and their union, returns exactly 0 of 955.**")
    ap("The row and `T13_FX.md` publish the result without the term, so the claim was not")
    ap("checkable from the document alone; the term was never lost, only left in the generator.")
    ap("")
    ap("**But the 0 is term-specific.** The word `trail` alone returns "
       f"{counts['trail'][0]} of 955 ({counts['trail'][1]} vehicle-carried): JC3 has plenty of")
    ap("trail effects, none of them spelled `canon_trail` or `shell_trail`. A reader who")
    ap("reconstructed the search as `trail` would get a very different number, so the proof line")
    ap("has to name its needles to be worth anything.")
    ap("")
    ap("## Method")
    ap("")
    ap(f"* Pool: the {len(paths)} distinct `.effc` paths in `Research/JC3Grab/FX_TABLE.jsonl`,")
    ap(f"  re-derived with `t17_fx.py`'s own rule; {len(veh)} of them are vehicle-carried (a")
    ap("  container path contains `/jc_vehicles/`). Both counts agree with `t17_fx.json`'s")
    ap("  `summary.fleet_effc` / `fleet_vehicle_effc`.")
    ap("* Test: case-insensitive substring on the full effect path - exactly what the generator")
    ap("  does (`any(m in p for m in rule['match'])`).")
    ap("* The omission's pool is `no_paths`, i.e. all 955, not the 589 subset (`no_vehicle_paths`")
    ap("  is what T-FX13 uses).")
    ap("")
    ap("## Counts per candidate")
    ap("")
    ap("| candidate | where the candidate comes from | matches / 955 | vehicle-carried / 589 | first hit |")
    ap("|---|---|---:|---:|---|")
    for term, prov, _a, _v in CANDIDATES:
        a, v, first = counts[term]
        shown = f"`{os.path.basename(first)}`" if first else "-"
        mark = (" **reproduces**" if term in needles
                else (" - zero too" if a == 0 else ""))
        ap(f"| `{term}` | {prov}{mark} | {a} | {v} | {shown} |")
    ap("")
    ap(f"Candidates returning 0 of 955: " + ", ".join(f"`{t}`" for t in hit_zero) + ".")
    ap("")
    ap("## Reading the table")
    ap("")
    ap("* **The decoded pair is the only one that is also the row's own search.** `canon_trail`")
    ap("  and `shell_trail` are what `t17_fx.py` feeds to the absence test for T-FX16, so the")
    ap("  published \"0 of 955\" is their union's count, reproduced here: 0 paths.")
    ap("* **Zero alone does not identify a term.** `cannon`, `canon_trail`, `shell_trail` and the")
    ap("  T-FX12 control `tracer` all return 0, for unrelated reasons. A bare \"0 of 955\" is")
    ap("  therefore not evidence of anything until the needle is printed beside it.")
    ap("* **The spelling trap is real.** `cannon` (two n) returns 0 while `canon` (one n) returns 1")
    ap("  - `effects/jc_weapons/muzzle_flash/tank_canon_muzzleflash.effc`. The generator chose")
    ap("  the one-n spelling, which is why its muzzle term finds the fleet's tank flash; a search")
    ap("  for `cannon` would report an absence where a file exists.")
    ap("* **What is actually absent is narrow**: no effect path calls itself a cannon or shell")
    ap("  trail. Trails exist (84), missile trails exist (30, T-FX14 keeps one), bullet effects")
    ap("  exist (23), and the bare word `projectile` names one DLC effect. Whether any of those")
    ap("  *is* a cannon-round trail is a different question from what the path is called.")
    ap("* **The row's conclusion is unchanged** by naming the term: with `canon_trail` +")
    ap("  `shell_trail` the count is still 0, so the named omission still holds on its own terms.")
    ap("  What changes is that the claim can now be re-run by a reader.")
    ap("")
    ap("## The row as it stands, and the one-line repair")
    ap("")
    ap("`t17_fx.json` records the T-FX16 omission as:")
    ap("")
    ap("```json")
    ap(json.dumps(row["absence"], indent=1, sort_keys=True))
    ap("```")
    ap("")
    ap("`T13_FX.md` §4 prints it as \"0 of 955 match over all distinct `.effc` paths\" with no")
    ap("needle. A proof line that names its term would read, without any other change:")
    ap("")
    ap("> 0 of 955 match `canon_trail` or `shell_trail` over all distinct `.effc` paths")
    ap("  (`t17_fx.py` T-FX16 `match`)")
    ap("")
    ap("That is proposed here as text only. **No row, ledger, document or JSON file was edited** -")
    ap("`T13_FX.md`, `t17_fx.json` and `T_ROWS.jsonl` are opened read-only.")
    ap("")
    ap("## What this does not settle")
    ap("")
    ap("* **Whether a JC3 cannon-round trail exists under another name.** The paths carry no")
    ap("  such name, but the 84 `trail` effects, 30 `missile` effects and 23 `bullet` effects were")
    ap("  not opened one by one here; deciding that one of them *is* the cannon round trail is")
    ap("  UNKNOWN, and belongs to a content read, not a name search.")
    ap("* **Whether the BmAK side needs the trail at all**: the row's answer (the round shows as")
    ap("  a tracer texture, T-FX12) rests on `WEAPONS.md` §6 and is not re-tested here.")
    ap("* **Runtime**: nothing was launched; the test ban stays.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: the 955/589 pools and every count, the T-FX16 `match` list and its line number,")
    ap("the row's `absence` record, the `T13_FX.md` proof string. Derived: the reconstruction of")
    ap("which candidate the row means, the reading of the zero set, the proposed proof line.")
    ap("UNKNOWN: everything under \"What this does not settle\".")
    ap("")
    text = "\n".join(L)

    failed = [c for c in checks if not c["ok"]]
    for c in checks:
        print(f"{'PASS' if c['ok'] else 'FAIL'} {c['oracle']}"
              + (f" [{c['detail']}]" if c["detail"] and not c["ok"] else ""))
    print(f"{len(checks) - len(failed)}/{len(checks)} oracles pass")
    if failed:
        return 1
    if write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT).replace(os.sep, '/')}")
        return 0
    current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    if current != text:
        for line in difflib.unified_diff(current.splitlines(), text.splitlines(),
                                         "on-disk", "recomputed", lineterm="", n=1):
            print(line)
        print("FAIL document differs from the regenerated text")
        return 1
    print("PASS document: FX16_TERM.md matches the regenerated text")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write FX16_TERM.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
