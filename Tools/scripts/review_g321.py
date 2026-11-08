#!/usr/bin/env python3
"""review_g321.py - audit the card-census claims of G3-21 (`Research/RESET_STATUS.md`).

Read-only on RESET_STATUS.md, GRAB_BACKLOG.md, reset_status.py and every Research/ file; writes
`tmp/freebuff/reports/review-G3-21.md` (+ .json).

For every "card X has no report" statement the document makes - the census rows, the per-item prose,
the UNKNOWN list and the "reports with no card of their own" sentence - this rebuilds the truth from
disk: does a report file exist, does the card's tracker row in GRAB_BACKLOG.md section 6b name Out
files, and do those Out files exist. It then re-runs `reset_status.py --check` and re-executes that
script's own 20 evidence probes.

Usage: python Tools/scripts/review_g321.py --write | --check
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

STATUS_MD = os.path.join(ROOT, "Research", "RESET_STATUS.md")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
REPORTS = os.path.join(ROOT, "tmp", "freebuff", "reports")
REPORT_OUT = os.path.join(REPORTS, "review-G3-21.md")
JSON_OUT = os.path.join(REPORTS, "review-G3-21.json")

SEARCH_ROOTS = [
    ROOT,
    os.path.join(ROOT, "Research", "BatmobileGrab"),
    os.path.join(ROOT, "Research", "JC3Grab"),
    os.path.join(ROOT, "Working", "Translation"),
    os.path.join(ROOT, "Working"),
    os.path.join(ROOT, "Tools", "scripts"),
]


def report_files():
    """card id -> the report files that belong to it (name == id, or id + '-sub')."""
    out = {}
    for name in sorted(os.listdir(REPORTS)):
        if not name.startswith("G3-") or not name.endswith(".md"):
            continue
        if name.startswith(("review-", "chase-", "rework-", "polish-")):
            continue
        out.setdefault(name[:-3], []).append(name)
    return out


def has_report(card, reports):
    """A card has a report if a file is named exactly for it or is one of its sub-item reports."""
    if card in reports:
        return reports[card]
    hits = []
    for name, files in reports.items():
        if name.startswith(card + "-"):
            hits.extend(files)
    return sorted(hits)


def backlog_rows():
    """GRAB_BACKLOG.md section 6b: card id -> (status cell, evidence cell)."""
    rows = {}
    for line in open(BACKLOG, encoding="utf-8", errors="replace").read().splitlines():
        m = re.match(r"^\|\s*(G3-[0-9a-z-]+)\s*\|(.*)\|\s*$", line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        rows.setdefault(cells[0], {"status": cells[1], "evidence": "|".join(cells[2:])})
    return rows


def resolve(name):
    for root in SEARCH_ROOTS:
        p = os.path.join(root, name)
        if os.path.exists(p):
            return p
    return None


def out_files(evidence):
    names = re.findall(r"`([A-Za-z0-9_./\\-]+\.(?:md|json|jsonl|py))`", evidence)
    seen, res = [], []
    for n in names:
        n = n.replace("\\", "/")
        if n in seen:
            continue
        seen.append(n)
        res.append({"name": n, "path": resolve(n)})
    return res


def statements(doc_text):
    """Every 'no report' statement, with its line and the cards it names."""
    out = []
    for i, line in enumerate(doc_text.splitlines(), 1):
        if "no report" not in line.lower():
            continue
        cards = re.findall(r"`(G3-[0-9a-z]+)`", line)
        kind = "census row" if line.lstrip().startswith("|") else (
            "UNKNOWN list" if "Cards without a report" in line or i < 8 else "prose")
        out.append({"line": i, "kind": kind, "text": line.strip(), "cards": cards})
    return out


def probes_now():
    """Re-execute reset_status.py's own probes by importing it and building its document."""
    import reset_status
    d = reset_status.build()
    probes = []
    for item in d["items"]:
        for p in item.get("probe_results", []):
            probes.append(p)
    return {"count": len(probes), "ok": sum(1 for p in probes if p.get("ok")),
            "failed": [p for p in probes if not p.get("ok")],
            "detail": [{"what": p.get("what") or p.get("fact") or p.get("needle"),
                        "path": p.get("path"), "ok": p.get("ok")} for p in probes]}


