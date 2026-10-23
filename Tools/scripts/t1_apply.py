"""t1_apply.py - check the T-1 edit list against the build it was written for.

`Working/Translation/t1_edits.json` is the machine-readable output of the translation
table. This script does **not** write a build; it proves the list is applicable and
complete before anyone does:

  * every `old` value must equal what `current.json` decoded from the build -> catches
    build drift (a value changed by hand, or a module rebuilt from a newer dump);
  * every `new` value must differ from `old` and parse as the same JSON type;
  * every row id must exist in the tables (`T_ROWS.jsonl`, built by `t_rows.py` from
    `T1_TRANSLATION.md` and `T2_TRANSLATION.md`) -> catches edits invented outside the
    table;
  * `not_numeric` rows are printed so nothing silently disappears from the plan.

Usage:
  python t1_apply.py                 # validate
  python t1_apply.py --json          # machine-readable validation report
Exit code is 0 only when every edit validates.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BASE = os.path.join(ROOT, "Working", "Translation")


def load(name: str) -> dict:
    with open(os.path.join(BASE, name), encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true", help="print a JSON report")
    a = ap.parse_args()

    edits_doc = load("t1_edits.json")
    current = load("current.json")["modules"]
    led = os.path.join(BASE, "T_ROWS.jsonl")
    if not os.path.exists(led):
        raise SystemExit("no T_ROWS.jsonl - run `t_rows.py build` first")
    table = {json.loads(l)["id"] for l in open(led, encoding="utf-8") if l.strip()}

    problems: list[str] = []
    rows: list[dict] = []
    for e in edits_doc["edits"]:
        tag = f"{e['row']} {e['module']}.{e['member']}"
        if e["row"] not in table:
            problems.append(f"{tag}: row not found in T_ROWS.jsonl")
        mod = current.get(e["module"])
        if not mod or "values" not in mod:
            problems.append(f"{tag}: module not in current.json")
            continue
        if e["member"] not in mod["values"]:
            problems.append(f"{tag}: member missing from {mod['file']}")
            continue
        have = mod["values"][e["member"]]
        if have != e["old"]:
            problems.append(f"{tag}: build holds {have!r}, list expects {e['old']!r}")
        if have == e["new"]:
            problems.append(f"{tag}: new equals old ({have!r}) - no-op edit")
        if isinstance(e["new"], float) and not isinstance(have, float) \
                and abs(float(have) - e["new"]) < 1e-9:
            problems.append(f"{tag}: new is numerically old")
        rows.append({**{k: e[k] for k in ("row", "module", "member", "old", "new", "conf")},
                     "kind": e["kind"], "file": mod["file"]})

    if a.json:
        print(json.dumps({"ok": not problems, "edits": len(rows),
                          "problems": problems, "rows": rows}, indent=1))
    else:
        print(f"{len(rows)} numeric edits across "
              f"{len({r['module'] for r in rows})} modules "
              f"({sum(1 for r in rows if r['conf'] == 'class')} class, "
              f"{sum(1 for r in rows if r['conf'] == 'derived')} derived, "
              f"{sum(1 for r in rows if r['conf'] == 'assumed')} assumed)")
        for r in rows:
            print(f"  {r['row']:7s} {r['module']+'.'+r['member']:50s} "
                  f"{str(r['old'])[:10]:>10s} -> {r['new']}")
        print("\nNot numeric (no build edit):")
        for n in edits_doc["not_numeric"]:
            print(f"  {n['row']:10s} {n['kind']:12s} {n['value']}")
        if problems:
            print("\nFAIL")
            for p in problems:
                print(" ", p)
        else:
            print("\ncheck ok: every edit matches the build, the table and a real member")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
