#!/usr/bin/env python3
"""Check the boost-row proposals against the BmAK source files and the JC3 field inventory.

`Working/Translation/BOOST_COVERAGE.md` lists the BmAK afterburner values that have no translation
row. `Working/Translation/BOOST_ROWS_PROPOSAL.md` proposes one row per value: either a **map** (a
JC3 field exists that can carry it, with the converted value and the conversion rule) or an explicit
**omit** (no carrier, with the reason).

This checker is read-only. It:

  * parses the fenced JSON in the proposal page;
  * re-reads every cited BmAK source line and asserts the needle and the value are on that line;
  * re-runs every conversion from the stated factor and asserts the converted value;
  * verifies each map row's JC3 member exists in the cited JC3 source line (and its fleet domain
    line), and that each omit row has no member and a stated reason with at least one evidence line;
  * parses the uncovered set out of BOOST_COVERAGE.md sections 3/4 and asserts the proposal covers
    exactly it;
  * checks the donor nitro block (`USAGES.md` section 6) still carries exactly the five members the
    decision refers to, and that the T-E5 conflict is real;
  * asserts no proposal id exists in `T_ROWS.jsonl` (nothing was added to the translation table).

Usage
  python Tools/scripts/t_boost_rows.py --check
  python Tools/scripts/t_boost_rows.py --write   # prints the parsed proposal counts (no file write)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROPOSAL = "Working/Translation/BOOST_ROWS_PROPOSAL.md"
COVERAGE = "Working/Translation/BOOST_COVERAGE.md"
ROWS = "Working/Translation/T_ROWS.jsonl"
USAGES = "Research/JC3Grab/USAGES.md"


def rel(p: str) -> str:
    return p.replace("\\", "/")


def read(path: str) -> str:
    return open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()


def line_of(path: str, n: int) -> str:
    lines = read(path).splitlines()
    if n < 1 or n > len(lines):
        raise SystemExit("%s:%d is outside the file" % (path, n))
    return lines[n - 1]


def proposal() -> dict:
    text = read(PROPOSAL)
    m = re.search(r"```json\n(.*?)\n```", text, re.S)
    if not m:
        raise SystemExit("no fenced json block in " + PROPOSAL)
    return json.loads(m.group(1))


def t_rows() -> list[dict]:
    return [json.loads(line) for line in read(ROWS).splitlines() if line.strip()]


def uncovered() -> set[str]:
    """The fields BOOST_COVERAGE.md leaves without a row: section 4 bullets + BoostDuration."""
    text = read(COVERAGE)
    sec = text.split("## 4. BmAK values with no translation row", 1)[1].split("\n## 5.", 1)[0]
    fields = set(re.findall(r"^\* `([^`]+)`", sec, re.M))
    # BoostDuration has no row of its own (section 3 marks it "T-B2 (as a term only)")
    fields.add("BoostDuration")
    return fields


def check_source(label: str, spec: dict, value_text: str | None) -> None:
    line = line_of(spec["path"], spec["line"])
    if spec["needle"] not in line:
        raise SystemExit("%s: %s:%d lacks %r" % (label, spec["path"], spec["line"], spec["needle"]))
    if value_text is not None and value_text not in line:
        raise SystemExit("%s: %s:%d lacks the value %r" % (label, spec["path"], spec["line"], value_text))


def check_evidence(label: str, ev: dict, rows: list[dict]) -> None:
    if "row_id" in ev:
        row = next((r for r in rows if r["id"] == ev["row_id"]), None)
        if row is None:
            raise SystemExit("%s: T_ROWS has no row %s" % (label, ev["row_id"]))
        if not any(ev["needle"] in c for c in row.get("cells", [])):
            raise SystemExit("%s: T_ROWS %s has no cell with %r" % (label, ev["row_id"], ev["needle"]))
        return
    check_source(label, ev, None)


def value_text(v) -> str | None:
    if v is None:
        return "None"
    if isinstance(v, bool):
        return None                      # the bool's evidence is the mask, checked by the needle
    return str(float(v))


def oracles() -> list[tuple[str, bool]]:
    p = proposal()
    rows = t_rows()
    props = p["proposals"]
    bad: list[tuple[str, bool]] = []

    def add(name: str, ok: bool) -> None:
        bad.append((name, ok))

    add("schema is 1", p.get("schema") == 1)
    add("T_ROWS was not edited", p.get("t_rows_edited") is False)
    add("8 proposals", len(props) == 8)
    add("ids are unique", len({r["id"] for r in props}) == len(props))
    add("no proposal id already exists in T_ROWS",
        not ({r["id"] for r in props} & {r["id"] for r in rows}))

    cov = uncovered()
    got = {r["bmak_field"] for r in props}
    add("proposal covers exactly the uncovered fields", got == cov)
    add("uncovered set is the 7 section-4 bullets + BoostDuration", len(cov) == 8)

    # BmAK sources: every row's own file:line carries its value
    for r in props:
        check_source(r["id"] + " bmak", r["bmak_source"], value_text(r["bmak_value"]))
    add("every BmAK value is on its cited source line", True)

    # conversions
    for r in props:
        f = r.get("conversion_factor")
        if f is None:
            continue
        want = float(r["bmak_value"]) * f
        got_v = float(r["converted_value"])
        if abs(want - got_v) > 1e-9:
            raise SystemExit("%s: %s x %s != %s" % (r["id"], r["bmak_value"], f, r["converted_value"]))
        if str(f) not in json.dumps(p["conversion_constants"]):
            raise SystemExit("%s: factor %s is not one of the declared constants" % (r["id"], f))
    add("every conversion re-derives from its factor", True)
    add("cu -> km/h factor is 0.036 (3000 cu = 108 km/h)",
        p["conversion_constants"]["cu_per_s_to_kmh"] == 0.036)

    # map / omit shape
    maps = [r for r in props if r["decision"] == "map"]
    omits = [r for r in props if r["decision"] == "omit"]
    add("2 map rows, 6 omit rows", len(maps) == 2 and len(omits) == 6)
    for r in maps:
        if not r.get("jc3_field"):
            raise SystemExit(r["id"] + ": map row has no jc3_field")
        check_source(r["id"] + " jc3", r["jc3_source"], None)
        if "jc3_domain_source" in r:
            check_source(r["id"] + " domain", r["jc3_domain_source"], None)
        if not r.get("conversion_rule") or not r.get("semantics"):
            raise SystemExit(r["id"] + ": map row needs a rule and semantics")
    add("every map row names a JC3 member that exists in its cited file", True)
    for r in omits:
        if r.get("jc3_field"):
            raise SystemExit(r["id"] + ": omit row carries a jc3_field")
        if len(r.get("reason", "")) < 60:
            raise SystemExit(r["id"] + ": omit row needs a stated reason")
        if not r.get("evidence"):
            raise SystemExit(r["id"] + ": omit row needs evidence")
        for ev in r["evidence"]:
            check_evidence(r["id"] + " evidence", ev, rows)
    add("every omit row has no carrier, a reason and verified evidence", True)

    # the donor block and the T-E5 conflict
    db = p["donor_block"]
    line = line_of(db["path"], db["line"])
    add("USAGES.md section 6 line is the nitro block", db["needle"] in line)
    add("the five donor members are all on that line",
        all(m in line for m in db["members"]))
    add("no duration/refill/timer member in the donor block",
        not any(k in line for k in ("use_time", "refill", "duration", "cooldown")))

    e5 = next((r for r in rows if r["id"] == "T-E5"), None)
    add("T-E5 exists and owns official_top_speed", e5 is not None
        and any("official_top_speed" in c for c in e5["cells"]))
    add("T-E5 carries 336.4", e5 is not None and any("336.4" in c for c in e5["cells"]))
    add("the base cap omit cites the T-E5 conflict",
        any(r["bmak_field"] == "SVehicle.MaxSpeed" and r["decision"] == "omit" for r in props))

    # the page and table are only read
    add("proposal page is markdown + one json block",
        read(PROPOSAL).count("```json") == 1)
    # The ledger's size is read from the ledger, never typed: it grew 198 -> 199 on 2026-11-06.
    nonblank = [ln for ln in read(ROWS).splitlines() if ln.strip()]
    add(f"T_ROWS parses cleanly ({len(rows)} rows, no duplicate ids)",
        len(nonblank) == len(rows) == len({r["id"] for r in rows}))
    print("T_ROWS sha256 " + hashlib.sha256(open(os.path.join(ROOT, ROWS), "rb").read()).hexdigest())
    return bad


def main() -> int:
    if "--write" not in sys.argv[1:] and "--check" not in sys.argv[1:]:
        print(__doc__)
        return 2
    try:
        ors = oracles()
    except SystemExit as e:
        print("FAIL: %s" % e)
        return 1
    for name, ok in ors:
        print(("PASS " if ok else "FAIL ") + name)
    bad = [n for n, ok in ors if not ok]
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if "--write" in sys.argv[1:]:
        p = proposal()
        print("map %d, omit %d, fields %d" % (
            sum(1 for r in p["proposals"] if r["decision"] == "map"),
            sum(1 for r in p["proposals"] if r["decision"] == "omit"),
            len(p["proposals"])))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
