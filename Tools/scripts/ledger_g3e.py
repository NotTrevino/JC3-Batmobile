#!/usr/bin/env python3
"""ledger_g3e.py - merge the G3 ledger verdicts into one table for all 198 rows.

Reads, never edits:
    Working/Translation/T_ROWS.jsonl            the 198 rows (ids + doc only)
    Working/Translation/LEDGER_G3B.md           Rows T-1, T-2b, T-13 (105)
    Working/Translation/LEDGER_G3C.md           Rows T-20, T-3, T-7, T-15, T-14 (93)
    Working/Translation/LEDGER_SOURCES.md       the 96 G3B OPEN rows' provenance
    Working/Translation/MISSING_ROWS.json       G3-11c's proposal (ids only)

Writes:
    Working/Translation/LEDGER_G3E.md
    Working/Translation/LEDGER_G3E.json

No value is re-tested: each verdict is taken verbatim from the file that states it.
The only rule applied is the merge rule:

    * G3B statuses map one-to-one (HOLDS / WRONG_VALUE / WRONG_CARD / OPEN).
    * G3C `QUOTED` maps by `relation`: agrees|supplies -> holds, differs -> wrong value,
      different-member|different-object -> wrong card.  G3C `OPEN` -> open.
    * G3B §2 and §3 both carry verdicts.  If they disagree, that is a conflict.
    * A row two sources grade differently is a conflict: neither verdict is taken.
    * An OPEN row that LEDGER_SOURCES puts "outside the seven" is not re-derivable.
    * A row with no verdict anywhere is UNKNOWN.

Usage:
    python Tools/scripts/ledger_g3e.py --write
    python Tools/scripts/ledger_g3e.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T = os.path.join(ROOT, "Working", "Translation")
T_ROWS = os.path.join(T, "T_ROWS.jsonl")
G3B = os.path.join(T, "LEDGER_G3B.md")
G3C = os.path.join(T, "LEDGER_G3C.md")
SOURCES = os.path.join(T, "LEDGER_SOURCES.md")
MISSING = os.path.join(T, "MISSING_ROWS.json")
OUT_MD = os.path.join(T, "LEDGER_G3E.md")
OUT_JSON = os.path.join(T, "LEDGER_G3E.json")

VERDICTS = ("holds", "wrong value", "wrong card", "open", "not re-derivable",
            "conflict", "UNKNOWN")

G3B_MAP = {"HOLDS": "holds", "WRONG_VALUE": "wrong value",
           "WRONG_CARD": "wrong card", "OPEN": "open"}
G3C_RELATION = {"agrees": "holds", "supplies": "holds", "differs": "wrong value",
                "different-member": "wrong card", "different-object": "wrong card",
                "adjacent": "wrong card"}


def read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def cell(s: str) -> str:
    """One markdown table cell: strip emphasis and backticks, collapse whitespace."""
    s = s.strip().replace("\\|", "|")
    s = s.replace("**", "").strip("`").strip()
    return re.sub(r"\s+", " ", s)


def cells(line: str) -> list[str]:
    """Split a table row on ` | `; escaped pipes (`\\|`) never split."""
    body = line.strip().strip("|")
    return [c.strip() for c in body.split(" | ")]


def section(text: str, start: str, end: str) -> list[tuple[int, str]]:
    """Lines (1-based) from the line containing `start` to the line containing `end`."""
    out, on = [], False
    for n, line in enumerate(text.splitlines(), 1):
        if not on:
            if start in line:
                on = True
            continue
        if end in line:
            break
        out.append((n, line))
    if not on:
        raise SystemExit(f"section not found: {start!r}")
    return out


def table_rows(lines):
    for n, line in lines:
        if line.startswith("| `T-") or line.startswith("| T-"):
            yield n, line


# ----------------------------------------------------------------- parse
def parse_ledger() -> list[dict]:
    rows = []
    for line in read(T_ROWS).splitlines():
        if line.strip():
            r = json.loads(line)
            rows.append({"id": r["id"], "doc": r.get("doc", ""), "dispo": r.get("dispo", "")})
    return rows


def parse_g3b() -> list[dict]:
    text = read(G3B)
    out = []
    # §2 has the first-pass verdicts for 18 rows; §3 has a status for every row.
    for n, line in table_rows(section(text, "## 2. The 18 rows", "## 3. Every row")):
        c = cells(line)
        rid = re.match(r"`?(T-[A-Z0-9]+)", c[0]).group(1)
        out.append({"row": rid, "verdict": G3B_MAP.get(cell(c[2]).upper(), "UNKNOWN"),
                    "source": f"LEDGER_G3B.md:{n}", "part": "§2",
                    "evidence": c[3] if len(c) > 3 else "", "raw": cell(c[2])})
    for n, line in table_rows(section(text, "## 3. Every row", "## 4. What the OPEN")):
        c = cells(line)
        rid = re.match(r"`?(T-[A-Z0-9]+)", c[0]).group(1)
        out.append({"row": rid, "verdict": G3B_MAP.get(cell(c[3]).upper(), "UNKNOWN"),
                    "source": f"LEDGER_G3B.md:{n}", "part": "§3",
                    "evidence": c[4] if len(c) > 4 else "", "raw": cell(c[3])})
    return out


def parse_g3c() -> list[dict]:
    text = read(G3C)
    out = []
    for n, line in table_rows(section(text, "## Row index", "## Rows")):
        c = cells(line)
        rid = re.match(r"`?(T-[A-Z0-9]+)", c[0]).group(1)
        status, relation = cell(c[3]).upper(), cell(c[4]).lower()
        if status == "QUOTED":
            verdict = G3C_RELATION.get(relation, "UNKNOWN")
        elif status == "OPEN":
            verdict = "open"
        else:
            verdict = "UNKNOWN"
        out.append({"row": rid, "verdict": verdict, "source": f"LEDGER_G3C.md:{n}",
                    "part": "row index", "relation": relation,
                    "evidence": c[5] if len(c) > 5 else "", "raw": f"{status}/{relation}"})
    return out


def parse_sources() -> list[dict]:
    text = read(SOURCES)
    out = []
    for n, line in table_rows(section(text, "## 2. The 96 OPEN rows", "### Counts")):
        c = cells(line)
        rid = re.match(r"`?(T-[A-Z0-9]+)", c[0]).group(1)
        prov = cell(c[4])
        out.append({"row": rid, "outside": "outside the seven" in prov,
                    "provenance": prov, "source": f"LEDGER_SOURCES.md:{n}",
                    "cites": cell(c[3])})
    return out


def parse_missing() -> list[str]:
    doc = json.load(open(MISSING, encoding="utf-8"))
    ids = []
    for key in ("rows", "proposed_rows", "proposal"):
        v = doc.get(key)
        if isinstance(v, list):
            for r in v:
                if isinstance(r, dict) and "id" in r:
                    ids.append(r["id"])
    return sorted(set(ids))


# ----------------------------------------------------------------- merge
def merge(ledger, g3b, g3c, sources, missing) -> dict:
    ids = {r["id"] for r in ledger}
    by_row: dict[str, list[dict]] = {}
    for v in g3b + g3c:
        if v["row"] in ids:
            by_row.setdefault(v["row"], []).append(v)
    src = {s["row"]: s for s in sources if s["row"] in ids}

    out = []
    for r in ledger:
        votes = by_row.get(r["id"], [])
        vs = {v["verdict"] for v in votes}
        if not votes:
            out.append({**r, "verdict": "UNKNOWN", "sources": [], "why": "no verdict in any file"})
            continue
        if "UNKNOWN" in vs:
            out.append({**r, "verdict": "UNKNOWN", "sources": votes,
                        "why": "a source used a status this merge cannot map"})
            continue
        if len(vs) > 1:
            out.append({**r, "verdict": "conflict", "sources": votes,
                        "why": "; ".join(sorted(vs))})
            continue
        verdict = vs.pop()
        chosen = votes[0]
        note = ""
        if verdict == "open" and r["id"] in src and src[r["id"]]["outside"]:
            verdict = "not re-derivable"
            note = ("LEDGER_SOURCES.md puts the row outside the seven; "
                    "still OPEN in " + chosen["source"])
        out.append({**r, "verdict": verdict, "sources": votes, "why": note})

    counts = {v: 0 for v in VERDICTS}
    for r in out:
        counts[r["verdict"]] += 1
    return {"rows": out, "counts": counts, "missing_ids": missing,
            "inputs": {"ledger": len(ledger),
                       "g3b_s2": sum(1 for v in g3b if v["part"] == "§2"),
                       "g3b_s3": sum(1 for v in g3b if v["part"] == "§3"),
                       "g3c": len(g3c),
                       "outside": sum(1 for s in sources if s["outside"]),
                       "sources": len(sources)}}


# ----------------------------------------------------------------- oracles
def oracles(doc: dict) -> dict:
    rows = doc["rows"]
    by_id = {r["id"]: r for r in rows}
    cited_ok, bad = True, []
    for r in rows:
        for s in r["sources"]:
            line = read(os.path.join(T, s["source"].split(":")[0])).splitlines()
            n = int(s["source"].split(":")[1])
            if r["id"] not in line[n - 1]:
                cited_ok = False
                bad.append(f"{r['id']} @ {s['source']}")
    conflicts = [r for r in rows if r["verdict"] == "conflict"]
    return {
        "row_count_198": {"ok": len(rows) == 198 and len(by_id) == 198,
                          "detail": {"rows": len(rows), "unique": len(by_id)}},
        "input_counts": {
            "ok": (doc["inputs"]["g3b_s3"] == 105 and doc["inputs"]["g3b_s2"] == 18
                   and doc["inputs"]["g3c"] == 93 and doc["inputs"]["sources"] == 96
                   and doc["inputs"]["outside"] == 27),
            "detail": doc["inputs"],
        },
        "counts_sum": {"ok": sum(doc["counts"].values()) == 198,
                       "detail": doc["counts"]},
        "every_verdict_has_source": {
            "ok": all(r["sources"] for r in rows if r["verdict"] != "UNKNOWN"),
            "detail": {"without": [r["id"] for r in rows
                                   if r["verdict"] != "UNKNOWN" and not r["sources"]]},
        },
        "cited_line_names_row": {"ok": cited_ok, "detail": bad[:10]},
        "conflicts_are_two_sided": {
            "ok": all(len({s["verdict"] for s in r["sources"]}) > 1 for r in conflicts),
            "detail": {r["id"]: [s["verdict"] for s in r["sources"]] for r in conflicts},
        },
        "conflict_split": {
            # 8 rows are §2 WRONG_CARD vs §3 OPEN inside G3B; T-WP11 is G3B §2
            # WRONG_CARD vs G3C QUOTED/agrees.  Both kinds are conflicts.
            "ok": (sum(1 for r in conflicts if {s["part"] for s in r["sources"]} == {"§2", "§3"}) == 8
                   and sum(1 for r in conflicts if len({s["source"].split(":")[0]
                                                        for s in r["sources"]}) > 1) == 1),
            "detail": {r["id"]: [s["source"] for s in r["sources"]] for r in conflicts},
        },
        "g3c_relations_known": {
            "ok": all(s.get("relation") in (None, "", *G3C_RELATION,
                                            "n/a", "negative", "confirms-open")
                      for r in rows for s in r["sources"]
                      if s["source"].startswith("LEDGER_G3C")),
            "detail": sorted({s.get("relation", "") for r in rows for s in r["sources"]
                              if s["source"].startswith("LEDGER_G3C")}),
        },
        "g3_11c_adds_no_ledger_row": {
            "ok": not (set(doc["missing_ids"]) & set(by_id)),
            "detail": {"proposed": doc["missing_ids"],
                       "in_ledger": sorted(set(doc["missing_ids"]) & set(by_id))},
        },
    }


# ----------------------------------------------------------------- render
def render(doc: dict) -> str:
    c = doc["counts"]
    rows = doc["rows"]
    L = [
        "# LEDGER_G3E — one verdict per ledger row",
        "",
        "Generated by `Tools/scripts/ledger_g3e.py --write`; `--check` re-reads the four source",
        "documents, re-parses every verdict and compares this file byte for byte. No value was",
        "re-tested here: each verdict is quoted from the file that states it.",
        "",
        "## 1. Verdicts",
        "",
        "| verdict | rows |",
        "|---|---:|",
    ]
    for v in VERDICTS:
        L.append(f"| {v} | {c[v]} |")
    L += [
        f"| **total** | **{sum(c.values())}** |",
        "",
        "## 2. How a source status became a verdict",
        "",
        "| source | its status | this table |",
        "|---|---|---|",
        "| `LEDGER_G3B.md` §2/§3 | HOLDS | holds |",
        "| `LEDGER_G3B.md` §2/§3 | WRONG_VALUE | wrong value |",
        "| `LEDGER_G3B.md` §2/§3 | WRONG_CARD | wrong card |",
        "| `LEDGER_G3B.md` §3 | OPEN | open |",
        "| `LEDGER_G3C.md` | QUOTED + relation `agrees` / `supplies` | holds |",
        "| `LEDGER_G3C.md` | QUOTED + relation `differs` | wrong value |",
        "| `LEDGER_G3C.md` | QUOTED + relation `different-member` | wrong card |",
        "| `LEDGER_G3C.md` | OPEN | open |",
        "| `LEDGER_SOURCES.md` | “outside the seven” on an open row | not re-derivable |",
        "",
        "A row with two different verdicts from two places is `conflict` and takes neither.",
        "A row no file grades is `UNKNOWN`.",
        "",
        "## 3. Conflicts",
        "",
    ]
    conflicts = [r for r in rows if r["verdict"] == "conflict"]
    if not conflicts:
        L.append("None.")
    else:
        L += ["| row | file:line | verdict it states |", "|---|---|---|"]
        for r in conflicts:
            for s in r["sources"]:
                L.append(f"| `{r['id']}` | `{s['source']}` ({s['part']}) | "
                         f"**{s['verdict']}** (`{s['raw']}`) |")
    internal = [r for r in conflicts
                if {s["part"] for s in r["sources"]} == {"§2", "§3"}]
    cross = [r for r in conflicts if r not in internal]
    L += [""]
    if internal:
        L += [f"{len(internal)} of these are inside `LEDGER_G3B.md` itself: §2 grades the row",
              "`WRONG_CARD` while §3 grades it `OPEN`. The file's header count (6 HOLDS, 96 OPEN,",
              "3 WRONG_VALUE) matches §3 only, so §2 is the outlier — but neither is taken here.",
              ""]
    if cross:
        L += [f"{len(cross)} {'is' if len(cross) == 1 else 'are'} cross-file: " + ", ".join(
                f"`{r['id']}` (" + " / ".join(s["source"] for s in r["sources"]) + ")"
                for r in cross) + ".", ""]
    L += ["## 4. Rows with no verdict", ""]
    unknown = [r for r in rows if r["verdict"] == "UNKNOWN"]
    if not unknown:
        L.append("None: every one of the 198 rows is graded by at least one file.")
    else:
        L += ["| row | doc |", "|---|---|"]
        for r in unknown:
            L.append(f"| `{r['id']}` | {r['doc']} |")
    L += [
        "",
        "## 5. Not re-derivable",
        "",
        "`LEDGER_SOURCES.md` §2 puts these open rows outside its seven sources (they name",
        "`stations.json`, the §70 mesh measurement or a card from another family), so no",
        "producer re-run can re-derive them. They keep the open verdict's substance and add why.",
        "",
        "| row | source | its provenance |",
        "|---|---|---|",
    ]
    for r in rows:
        if r["verdict"] == "not re-derivable":
            s = r["sources"][0]
            L.append(f"| `{r['id']}` | `{s['source']}` | {r['why']} |")
    L += [
        "",
        "## 6. Every row",
        "",
        "| row | doc | verdict | source | evidence as taken |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        if not r["sources"]:
            L.append(f"| `{r['id']}` | {r['doc']} | **UNKNOWN** | — | — |")
            continue
        src = "; ".join(f"`{s['source']}`" for s in r["sources"])
        ev = " / ".join(cell(s["evidence"]) for s in r["sources"])
        ev = ev if len(ev) <= 150 else ev[:147] + "..."
        L.append(f"| `{r['id']}` | {r['doc']} | **{r['verdict']}** | {src} | {ev or '—'} |")
    L += [
        "",
        "## 7. Oracles",
        "",
        "| oracle | ok | detail |",
        "|---|---|---|",
    ]
    for k, v in doc["oracles"].items():
        d = json.dumps(v["detail"], default=str)
        if len(d) > 200:
            d = d[:197] + "..."
        L.append(f"| `{k}` | {v['ok']} | `{d}` |")
    L += [
        "",
        "## 8. Sources and UNKNOWNs",
        "",
        "- `Working/Translation/T_ROWS.jsonl` — read for the 198 ids and doc labels only.",
        "- `Working/Translation/LEDGER_G3B.md` — groups T-1, T-2b, T-13 (105 rows).",
        "- `Working/Translation/LEDGER_G3C.md` — groups T-20, T-3, T-7, T-15, T-14 (93 rows).",
        "- `Working/Translation/LEDGER_SOURCES.md` — the 96 G3B-open rows' provenance.",
        "- `Working/Translation/MISSING_ROWS.json` — G3-11c's 8 proposed ids.",
        "",
        "UNKNOWNs:",
        "",
        f"- **Which of §2/§3 in `LEDGER_G3B.md` is current.** The {len(internal)} rows that",
        "  disagree inside that file are left as conflicts; resolving them needs the author of",
        "  that pass, not a re-read. The ninth conflict (`T-WP11`) is cross-file.",
        "- **Any verdict G3-11c was expected to add.** Its report and `MISSING_ROWS.json` propose",
        "  eight ids that are not in `T_ROWS.jsonl` (`T-AB1..3`, `T-IN1..5`); none of the 198 rows",
        "  gains a verdict from it. The brief's \"G3-11c handled those 27\" is therefore not",
        f"  supported by the file: `LEDGER_SOURCES.md` puts {doc['inputs']['outside']} rows outside its",
        "  seven sources, and two of them (`T-CO1`, `T-CO2`) are also §2/§3 conflicts, leaving",
        "  25 as not re-derivable. G3-11c proposes new ids, it does not grade an existing row.",
        "",
    ]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = merge(parse_ledger(), parse_g3b(), parse_g3c(), parse_sources(), parse_missing())
    doc["oracles"] = oracles(doc)
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
    for k, v in doc["oracles"].items():
        print(f"{'ok  ' if v['ok'] else 'FAIL'} {k}")
    print("counts: " + ", ".join(f"{k} {v}" for k, v in doc["counts"].items()))

    if a.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print(f"wrote {OUT_MD}\nwrote {OUT_JSON}")
    else:
        if open(OUT_MD, encoding="utf-8").read() != md:
            print("FAIL md differs from a fresh merge")
            bad.append("md")
        if open(OUT_JSON, encoding="utf-8").read() != js:
            print("FAIL json differs from a fresh merge")
            bad.append("json")
        print("check ok" if not bad else "check FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