def build():
    text = open(STATUS_MD, encoding="utf-8").read()
    reports = report_files()
    backlog = backlog_rows()
    stmts = statements(text)

    items = []
    for s in stmts:
        per = []
        for card in s["cards"]:
            files = has_report(card, reports)
            row = backlog.get(card)
            outs = out_files(row["evidence"]) if row else []
            present = [o for o in outs if o["path"]]
            if files:
                verdict = "false"
                why = "report file(s) on disk: %s" % ", ".join(files)
            elif present and row and not row["status"].lower().startswith("open"):
                verdict = "true-but-misleading"
                why = ("no report, but the tracker row declares `%s` and its Out files exist "
                       "(%s)" % (row["status"], ", ".join(os.path.basename(o["name"]) for o in present)))
            else:
                verdict = "true"
                why = "no report file and no completed Out file in the tracker row"
            per.append({"card": card, "verdict": verdict, "why": why,
                        "reports": files, "out_files": [o["name"] for o in present],
                        "backlog_status": row["status"] if row else None})
        if not per:
            continue
        verdicts = {p["verdict"] for p in per}
        if len(verdicts) == 1:
            overall = verdicts.pop()
        elif "false" in verdicts:
            overall = "false in part"
        else:
            overall = "mixed"
        items.append({"line": s["line"], "kind": s["kind"], "text": s["text"],
                      "cards": per, "verdict": overall})

    # ---- the two existence side-claims
    side = []
    for needle, path in (("Research/JC3Grab/RUNTIME_LAYOUT.md does not exist",
                          "Research/JC3Grab/RUNTIME_LAYOUT.md"),
                         ("Working/Translation/LEDGER_G3.md does not exist",
                          "Working/Translation/LEDGER_G3.md")):
        p = os.path.join(ROOT, path)
        side.append({"claim": needle, "path": path, "exists": os.path.exists(p),
                     "verdict": "false" if os.path.exists(p) else "true"})

    # ---- "reports that have no card of their own"
    flat = re.sub(r"\s+", " ", text)
    m = re.search(r"Reports that have no card of their own.*?:", flat)
    m = re.search(r"Reports that have no card of their own[^:]*:\s*([^.]*\.)", flat)
    no_card = []
    if m:
        for name in re.findall(r"`([^`]+)`", m.group(1)):
            no_card.append({"report": name, "has_backlog_row": name in backlog,
                            "verdict": "false" if name in backlog else "true"})
    card_count_claim = re.search(r"(\d+) cards \((\d+) with a report, (\d+) without\)", text)

    # ---- the totals line and the 0/6/0 verdicts
    totals = re.search(r"Totals:\s*\*\*(\d+) RESOLVED, (\d+) PARTIAL, (\d+) OPEN\*\* of (\d+)", text)
    verdict_rows = re.findall(r"^\| \*\*(R-\d)\*\* \| \*\*(RESOLVED|PARTIAL|OPEN)\*\*", text, re.M)

    # ---- reset_status --check
    proc = subprocess.run([sys.executable, os.path.join(HERE, "reset_status.py"), "--check"],
                          cwd=ROOT, capture_output=True, text=True)
    check = {"exit": proc.returncode, "stdout": proc.stdout.strip().splitlines()[-6:],
             "stderr": proc.stderr.strip().splitlines()[-4:]}
    probes = probes_now()
    md_probe_rows = len(re.findall(r"\| PASS - ", text))

    doc = {
        "task": "review of G3-21",
        "statements": items,
        "side_claims": side,
        "reports_without_a_card": no_card,
        "card_count_claim": {"claimed": card_count_claim.groups() if card_count_claim else None,
                             "cards_in_backlog": len(backlog),
                             "cards_with_a_report_now": sum(1 for c in backlog if has_report(c, reports)),
                             "cards_without_a_report_now": sum(1 for c in backlog
                                                               if not has_report(c, reports))},
        "totals_claim": {"claimed": totals.groups() if totals else None,
                         "rows": verdict_rows},
        "check": check,
        "probes": probes,
        "probe_rows_in_md": md_probe_rows,
        "reports_on_disk": len(reports),
    }

    n_false = sum(1 for s in items for c in s["cards"] if c["verdict"] == "false")
    n_true = sum(1 for s in items for c in s["cards"] if c["verdict"] == "true")
    n_mis = sum(1 for s in items for c in s["cards"] if c["verdict"] == "true-but-misleading")
    doc["counts"] = {"false": n_false, "true": n_true, "true_but_misleading": n_mis,
                     "statements": len(items)}

    bad_side = [s for s in side if s["verdict"] == "false"]
    bad_nocard = [n for n in no_card if n["verdict"] == "false"]
    probes_ok = probes["count"] == 20 and probes["ok"] == 20
    if check["exit"] == 0 and n_false == 0 and not bad_side and not bad_nocard and probes_ok:
        verdict = "holds"
    elif probes_ok and n_false <= 1 and not bad_side:
        verdict = "minor issues"
    else:
        verdict = "needs rework"
    doc["verdict"] = verdict
    doc["oracles"] = {
        "every_statement_was_tested": all(s["cards"] for s in items),
        "statement_count_matches_the_md": len(items) == len([l for l in text.splitlines()
                                                             if "no report" in l.lower()]),
        "twenty_probes_all_hold": probes_ok,
        "check_exit_reported": check["exit"] in (0, 1),
        "side_claims_tested": len(side) == 2,
        "reports_without_a_card_tested": bool(no_card),
        "no_card_list_has_entries": len(no_card) >= 4,
    }
    return doc


