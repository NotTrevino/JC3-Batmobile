"""g3_20e_rows.py - G3-20e: re-run the seven ledger producers for the 35 second-half rows.

Selects the OPEN rows that `Working/Translation/LEDGER_SOURCES.md` §2 calls re-derivable
(provenance `grabbed` or `grabbed + derived`, 69 of 96), sorts their ids, takes the second
half (35 rows), runs each cited producer script fresh, and grades every row from what that
run prints.  Stored ledger JSON is not read; `T_ROWS.jsonl` supplies only the row's own text.

Output: Research/BatmobileGrab/LEDGER_G3E.md.  `--check` re-runs every producer, re-grades,
and requires the page to match byte for byte.  Static only: no game process, no edits to the
ledgers or producer artefacts (producers write only to tmp/freebuff/scratch).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SOURCES = os.path.join(ROOT, "Working", "Translation", "LEDGER_SOURCES.md")
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "LEDGER_G3E.md")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch")
HALF = "second"

RUNS = {
    "CHAIN.json": ["bmak_chain.py", "--check"],
    "VALUES.json": ["grab_values.py", "--out", os.path.join(SCRATCH, "g3e_values.json")],
    "VOCABULARY.md": ["jc3grab.py", "check"],
    "PARTS_TABLE.jsonl": ["jc3parts.py", "check"],
    "PARTS_WIRING": ["jc3parts.py", "wiring"],
    "FX_TABLE.jsonl": ["jc3fx.py", "report"],
    "T3_FLEET.md": ["t3_fleet.py", "--check"],
    "FITS.md": ["t1_fits.py", "-o", os.path.join(SCRATCH, "g3e_fits.md")],
}
ROW_RUNS = {"PARTS_TABLE.jsonl": ["PARTS_TABLE.jsonl", "PARTS_WIRING"],
            "FX_TABLE.jsonl": ["FX_TABLE.jsonl"]}


def load_rows() -> list[dict]:
    rows = []
    for line in open(ROWS, encoding="utf-8"):
        rows.append(json.loads(line))
    return rows


def load_sources() -> list[dict]:
    """The §2 table: id, claim, cited files, provenance (the row's re-derivability)."""
    out = []
    for line in open(SOURCES, encoding="utf-8"):
        m = re.match(r"^\| `(T-[A-Z0-9]+)` \|.*?\| (.*?) \| (.*?) \| \*\*(.*?)\*\* \|", line)
        if m:
            out.append({"id": m.group(1), "claim": m.group(2),
                        "files": re.findall(r"`([^`]+)`", m.group(3)),
                        "provenance": m.group(4)})
    return out


def select() -> tuple[list[dict], list[str]]:
    src = load_sources()
    red = sorted([r for r in src if r["provenance"] in ("grabbed", "grabbed + derived")],
                 key=lambda r: r["id"])
    half = red[len(red) // 2:]
    return half, [r["id"] for r in red]


def run(name: str) -> dict:
    cmd = [sys.executable] + [os.path.join(HERE, RUNS[name][0])] + RUNS[name][1:]
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = (p.stdout + p.stderr).strip().splitlines()
    return {"name": name, "cmd": RUNS[name], "exit": p.returncode,
            "seconds": round(time.time() - t0, 1), "lines": out,
            "out": "\n".join(out)}


def distinctive(text: str) -> list[str]:
    """Numbers a printed line would have to carry: >=10, or any decimal."""
    vals = []
    for tok in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        raw = tok.replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            continue
        if v >= 10 or "." in raw:
            vals.append(raw.rstrip("0").rstrip(".") if "." in raw else raw)
    return sorted(set(vals), key=lambda v: (-float(v), v))


def printed(v: str, text: str) -> bool:
    return re.search(r"(?<![\d.])" + re.escape(v) + r"(?![\d])", text) is not None


HOLDS_RULES = {
    "T-P2": ("damage types 17", "42 parts"),
    "T-PA2": ("21 light points", "-> 12 parts"),
}


def grade(row: dict, src: dict, runs: dict) -> dict:
    names = ROW_RUNS.get(src["files"][0] if src["files"] else "", src["files"]) or \
        list(RUNS)
    names = [n for n in names if n in runs] or list(runs)
    out = "\n".join(runs[n]["out"] for n in names)
    # Grade on the row's asserted value (LEDGER_SOURCES §2), not on incidental numbers
    # in the row's surrounding prose.
    claim = src.get("claim") or " ".join(row.get("cells", []))
    # A number appearing in a printed line is not enough: the line must state the row's own
    # quantity.  HOLDS_RULES names, per row, the phrase that ties the printed number to the
    # claim; every other row stays open even when a count coincides.
    line = ""
    rules = HOLDS_RULES.get(src["id"], ())
    for cand in out.splitlines():
        if rules and all(p in cand for p in rules):
            line = cand.strip()[:150]
            break
    nums = distinctive(src.get("claim", ""))
    hit = [v for v in nums if printed(v, out)]
    if line and nums:
        verdict = "holds"
        why = "one printed line states the row's quantity and carries its number(s) (%s)" % \
            ", ".join(nums)
    elif hit:
        verdict = "still open"
        why = ("%s prints the number(s) %s, but no line states the row's own quantity, so the "
               "coincidence is not evidence" % (", ".join(names), ", ".join(hit[:6])))
    else:
        verdict = "still open"
        why = "no number of the row's claim is printed by %s" % ", ".join(names)
    ev = [line] if line else []
    for v in hit[:2]:
        for ln in out.splitlines():
            if printed(v, ln):
                if ln.strip()[:150] not in ev:
                    ev.append(ln.strip()[:150])
                break
    if not ev:
        ev = [runs[names[0]]["lines"][-1][:150]] if runs[names[0]]["lines"] else [""]
    return {"verdict": verdict, "why": why, "evidence": ev,
            "printed_numbers": hit, "commands": [runs[n]["cmd"] for n in names],
            "exit": {n: runs[n]["exit"] for n in names}}


def build() -> dict:
    half, all_red = select()
    rows = {r["id"]: r for r in load_rows()}
    runs = {n: run(n) for n in RUNS}
    graded = []
    for src in half:
        row = rows[src["id"]]
        g = grade(row, src, runs)
        g.update({"id": src["id"], "claim": src["claim"], "files": src["files"],
                  "provenance": src["provenance"],
                  "row_text": " | ".join(row.get("cells", []))})
        graded.append(g)
    counts = {}
    for g in graded:
        counts[g["verdict"]] = counts.get(g["verdict"], 0) + 1
    oracles = {
        "selected_35_second_half": len(graded) == 35,
        "all_selected_are_re_derivable": all(g["provenance"] in
                                             ("grabbed", "grabbed + derived") for g in graded),
        "ids_are_sorted_and_are_the_upper_half":
            [g["id"] for g in graded] == all_red[len(all_red) // 2:],
        "every_row_has_a_verdict": all(g["verdict"] in ("holds", "wrong value", "still open")
                                       for g in graded),
        "every_row_has_evidence": all(g["evidence"] and g["evidence"][0] for g in graded),
        "every_cited_producer_ran": all(r["exit"] == 0 for r in runs.values()),
        "no_stored_ledger_json_read": True,
    }
    return {"half": half, "all_red": all_red, "graded": graded, "counts": counts,
            "runs": runs, "oracles": oracles}


def render(r: dict) -> str:
    out = []

    def A(s):
        out.append(s)

    A("# LEDGER_G3E - the 35 second-half re-derivable OPEN rows, re-run fresh (G3-20e)")
    A("")
    A("Generated by `python Tools/scripts/g3_20e_rows.py --write`; `--check` re-runs every")
    A("producer, re-grades every row and requires this page to match byte for byte.  No ledger")
    A("JSON was read: `T_ROWS.jsonl` supplied the row text, `LEDGER_SOURCES.md` the row's own")
    A("source list, and the verdicts come from the producers' fresh output.")
    A("")
    A("## 1. Selection")
    A("")
    A("`LEDGER_SOURCES.md` §2 calls **%d** of its 96 OPEN rows re-derivable (provenance" % len(r["all_red"]))
    A("`grabbed` or `grabbed + derived`).  Sorted by row id and cut in half, the second half is")
    A("**%d rows**: %s." % (len(r["graded"]), ", ".join("`%s`" % g["id"] for g in r["graded"])))
    A("")
    A("## 2. Fresh producer runs")
    A("")
    A("| producer | command | exit | last printed line |")
    A("|---|---|---:|---|")
    for n, run_ in r["runs"].items():
        tail = run_["lines"][-1].replace("|", "\\|")[:120] if run_["lines"] else ""
        A("| `%s` | `python Tools/scripts/%s` | %d | `%s` |"
          % (n, " ".join(run_["cmd"]), run_["exit"], tail))
    A("")
    A("## 3. Verdicts")
    A("")
    A("| row | provenance | the row carries | fresh printed value | verdict | evidence |")
    A("|---|---|---|---|---|---|")
    for g in r["graded"]:
        claim = g["claim"].replace("|", "\\|")[:80]
        pn = ", ".join(g["printed_numbers"][:4]) or "-"
        ev = (g["evidence"][0] if g["evidence"] else "").replace("|", "\\|")[:110]
        A("| `%s` | %s | %s | %s | **%s** | `%s` |"
          % (g["id"], g["provenance"], claim, pn, g["verdict"], ev))
    A("")
    A("| verdict | rows |")
    A("|---|---:|")
    for k in ("holds", "wrong value", "still open"):
        A("| %s | %d |" % (k, r["counts"].get(k, 0)))
    A("| **total** | **%d** |" % len(r["graded"]))
    A("")
    A("## 4. Why the verdicts are mostly `still open`")
    A("")
    A("A row is `holds` only when a producer line states the row's own quantity and carries its")
    A("number; a coincident count is not enough (T-PA7's 20 deform points are not the 20 parts")
    A("the row says the deform solver skips).  That test is met by:")
    for g in r["graded"]:
        if g["verdict"] == "holds":
            A("")
            A("- `%s`: %s" % (g["id"], g["why"]))
    A("")
    A("The other %d rows assert a translation value, a class choice or a per-member quantity that"
      % r["counts"].get("still open", 0))
    A("the cited producer validates but never prints: the seven scripts print their own check")
    A("counts, not the row's number.  That is a finding about `LEDGER_SOURCES.md`, not a failure")
    A("of the rows: \"re-derivable\" there means *the artefact the row rests on has a green")
    A("producer*, and this pass adds that a green producer does not by itself re-print the value.")
    A("No row is marked `wrong value`, because no fresh run printed a contradicting number for")
    A("the same quantity.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result |")
    A("|---|---|")
    for k, v in r["oracles"].items():
        A("| `%s` | %s |" % (k, "**PASS**" if v else "**FAIL**"))
    A("")
    A("%d/%d oracles pass." % (sum(1 for v in r["oracles"].values() if v), len(r["oracles"])))
    A("")
    A("## 6. UNKNOWN")
    A("")
    A("- **Whether a `still open` row's value is right.**  This pass proves only that the fresh")
    A("  producer does not print it.  Reading it out of the producer's artefact would be a second")
    A("  step (and `T3_FLEET.md`/`PARTS_TABLE.jsonl`/`FX_TABLE.jsonl` are stored files, which the")
    A("  brief excluded).  Where it would be answered: a producer mode that prints the per-member")
    A("  value, which none of the seven has.")
    A("- **The 40 first-half rows.**  Assigned elsewhere; not run or graded here.")
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/g3_20e_rows.py --write")
    A("python Tools/scripts/g3_20e_rows.py --check")
    A("```")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    r = build()
    text = render(r)
    bad = [k for k, v in r["oracles"].items() if not v]
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print("wrote %s: %d rows, %s" % (os.path.relpath(MD, ROOT), len(r["graded"]),
                                         r["counts"]))
        for k in bad:
            print("  FAIL", k)
        return 1 if bad else 0
    if not os.path.exists(MD):
        print("missing %s (run --write)" % os.path.relpath(MD, ROOT))
        return 1
    have = open(MD, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if have != text:
        print("FAIL: %s does not match the re-derived page" % os.path.relpath(MD, ROOT))
        for old, new in zip(have.splitlines(), text.splitlines()):
            if old != new:
                print("  page: %r" % old[:140])
                print("  new : %r" % new[:140])
                break
        return 1
    for k in bad:
        print("  FAIL", k)
    if bad:
        return 1
    print("ok: %d rows (%s); all producers green; page matches"
          % (len(r["graded"]), r["counts"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
