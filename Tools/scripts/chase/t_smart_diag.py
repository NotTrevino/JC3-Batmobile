"""t_smart_diag.py - re-derive the smart-search recall diagnosis from the stored runs.

Reads the calibration case list and both judge runs (outside the repo, the
paths the report names), classifies every case, and re-tests the route fix
against MODES.md. Read-only; no model call.

Usage:
  python Tools/scripts/chase/t_smart_diag.py --check
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CH = r"E:/Modding/_gamedata/BmAKgrab/chase"
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "smart-search-recall-diagnosis.md")
MODES = os.path.join(ROOT, "Research", "BatmobileGrab", "MODES.md")
RUNS = {"qwen": "51c8dd3c_v1search", "jeb": "jeb_340c7b55_v1search"}

GAME = ("sim_cdo", "chase2_defaults", "g1_chase_native", "svehicle_cdo",
        "value_cdo", "camera_cdo", "wheel_cdo", "chase2_native")
PROMPT_WORDS = ("analysis record", "offset table", "metadata", "not a game file")


def src_class(src: str) -> str:
    s = src.lower()
    if any(g in s for g in GAME):
        return "game"
    if any(t in s for t in ("calib.jsonl", "verify", "namescan", "pkg_", "chase2_04")):
        return "tool"
    if s.startswith("exe "):
        return "exe"
    return "other"


def main() -> int:
    ok: list[str] = []
    fails: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        (ok if cond else fails).append(f"{name}{(': ' + detail) if detail else ''}")

    calib = [json.loads(l) for l in open(os.path.join(CH, "calib.jsonl"), encoding="utf-8") if l.strip()]
    check("38 cases", len(calib) == 38, str(len(calib)))
    check("20 positives", sum(c["kind"] == "positive" for c in calib) == 20)
    check("8 found", sum(c["kind"] == "found" for c in calib) == 8)
    check("10 negatives", sum(c["kind"] == "negative" for c in calib) == 10)

    counts = {}
    for judge, run in RUNS.items():
        cls = {"SEARCH": 0, "WINDOW": 0, "JUDGE": 0, "PROMPT": 0, "ok": 0}
        cut_verdicts = allcut = somecut = nocut = 0
        for c in calib:
            d = json.load(open(os.path.join(CH, "calib_runs", run, c["id"] + ".json"), encoding="utf-8"))
            vs = d.get("verdicts", [])
            found = any(v.get("found") is True for v in vs)
            cuts = [v for v in vs if any("2048" in w for w in (v.get("warnings") or []))]
            cut_verdicts += len(cuts)
            if vs and len(cuts) == len(vs):
                allcut += 1
            elif cuts:
                somecut += 1
            elif vs:
                nocut += 1
            kinds = [src_class(v.get("source", "")) for v in vs]
            if c["kind"] == "negative":
                cls["ok" if not found else "JUDGE"] += 1
                continue
            if found:
                cls["ok"] += 1
            elif "game" not in kinds:
                cls["SEARCH"] += 1
            elif judge == "jeb":
                cls["JUDGE"] += 1
            else:
                why = " ".join(v.get("why", "").lower() for v in vs if not v.get("found"))
                cls["PROMPT" if any(w in why for w in PROMPT_WORDS) else "JUDGE"] += 1
        counts[judge] = cls
        check(f"{judge} SEARCH 23", cls["SEARCH"] == 23, str(cls))
        check(f"{judge} WINDOW 0", cls["WINDOW"] == 0)
        check(f"{judge} total 38", sum(cls.values()) == 38, str(sum(cls.values())))
        if judge == "qwen":
            check("qwen JUDGE 1 / PROMPT 3", (cls["JUDGE"], cls["PROMPT"]) == (1, 3), str(cls))
            check("qwen ok 11", cls["ok"] == 11)
        else:
            check("jeb JUDGE 5 / PROMPT 0", (cls["JUDGE"], cls["PROMPT"]) == (5, 0), str(cls))
            check("jeb ok 10", cls["ok"] == 10)
            check("jeb cut verdicts 118", cut_verdicts == 118, str(cut_verdicts))
            check("jeb all-cut 12 / some 22 / none 4",
                  (allcut, somecut, nocut) == (12, 22, 4), f"{allcut}/{somecut}/{nocut}")

    modes = open(MODES, encoding="utf-8", errors="replace").read().splitlines()

    def row(member: str) -> str:
        return next((ln for ln in modes if "`" + member + "`" in ln), "")

    rec = set()
    for c in calib:
        if c["kind"] == "negative":
            continue
        r = row(c["member"])
        if r and re.search(re.escape(str(c["known"]).lstrip("-")) + r"(?![0-9])", r):
            rec.add(c["id"])
    check("MODES rows 19", len(rec) == 19, str(sorted(rec)))
    union = rec | {"F18", "F33", "F35"}
    check("route union 22", len(union) == 22, str(len(union)))
    check("positive route 19/20", len([x for x in union if x.startswith("P")]) == 19)

    md = open(REPORT, encoding="utf-8").read()
    for token in ("23", "0/10", "22/28", "1/28", "WinError 10061", "118", "12"):
        check(f"report quotes {token}", token in md)
    for head in ("(a) SEARCH", "(b) WINDOW", "(c) JUDGE", "(d) PROMPT"):
        check(f"report class {head}", head in md)

    for line in ok:
        print("PASS", line)
    for line in fails:
        print("FAIL", line)
    print(f"\n{len(ok)} passed, {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