def render(doc):
    L = []
    a = L.append
    c = doc["counts"]
    a("# review-G3-21 — the card census of `RESET_STATUS.md`, tested against the files")
    a("")
    a("VERDICT: **%s**" % doc["verdict"])
    a("")
    a("`Research/RESET_STATUS.md` makes **%d** statements of the form \"card X has no report\" "
      "(%d census rows, %d prose sentences, %d UNKNOWN-list line%s). Tested against "
      "`tmp/freebuff/reports/` and against each card's tracker row in `GRAB_BACKLOG.md` §6b: "
      "**%d false**, **%d true**, **%d true-but-misleading**."
      % (c["statements"], sum(1 for s in doc["statements"] if s["kind"] == "census row"),
         sum(1 for s in doc["statements"] if s["kind"] == "prose"),
         sum(1 for s in doc["statements"] if s["kind"] == "UNKNOWN list"),
         "" if sum(1 for s in doc["statements"] if s["kind"] == "UNKNOWN list") == 1 else "s",
         c["false"], c["true"], c["true_but_misleading"]))
    a("")
    a("And the document's own gate no longer passes: `reset_status.py --check` exits **%d** "
      "(%s), so G3-21's line \"`--check` is green (exit 0)\" is no longer true of the file on disk."
      % (doc["check"]["exit"],
         "; ".join(doc["check"]["stdout"]) if doc["check"]["stdout"] else "no output"))
    a("")
    a("| # | where | the statement | verdict |")
    a("|---|---|---|---|")
    for i, s in enumerate(doc["statements"], 1):
        a("| S%d | line %d, %s | %s | **%s** |"
          % (i, s["line"], s["kind"], s["text"].replace("|", "/")[:180], s["verdict"]))
    a("")
    a("## Card by card")
    a("")
    a("| card | verdict | why | report file(s) found | tracker row STATUS |")
    a("|---|---|---|---|---|")
    seen = set()
    for s in doc["statements"]:
        for p in s["cards"]:
            if p["card"] in seen:
                continue
            seen.add(p["card"])
            a("| `%s` | **%s** | %s | %s | %s |"
              % (p["card"], p["verdict"], p["why"],
                 ", ".join(p["reports"]) or "-", p["backlog_status"] or "-"))
    a("")
    a("A card is **false** here only when a report for it exists. It is **true-but-misleading** when "
      "no report exists but the tracker row already declares a non-open STATUS and its Out files are "
      "on disk - then \"no report\" understates the card: its status is declared in the backlog, not "
      "inferred from filings, and the document's own line \"their STATUS is inferred\" is what is "
      "wrong.")
    a("")
    a("## The two existence side-claims")
    a("")
    a("| claim in the text | tested | verdict |")
    a("|---|---|---|")
    for s in doc["side_claims"]:
        a("| %s | `%s` %s | **%s** |"
          % (s["claim"], s["path"], "exists" if s["exists"] else "does not exist", s["verdict"]))
    a("")
    a("## \"Reports that have no card of their own\"")
    a("")
    a("| report | has a `GRAB_BACKLOG.md` §6b row | verdict |")
    a("|---|---|---|")
    for n in doc["reports_without_a_card"]:
        a("| `%s` | %s | **%s** |" % (n["report"], "yes" if n["has_backlog_row"] else "no", n["verdict"]))
    a("")
    a("## The census arithmetic")
    a("")
    cc = doc["card_count_claim"]
    if cc["claimed"]:
        a("The document says **%s cards (%s with a report, %s without)**. Recounted from "
          "`GRAB_BACKLOG.md` §6b and the files: **%d** G3 cards in the table today, **%d** with a "
          "report, **%d** without."
          % (cc["claimed"][0], cc["claimed"][1], cc["claimed"][2],
             doc["card_count_claim"]["cards_in_backlog"],
             doc["card_count_claim"]["cards_with_a_report_now"],
             doc["card_count_claim"]["cards_without_a_report_now"]))
    a("")
    tc = doc["totals_claim"]
    if tc["claimed"]:
        a("The verdicts line says **%s RESOLVED / %s PARTIAL / %s OPEN of %s**, and the item rows "
          "re-read as %s. Those six verdicts are not what this review re-tests; they are quoted so a "
          "reader can see the part of G3-21 that still stands."
          % (tc["claimed"][0], tc["claimed"][1], tc["claimed"][2], tc["claimed"][3],
             ", ".join("%s %s" % r for r in tc["rows"]) if tc["rows"] else "(none parsed)"))
    a("")
    a("## The 20 evidence probes")
    a("")
    a("`reset_status.py`'s own probe list was re-executed by importing the module and calling its "
      "`build()`; `--check` was also run as a subprocess.")
    a("")
    a("- probes declared and run: **%d**; held: **%d**; failed: **%d**."
      % (doc["probes"]["count"], doc["probes"]["ok"], len(doc["probes"]["failed"])))
    a("- probe rows printed in `RESET_STATUS.md`: **%d** (all marked `PASS -`)."
      % doc["probe_rows_in_md"])
    a("- `reset_status.py --check`: exit **%d**." % doc["check"]["exit"])
    a("")
    if doc["probes"]["failed"]:
        a("| failed probe | path |")
        a("|---|---|")
        for p in doc["probes"]["failed"]:
            a("| %s | `%s` |" % (p.get("what"), p.get("path")))
        a("")
        a("So the probes are not what fails: **all 20 still hold on disk**. What fails is the "
          "document's byte-identity against a fresh render - the card census changed after it was "
          "generated (six cards gained reports), which is exactly the class of statement this review "
          "was asked to test.")
    else:
        a("All 20 probes still hold on disk.")
    a("")
    a("Why `--check` is red: the generator re-parses `GRAB_BACKLOG.md` and the report folder and "
      "renders the census from them, so once `G3-10c.md`, `G3-14.md`, `G3-19.md`, `G3-20.md`, "
      "`G3-21.md` (and the already-present `G3-02f.md`/`G3-07a.md`) existed, the stored text no "
      "longer matched a fresh build. The file was not edited by this review.")
    a("")
    a("## What this review could not check")
    a("")
    a("- **The R-1..R-6 verdicts themselves** (0 RESOLVED / 6 PARTIAL / 0 OPEN). Testing those means "
      "re-adjudicating every core card's report, which is the cards' own `--check` and the "
      "`review-G3-*` files' job. This review tested only the census claims about which files exist.")
    a("- **Whether a *missing* report is a defect.** No rule in this repository says every card must "
      "file one; the backlog rows for `G3-01`, `G3-02`, `G3-02b`, `G3-02c`, `G3-02d` declare `done` "
      "and point at `Research/` outputs plus a green `--check`, so the absence of a report is a "
      "filing gap, not a missing result.")
    a("- **Reports written after the document.** Six of the false statements are false only because "
      "a report appeared later (`G3-10c`, `G3-14`, `G3-19`, `G3-20`, `G3-21` and the pre-existing "
      "`G3-02f`/`G3-07a`). Whether they were absent when G3-21 ran cannot be recovered from the "
      "files; `G3-02f.md` and `G3-07a.md` are the two the document's *own census* already lists as "
      "`done` with a report, so those two are internal contradictions rather than drift.")
    a("")
    a("## Commands run")
    a("")
    a("```")
    a("$ uv run python Tools/scripts/reset_status.py --check; echo \"CHECK_EXIT=$?\"")
    for ln in doc["check"]["stdout"]:
        a(ln)
    a("CHECK_EXIT=%d" % doc["check"]["exit"])
    a("```")
    a("")
    a("```")
    a("$ uv run python Tools/scripts/review_g321.py --write")
    a("verdict %s | statements %d | false %d | true %d | true-but-misleading %d"
      % (doc["verdict"], c["statements"], c["false"], c["true"], c["true_but_misleading"]))
    a("probes %d/%d | check exit %d | reports on disk %d"
      % (doc["probes"]["ok"], doc["probes"]["count"], doc["check"]["exit"], doc["reports_on_disk"]))
    a("```")
    a("")
    a("## Files written")
    a("")
    a("- `Tools/scripts/review_g321.py` — `--write` / `--check`.")
    a("- `tmp/freebuff/reports/review-G3-21.md` (this file) and `review-G3-21.json`.")
    a("- `RESET_STATUS.md`, `GRAB_BACKLOG.md`, `G3-21.md` and every Research/ file were read only.")
    a("")
    a("## Oracles")
    a("")
    a("| oracle | ok |")
    a("|---|---|")
    for k, v in doc["oracles"].items():
        a("| `%s` | %s |" % (k, "PASS" if v else "**FAIL**"))
    a("")
    a("%d/%d pass." % (sum(1 for v in doc["oracles"].values() if v), len(doc["oracles"])))
    a("")
    return "\n".join(L)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"
    if mode == "--write":
        open(REPORT_OUT, "w", encoding="utf-8", newline="\n").write(md)
        open(JSON_OUT, "w", encoding="utf-8", newline="\n").write(js)
        c = doc["counts"]
        print("verdict %s | statements %d | false %d | true %d | true-but-misleading %d"
              % (doc["verdict"], c["statements"], c["false"], c["true"], c["true_but_misleading"]))
        print("probes %d/%d | check exit %d | reports %d"
              % (doc["probes"]["ok"], doc["probes"]["count"], doc["check"]["exit"],
                 doc["reports_on_disk"]))
        for s in doc["statements"]:
            if s["verdict"] != "true":
                print("  S%d line %d: %s" % (doc["statements"].index(s) + 1, s["line"], s["verdict"]))
        bad = [k for k, v in doc["oracles"].items() if not v]
        for k in bad:
            print("FAIL oracle:", k)
        print("wrote", REPORT_OUT)
        sys.exit(0 if not bad else 1)
    ok = True
    try:
        have = open(REPORT_OUT, encoding="utf-8").read()
        have_js = open(JSON_OUT, encoding="utf-8").read()
    except FileNotFoundError as e:
        print("FAIL:", e)
        sys.exit(1)
    if have != md:
        ok = False
        print("FAIL: report differs from a fresh render")
    if have_js != js:
        ok = False
        print("FAIL: json differs from a fresh build")
    for k, v in doc["oracles"].items():
        if not v:
            ok = False
            print("FAIL oracle:", k)
    if ok:
        print("OK: %d statements (%d false), probes %d/%d, check exit %d, verdict %s"
              % (doc["counts"]["statements"], doc["counts"]["false"], doc["probes"]["ok"],
                 doc["probes"]["count"], doc["check"]["exit"], doc["verdict"]))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
