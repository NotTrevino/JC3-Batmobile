#!/usr/bin/env python
"""reset_delta.py - what the reports newer than `RESET_STATUS.md` do to R-1..R-6 (G3-21e).

The baseline is `Research/RESET_STATUS.md`: its mtime is the cutoff, and its own tables are the
only mapping used from a report to an R item - a report is attached to R-n when the card family
in its file name is a card that baseline lists under R-n (core or supporting), with `review-`,
`rework-`, `audit-`, `chase-`, `polish-` and `reverify-` prefixes stripped first.  A report whose
name matches no such card is **not** attached to anything: it is printed in a separate list, so
nothing is guessed.

For every attached report the tool quotes its `STATUS:` line and derives two things from the
report's own text, never from general knowledge:

  * **opened UNKNOWNs** - the bullets of the report's own UNKNOWN section that do not match a
    baseline UNKNOWN of that item (content-word coverage < 0.6);
  * **closed UNKNOWNs** - a baseline UNKNOWN of that item whose content words (coverage >= 0.6)
    appear in the report's *body*, i.e. outside its own UNKNOWN section, and only when the report
    is evidence at all.

Two operator corrections of 2026-11-05 are applied and printed:

  1. the **EM ejection part** open item is dropped - only the eject mechanic matters, and its
     mapping to JC3 is task G3-08b;
  2. a **blocked** report (its `STATUS:` says blocked, its gate was missing) counts as **no
     evidence at all** - it closes nothing, and its UNKNOWNs are listed as "reported while
     blocked", not as opened evidence.

`reset_status.py` is not run or copied and `RESET_STATUS.md` is not touched.

Usage:
    uv run python Tools/scripts/reset_delta.py --write
    uv run python Tools/scripts/reset_delta.py --check
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REPORTS = os.path.join(ROOT, "tmp", "freebuff", "reports")
BASELINE = os.path.join(ROOT, "Research", "RESET_STATUS.md")
OUT_MD = os.path.join(ROOT, "Research", "RESET_DELTA.md")
OUT_JSON = os.path.join(ROOT, "Research", "RESET_DELTA.json")

PREFIXES = ("review-", "rework-", "audit-", "chase-", "polish-", "reverify-")
MIN_COVERAGE = 0.5
STOP = set("""a an and are as at be been but by can could do does for from has have how if in into
is it its no not of on or that the their them then there these they this those to was were what
when where which who why will with would unknown unknowns report card status done partial""".split())
DROPPED_TOPIC = ("em ejection", "ejection part", "em eject")


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9_+.-]*", text.lower())
            if len(w) > 3 and w not in STOP}


def coverage(target: str, pool: set[str]) -> float:
    w = words(target)
    return len(w & pool) / len(w) if w else 0.0


def dropped(text: str) -> bool:
    low = text.lower()
    return any(t in low for t in DROPPED_TOPIC)


# ---------------------------------------------------------------- baseline
def parse_baseline() -> dict:
    text = open(BASELINE, encoding="utf-8").read()
    mtime = os.path.getmtime(BASELINE)
    items = {}
    cur = None
    mode = None
    for line in text.splitlines():
        m = re.match(r"^## (R-\d)\s+[—-]\s+(\w+)", line)
        if m:
            cur = m.group(1)
            items[cur] = {"verdict": m.group(2), "question": "", "cards": {},
                          "unknowns": [], "remains": []}
            mode = "head"
            continue
        if cur is None:
            continue
        if line.startswith("## "):
            cur = None
            continue
        if line.startswith("### "):
            head = line[4:].strip().lower()
            mode = "unknowns" if head.startswith("unknown") else (
                "remains" if head.startswith("what remains") else None)
            continue
        if mode == "head":
            q = re.match(r"^>\s*(.+)$", line.strip())
            if q:
                items[cur]["question"] = q.group(1).strip()
            card = re.match(r"^\|\s*`([A-Za-z0-9.\-]+)`\s*(\(supporting\))?\s*\|", line)
            if card:
                items[cur]["cards"][card.group(1)] = {"supporting": bool(card.group(2)),
                                                      "baseline": True}
        elif mode == "unknowns" and line.strip().startswith(("* ", "- ")):
            items[cur]["unknowns"].append(line.strip("* -").strip())
        elif mode == "remains" and line.strip().startswith(("* ", "- ")):
            items[cur]["remains"].append(line.strip("* -").strip())
    return {"path": os.path.relpath(BASELINE, ROOT).replace("\\", "/"), "mtime": mtime,
            "mtime_iso": dt.datetime.fromtimestamp(mtime).isoformat(timespec="seconds"),
            "sha256_16": hashlib.sha256(text.encode()).hexdigest()[:16],
            "items": items}


def family(card: str) -> str:
    """The card family: the first two hyphen groups without a trailing letter run.

    So `G3-10b`, `G3-10k`, `review-G3-10h` and `G3-01b-boxes-u2` are `g3-10`, `g3-10`, `g3-10`
    and `g3-01`; `T-WLD11` and `B-10d` are `t-wld11` and `b-10` (neither is an R card).
    """
    parts = card.lower().split("-")
    if len(parts) > 1:
        parts[1] = re.sub(r"[a-z]+$", "", parts[1])
    return "-".join(parts[:2])


def card_index(base: dict) -> tuple[dict, dict]:
    """(card -> (R, supporting), family -> {R: supporting}); longest card name wins."""
    idx, fam = {}, {}
    for rid, item in base["items"].items():
        for card, meta in item["cards"].items():
            if card not in idx or (idx[card][1] and not meta["supporting"]):
                idx[card] = (rid, meta["supporting"])
            if meta["supporting"]:
                fam.setdefault(family(card), {}).setdefault(rid, False)
            else:
                fam.setdefault(family(card), {}).setdefault(rid, True)
                fam[family(card)][rid] = False if fam[family(card)].get(rid) is False else True
    return idx, fam


def attach(name: str, idx: dict, fam: dict) -> tuple:
    """(R, supporting, how) for a report, or (None, None, reason) - never a guess."""
    stem = name[:-3] if name.lower().endswith(".md") else name
    low = stem.lower()
    for p in PREFIXES:
        if low.startswith(p):
            low = low[len(p):]
            break
    for card in sorted(idx, key=len, reverse=True):
        c = card.lower()
        if low == c or (low.startswith(c) and not low[len(c)].isalnum()):
            return idx[card][0], idx[card][1], f"card `{card}`"
    f = family(low.split(".")[0])          # G3-10k -> g3-10
    hits = fam.get(f) or {}
    if len(hits) == 1:
        rid = next(iter(hits))
        return rid, hits[rid], f"card family `{f}`"
    if len(hits) > 1:
        return None, None, f"card family `{f}` maps to several items ({', '.join(sorted(hits))})"
    return None, None, f"no card family `{f}` in the baseline tables"


# ---------------------------------------------------------------- a report
def status_of(text: str) -> tuple[str, str]:
    for line in text.splitlines():
        s = line.strip().lstrip("#*-> ").strip()
        if s.upper().startswith("STATUS:"):
            return s, s.split(":", 1)[1].strip()
    return "", ""


def kind(status_tail: str) -> str:
    low = status_tail.lower()
    for k in ("blocked", "done", "partial", "unknown", "deferred", "superseded"):
        if low.startswith(k) or low.startswith("**" + k):
            return k
    return "other"


def unknown_section(text: str) -> tuple[list[str], str]:
    """(bullets of the report's own UNKNOWN section, the body with that section removed)."""
    lines = text.splitlines()
    start = end = None
    for i, line in enumerate(lines):
        if re.match(r"^#+\s*.*\bunknown", line.strip(), re.I):
            start = i
            level = len(line) - len(line.lstrip("#"))
            for j in range(i + 1, len(lines)):
                m = re.match(r"^(#+)\s", lines[j])
                if m and len(m.group(1)) <= level:
                    end = j
                    break
            end = end or len(lines)
            break
    if start is None:
        return [], text
    bullets = []
    for line in lines[start:end]:
        s = line.strip()
        if s.startswith(("* ", "- ")):
            bullets.append(s[2:].strip().lstrip("`").strip())
        elif s and bullets and not s.startswith("#"):
            bullets[-1] += " " + s            # a wrapped bullet
    return bullets, "\n".join(lines[:start] + lines[end:])


def scan() -> dict:
    base = parse_baseline()
    idx, fam = card_index(base)
    cutoff = base["mtime"]
    files = []
    for name in sorted(os.listdir(REPORTS)):
        p = os.path.join(REPORTS, name)
        if not os.path.isfile(p) or not name.lower().endswith(".md"):
            continue
        files.append({"name": name, "mtime": os.path.getmtime(p),
                      "path": os.path.relpath(p, ROOT).replace("\\", "/")})
    newer = [f for f in files if f["mtime"] > cutoff]

    rows, unattached = [], []
    for f in newer:
        text = open(os.path.join(REPORTS, f["name"]), encoding="utf-8", errors="replace").read()
        line, tail = status_of(text)
        k = kind(tail)
        evidence = k in ("done", "partial")
        bullets, body = unknown_section(text)
        rid, supporting, how = attach(f["name"], idx, fam)
        rec = {"report": f["name"], "path": f["path"],
               "mtime": dt.datetime.fromtimestamp(f["mtime"]).isoformat(timespec="seconds"),
               "status_line": line, "status": k, "evidence": evidence,
               "blocked": k == "blocked",
               "unknowns": [b for b in bullets if not dropped(b)],
               "dropped_unknowns": [b for b in bullets if dropped(b)]}
        if rid is None:
            unattached.append({**rec, "why": how})
            continue
        item = base["items"][rid]
        pool = words(body)
        still_pool = words(" ".join(rec["unknowns"]))
        closed, closed_left = [], []
        for u in item["unknowns"]:
            if dropped(u):
                continue
            c = coverage(u, pool)
            restated = coverage(u, still_pool)
            entry = {"baseline": u, "coverage": round(c, 2),
                     "restated_unknown": round(restated, 2)}
            # a report that still lists the same unknown has not closed it, however much of its
            # body happens to share words with the baseline sentence
            if c >= MIN_COVERAGE and evidence and restated < MIN_COVERAGE:
                closed.append(entry)
            else:
                closed_left.append(entry)
        baseline_pool = " ".join(item["unknowns"]).lower()
        opened = [u for u in rec["unknowns"] if coverage(u, words(baseline_pool)) < MIN_COVERAGE]
        kept = [u for u in rec["unknowns"] if u not in opened]
        rows.append({**rec, "item": rid, "supporting": supporting, "how": how,
                     "closed": closed, "not_closed": closed_left,
                     "opened": opened, "matched_baseline_unknown": kept,
                     "question": item["question"], "verdict_before": item["verdict"]})

    rows.sort(key=lambda r: (r["item"], r["mtime"]))
    unattached.sort(key=lambda r: r["report"])
    doc = {
        "schema": 1,
        "card": "G3-21e",
        "generator": "Tools/scripts/reset_delta.py",
        "baseline": {k: base[k] for k in ("path", "mtime_iso", "sha256_16")},
        "method": {
            "cutoff": "a report is in the delta when its mtime is later than the baseline's "
                      "mtime (both printed, to the second)",
            "attachment": "the card family in the report's file name must be a card the baseline "
                          "lists under R-n; prefixes review-/rework-/audit-/chase-/polish-/"
                          "reverify- are stripped, the longest card name wins, and a name that "
                          "matches no card is left unattached",
            "status": "the report's own `STATUS:` line, quoted; its first word is the kind",
            "evidence": "only STATUS: done and STATUS: partial are evidence",
            "closed": f"a baseline UNKNOWN whose content words appear (coverage >= "
                      f"{MIN_COVERAGE}) in the report body outside its own UNKNOWN section",
            "opened": "a bullet of the report's UNKNOWN section that matches no baseline "
                      f"UNKNOWN of the item (coverage < {MIN_COVERAGE})",
        },
        "corrections": [
            {"id": "C-1", "what": "the 'EM ejection part' open item is dropped - only the eject "
                                  "mechanic matters, and its mapping to JC3 is task G3-08b",
             "effect": "baseline and report items mentioning the EM ejection part are excluded"},
            {"id": "C-2", "what": "a blocked report (STATUS: blocked, its gate missing) counts as "
                                  "no evidence at all",
             "effect": "blocked reports close nothing; their UNKNOWNs are listed apart"},
        ],
        "baseline_items": {rid: {"verdict": v["verdict"], "question": v["question"],
                                 "cards": sorted(v["cards"]),
                                 "unknowns": [u for u in v["unknowns"] if not dropped(u)]}
                           for rid, v in base["items"].items()},
        "rows": rows,
        "unattached": unattached,
        "counts": {
            "reports_total": len(files),
            "newer_than_baseline": len(newer),
            "attached": len(rows),
            "unattached": len(unattached),
            "blocked": sum(1 for r in rows if r["blocked"])
                       + sum(1 for r in unattached if r["blocked"]),
            "per_item": {rid: sum(1 for r in rows if r["item"] == rid)
                         for rid in sorted(base["items"])},
            "c1_dropped_bullets": sum(len(r.get("dropped_unknowns") or [])
                                       for r in rows + unattached),
            "c2_blocked": sum(1 for r in rows + unattached if r["blocked"]),
        },
        "dropped_baseline_unknowns": {rid: [u for u in v["unknowns"] if dropped(u)]
                                      for rid, v in base["items"].items()},
    }
    doc["digest"] = hashlib.sha1(json.dumps({k: v for k, v in doc.items() if k != "digest"},
                                            sort_keys=True, separators=(",", ":")).encode()
                                ).hexdigest()[:16]
    return doc


# ---------------------------------------------------------------- output
def table_rows(doc: dict) -> list[tuple[str, str, str, str, str]]:
    out = []
    for r in doc["rows"]:
        closed = "; ".join(c["baseline"] for c in r["closed"]) or "-"
        if r["evidence"]:
            opened = "; ".join(r["opened"]) or "-"
        else:
            tag = "blocked, no evidence" if r["blocked"] else "not done/partial, no evidence"
            opened = f"({tag}) " + ("; ".join(r["opened"]) or "-")
        out.append((r["item"], r["report"], r["status"], closed, opened))
    return out


def render(doc: dict) -> str:
    L: list[str] = []
    A = L.append
    A("# RESET_DELTA - what the reports after `RESET_STATUS.md` do to R-1..R-6")
    A("")
    A("Generated by `Tools/scripts/reset_delta.py --write`; `--check` re-reads every report and")
    A("re-derives this file byte for byte. `RESET_STATUS.md` is the baseline and is never written,")
    A("and `reset_status.py` is neither run nor copied.")
    A("")
    A(f"Baseline: `{doc['baseline']['path']}`, mtime **{doc['baseline']['mtime_iso']}**, sha256_16")
    A(f"`{doc['baseline']['sha256_16']}`. Reports in `tmp/freebuff/reports`: "
      f"{doc['counts']['reports_total']} `.md`; **{doc['counts']['newer_than_baseline']}** are")
    A("newer than the baseline and are the delta. Their STATUS lines are quoted verbatim.")
    A("")
    A("## Corrections applied (operator, 2026-11-05)")
    A("")
    for c in doc["corrections"]:
        A(f"- **{c['id']}** — {c['what']}. *Effect:* {c['effect']}.")
    dropped_items = {rid: v for rid, v in doc["dropped_baseline_unknowns"].items() if v}
    A("")
    if dropped_items:
        A("Baseline UNKNOWN lines dropped by C-1:")
        A("")
        for rid, us in sorted(dropped_items.items()):
            for u in us:
                A(f"- `{rid}` — {u}")
    else:
        A("No baseline UNKNOWN line mentions the EM ejection part, so C-1 removes nothing from the")
        A(f"baseline. It removes **{doc['counts']['c1_dropped_bullets']}** report bullet(s) from "
          f"the delta.")
    A("")
    A("## The table")
    A("")
    A("| R item | report | STATUS | closed UNKNOWNs | opened UNKNOWNs |")
    A("|---|---|---|---|---|")
    for rid, rep, status, closed, opened in table_rows(doc):
        A(f"| **{rid}** | `{rep}` | {status.replace('|', '/')} | {closed} | {opened} |")
    A("")
    A("## Per item")
    A("")
    for rid, item in doc["baseline_items"].items():
        rows = [r for r in doc["rows"] if r["item"] == rid]
        A(f"### {rid} — baseline **{item['verdict']}**, {len(rows)} report(s) in the delta")
        A("")
        A(f"> {item['question']}")
        A("")
        if not rows:
            A("No report newer than the baseline attaches to this item.")
            A("")
            continue
        A("| report | STATUS (verbatim) | attached by | evidence | closed | opened |")
        A("|---|---|---|---:|---:|---:|")
        for r in rows:
            A(f"| `{r['report']}` | {r['status_line'].replace('|', '/')} | {r['how']} | "
              f"{'yes' if r['evidence'] else '**no**'} | {len(r['closed'])} | "
              f"{len(r['opened'])} |")
        A("")
        closed_rows = [(r["report"], c) for r in rows for c in r["closed"]]
        if closed_rows:
            A("Closed:")
            A("")
            for rep, c in closed_rows:
                A(f"- `{rep}` closes **{c['baseline']}** (coverage {c['coverage']})")
            A("")
        opened_rows = [(r["report"], u) for r in rows if r["evidence"] for u in r["opened"]]
        if opened_rows:
            A("Opened:")
            A("")
            for rep, u in opened_rows:
                A(f"- `{rep}`: {u}")
            A("")
        blocked_rows = [r for r in rows if not r["evidence"]]
        if blocked_rows:
            A("No evidence — `blocked` (C-2) or a STATUS word outside done/partial; listed, "
              "closes nothing:")
            A("")
            for r in blocked_rows:
                A(f"- `{r['report']}` — {r['status_line'] or '_no STATUS line_'}")
            A("")
        still = [(r["report"], c) for r in rows for c in r["not_closed"] if c["coverage"] >= 0.4]
        if still:
            A("Baseline UNKNOWNs a report *touches* but does not close (coverage 0.4-0.6):")
            A("")
            for rep, c in still:
                A(f"- `{rep}`: {c['baseline']} ({c['coverage']})")
            A("")
    A("## Reports that could not be classified")
    A("")
    A(f"{doc['counts']['unattached']} of the {doc['counts']['newer_than_baseline']} delta reports")
    A("name no card the baseline lists under R-1..R-6, so they are attached to nothing here.")
    A("The reason is the same for all: the file name's card family is not in the baseline's tables")
    A("(follow-up cards, tool reports, ledger and world/audio cards).")
    A("")
    A("| report | STATUS | why unattached |")
    A("|---|---|---|")
    for r in doc["unattached"]:
        A(f"| `{r['report']}` | {r['status_line'] or '_no STATUS line_'} | {r['why']} |")
    A("")
    A("## What this document does not say")
    A("")
    A("- It does not re-derive any R verdict. The baseline's verdicts are quoted, not changed; a")
    A("  report that closes an UNKNOWN does not by itself move an item from PARTIAL to RESOLVED,")
    A("  which the baseline defines over its core cards and their reviews.")
    A("- It does not judge a report's numbers. A `needs rework` review is itself one of the delta")
    A("  reports (attached by its file name), so its effect is visible as a row, not as a verdict.")
    A("- It does not attach a report by keyword similarity to an R question: only the baseline's")
    A("  own card tables decide, and anything else lands in the unattached list.")
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = scan()
    md = render(doc)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1, sort_keys=True)
            f.write("\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        for rid, rep, status, closed, opened in table_rows(doc):
            print(f"{rid:5} | {rep:28} | {status[:44]:44} | closed: {closed[:40]:40} | "
                  f"opened: {opened[:40]}")
        print(f"\n{doc['counts']['attached']} attached, {doc['counts']['unattached']} unattached, "
              f"{doc['counts']['newer_than_baseline']} newer than the baseline")
        print(f"digest {doc['digest']}")
        return 0
    same = (os.path.exists(OUT_MD) and open(OUT_MD, encoding="utf-8").read() == md
            and os.path.exists(OUT_JSON) and open(OUT_JSON, encoding="utf-8").read()
            == json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"md+json identical {same}")
    print(f"attached {doc['counts']['attached']}  unattached {doc['counts']['unattached']}  "
          f"newer {doc['counts']['newer_than_baseline']}")
    print("CHECK", "PASS" if same else "FAIL")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())
