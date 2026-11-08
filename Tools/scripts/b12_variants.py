"""
b12_variants.py - B-12: is the variant card live, and are its preconditions still unmet?

`GRAB_BACKLOG.md` §8 (`B-12`): "**Variants (only if D-2 = two variants)** ... `bm_build.py
--variant pursuit|battle` builds both entities from one source; the only differences are the rows
in `t11_variants.json`. **Done:** `aafdiff` between variants lists only the files the variant
table names."

The card's own precondition is "only if D-2 = two variants". D-2 is a user decision and it moved
twice: resolved to **(b) one hybrid car** on 2026-10-28 (the card was skipped), then **reopened on
2026-11-06** because BmAK has two modes and a hybrid cannot carry T-MD5/T-MD6/T-MD7/T-MD8/T-MD13/
T-MD14 (`tmp/freebuff/reports/apply-mode-switch-rows.md`). So the card is now a live `todo` with
four preconditions, and this reader re-derives the state of each from the files on disk instead of
trusting the prose (R11):

  1. **decision** - §11 D-2 still reads `REOPENED` (met once it reads a resolution to (a));
  2. **row sets** - `Working/Translation/t11_variants.json` still holds the one hybrid set T-15
     emitted (met once it declares two variant sets);
  3. **swap** - a runtime entity swap. Nothing on disk can settle this, so it is reported
     `UNKNOWN` every run and never counts as met: `tmp/freebuff/reports/mode-switch-carriers.md`
     §7 U1 (no decoded selector in any module, entity graph or `.physicsc`);
  4. **build surface** - `Tools/scripts/bm_build.py` registers no `--variant` and `Builds/` holds
     no variant-named tree (met once both exist).

It writes nothing. `--check` exits 0 when the register still reads reopened and **none** of the
four preconditions is met (the card is live and unbuilt), and non-zero as soon as one is met -
then the card is buildable and must be built, not left a todo - or when the register drifted back
to `skipped: D-2` without a recorded decision. The path arguments exist so a tamper test can point
the same check at a copy.

Usage:
    python Tools/scripts/b12_variants.py --check
    python Tools/scripts/b12_variants.py --check --variants <copy.json>
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

VARIANTS = os.path.join(ROOT, "Working", "Translation", "t11_variants.json")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
BUILD_SCRIPT = os.path.join(HERE, "bm_build.py")
BUILDS = os.path.join(ROOT, "Builds")

REOPENED = "REOPENED 2026-11-06"
CARD_MARKERS = (
    ("Preconditions", "the card lists its preconditions"),
    ("(a) two variants", "the decision it waits for is named"),
    ("two row sets", "T-15's re-run is a precondition"),
    ("runtime entity swap", "the missing selector is named"),
    ("--variant pursuit|battle", "the build surface it needs is named"),
)


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def load_variants(path: str) -> tuple[dict | None, str | None]:
    if not os.path.exists(path):
        return None, f"no variant table at {rel(path)}"
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh), None
    except json.JSONDecodeError as exc:
        return None, f"{rel(path)} is not JSON: {exc}"


def read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def d2_row(path: str) -> tuple[str | None, str | None]:
    """The single `| D-2 |` row of §11, as text."""
    if not os.path.exists(path):
        return None, f"no backlog at {rel(path)}"
    for line in read(path).splitlines():
        if line.startswith("| D-2 |"):
            return line, None
    return None, "no `| D-2 |` row in the decision register"


def b12_card(path: str) -> tuple[str | None, str | None]:
    """The §8 card block for B-12, from its heading to the next `#### ` heading."""
    if not os.path.exists(path):
        return None, f"no backlog at {rel(path)}"
    lines, on = read(path).splitlines(), False
    block: list[str] = []
    for line in lines:
        if line.startswith("#### B-12 "):
            on = True
            block.append(line)
            continue
        if on and line.startswith("#### "):
            break
        if on:
            block.append(line)
    if not block:
        return None, "no `#### B-12` card in §8"
    return "\n".join(block), None


def b12_tracker(path: str) -> str | None:
    for line in read(path).splitlines():
        if line.startswith("| B-12 |"):
            return line
    return None


def variant_option(path: str) -> tuple[bool, str | None]:
    """Does the build scaffold register a `--variant` argument?"""
    if not os.path.exists(path):
        return False, f"no build scaffold at {rel(path)}"
    for line in read(path).splitlines():
        if "add_argument(" in line and "variant" in line:
            return True, None
    return False, None


def named_builds(path: str) -> list[str]:
    """Variant-named trees under `Builds/`: flat (`bm-RC4-modes-battle`) or nested.

    B-12's pair lives in a container - `Builds/bm-RC4-modes/{pursuit,battle}/` - so the two trees
    sit side by side and the cross-variant `aafdiff` reads one `variant.json` from a sibling of
    the other. Counting only one level deep reported 0 trees while two existed.
    """
    if not os.path.isdir(path):
        return []
    out = []
    for n in sorted(os.listdir(path)):
        full = os.path.join(path, n)
        if not os.path.isdir(full):
            continue
        if re.search(r"pursuit|battle", n, re.I):
            out.append(n)
            continue
        for sub in sorted(os.listdir(full)):
            if (os.path.isdir(os.path.join(full, sub))
                    and re.search(r"pursuit|battle", sub, re.I)):
                out.append(f"{n}/{sub}")
    return out


def check(variants_path: str, backlog_path: str, script_path: str, builds_path: str) -> int:
    bad = 0
    met: list[str] = []

    table, err = load_variants(variants_path)
    if err:
        print(f"FAIL: {err}")
        return 1
    assert table is not None
    if table.get("schema") != 1:
        bad += 1
        print(f"FAIL: schema {table.get('schema')!r}, expected 1")

    variants = table.get("variants") or []
    split = table.get("split") or []
    counts = table.get("counts") or {}

    # --- the table is still the one-set record B-12 has to replace
    if len(variants) != 1:
        met.append(f"row sets (the table declares {len(variants)} variants)")
    for v in variants:
        vid = v.get("id")
        if vid != "hybrid":
            bad += 1
            print(f"FAIL: variant id {vid!r}, the one-set record is 'hybrid'")
        for key, want in (("entities", 1), ("drop_entries", 1)):
            if v.get(key) != want:
                bad += 1
                print(f"FAIL: variant {vid!r} {key} {v.get(key)!r}, the one-set record is {want}")
        if v.get("mode_switch") is not None:
            bad += 1
            print(f"FAIL: variant {vid!r} declares a mode_switch {v.get('mode_switch')!r}; "
                  f"no JC3 member carries one (`mode-switch-carriers.md` §2.7)")
        if v.get("B-12") != "todo: D-2 reopened":
            met.append(f"build surface (the table's B-12 field is {v.get('B-12')!r}, not a todo)")

    decision = (table.get("decision") or {}).get("D-2", "")
    if REOPENED not in decision:
        bad += 1
        print(f"FAIL: the table's D-2 record does not read {REOPENED!r}: {decision!r}")

    # --- the table's own arithmetic (the numbers a report may quote)
    if counts.get("rows") != len(split):
        bad += 1
        print(f"FAIL: counts.rows {counts.get('rows')!r} != {len(split)} split rows")
    for code in ("MOD-1", "MOD-2"):
        got = sum(1 for r in split if r.get("code") == code)
        if counts.get(code) != got:
            bad += 1
            print(f"FAIL: counts.{code} {counts.get(code)!r} != {got} re-counted rows")
    if not split:
        bad += 1
        print("FAIL: no split rows - nothing records what a two-variant build would have written")
    differs = [r.get("row") for r in split
               if json.dumps(r.get("pursuit"), sort_keys=True)
               != json.dumps(r.get("battle"), sort_keys=True)]
    for r in split:
        if not all(k in r for k in ("pursuit", "battle", "hybrid")):
            bad += 1
            print(f"FAIL: row {r.get('row')!r} is missing one of pursuit/battle/hybrid")

    # --- precondition 1: the decision register
    row, err = d2_row(backlog_path)
    if err:
        bad += 1
        print(f"FAIL: {err}")
    else:
        assert row is not None
        if REOPENED in row:
            pass                      # still open: precondition unmet, as expected
        elif "skipped: D-2" in row:
            bad += 1
            print("FAIL: §11 D-2 reads `skipped: D-2` again with no recorded decision - a reopen "
                  "does not revert silently; record the answer in §11 and MODLOG")
        elif "(a) two variants" in row:
            met.append("decision (§11 D-2 no longer reads reopened)")
        else:
            bad += 1
            print("FAIL: §11 D-2 is neither reopened, resolved to (a), nor skipped - re-read it")
        if "(b) one hybrid car" not in row:
            bad += 1
            print("FAIL: §11 D-2 dropped the 2026-10-28 answer instead of keeping it as history")

    # --- the card carries the preconditions this script checks
    card, err = b12_card(backlog_path)
    if err:
        bad += 1
        print(f"FAIL: {err}")
    else:
        assert card is not None
        for marker, why in CARD_MARKERS:
            if marker not in card:
                bad += 1
                print(f"FAIL: the B-12 card lost the marker {marker!r}: {why}")

    tr = b12_tracker(backlog_path)
    if tr is None:
        bad += 1
        print("FAIL: no `| B-12 |` row in the §12 tracker")
    elif not tr.startswith("| B-12 | todo"):
        bad += 1
        print(f"FAIL: the tracker's B-12 row is not a todo: {tr[:90]!r}")

    # --- precondition 4: the build surface
    has_flag, err = variant_option(script_path)
    if err:
        bad += 1
        print(f"FAIL: {err}")
    named = named_builds(builds_path)
    if has_flag or named:
        met.append(f"build surface (--variant registered: {has_flag}; variant-named trees: "
                   f"{len(named)})")

    # --- report
    v = variants[0] if len(variants) == 1 else {}
    print(f"{'FAIL' if bad else 'PASS'}: B-12 is live and unbuilt "
          f"- {len(variants)} variant ({v.get('id')}), {v.get('entities')} entity, "
          f"{v.get('drop_entries')} drop entry, 0 variant pair(s) to diff")
    print(f"  table    : {rel(variants_path)} - {len(split)} split rows "
          f"(MOD-1 {counts.get('MOD-1')}, MOD-2 {counts.get('MOD-2')}); "
          f"{len(differs)} row(s) where pursuit != battle")
    if differs:
        print(f"             {', '.join(str(x) for x in differs)}")
    print(f"  decision : backlog section 11, D-2 = reopened 2026-11-06 "
          f"(2026-10-28's (b) kept as history); card tag `B-12 todo: D-2 reopened`")
    print(f"  preconds : 1 decision reopened; 2 one row set; 3 swap UNKNOWN (U1); "
          f"4 --variant {has_flag}, {len(named)} variant-named tree(s)")
    print(f"  Done     : NOT RUNNABLE - `aafdiff` needs two entity trees and the table declares "
          f"{len(variants)}")
    if met:
        bad += 1
        print("FAIL: precondition(s) met, so the card is buildable and must not stay a todo: "
              + "; ".join(met))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="re-derive and compare (no writes)")
    ap.add_argument("--variants", default=VARIANTS, help="variant table (default the T-15 output)")
    ap.add_argument("--backlog", default=BACKLOG, help="backlog, for §11 D-2 and the §8 card")
    ap.add_argument("--build-script", default=BUILD_SCRIPT, help="build scaffold to inspect")
    ap.add_argument("--builds", default=BUILDS, help="build tree root")
    args = ap.parse_args()
    if not args.check:
        ap.print_help()
        print("\nthis reader has no write mode; pass --check")
        return 2
    return check(args.variants, args.backlog, args.build_script, args.builds)


if __name__ == "__main__":
    sys.exit(main())
