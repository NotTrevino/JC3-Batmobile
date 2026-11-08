#!/usr/bin/env python3
"""t_vnf_six.py - the six VALUE-NOT-FOUND rows of the first audit, explained and re-cited.

`Working/Translation/ROW_EVIDENCE_AUDIT.md` reports six rows whose cited file does not carry
the quoted value: T-M1, T-E2, T-B4, T-A1, T-L3, T-L5. This script re-derives those six with
the *same* grading helpers (it imports `Tools/scripts/t_row_evidence.py`), opens the cited
files, records the nearest value each file does hold, classifies the mismatch, and prints a
proposed corrected row as JSON - in the document, never applied to `T_ROWS.jsonl`.

Classifications (one per row):
  wrong citation        the quoted value exists, in a different file (named)
  wrong value           the cited file holds a different number (named)
  unit/format difference  the same fact in another form (glob vs expanded name, pattern, unit)

Read-only: the ledger, the first script and the first audit are opened, never written.

    python Tools/scripts/t_vnf_six.py --write
    python Tools/scripts/t_vnf_six.py --check
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t_row_evidence as E  # noqa: E402  - the first audit's own grading helpers

LEDGER = E.LEDGER
OUT = os.path.join(ROOT, "Working", "Translation", "VALUE_NOT_FOUND_SIX.md")
FIRST_AUDIT = E.OUT
# sha256 of the ledger this sheet was written from (199 rows since 2026-11-06; the earlier pin
# was the 198-row file).  `--check` still fails if the ledger moves after the sheet was written.
LEDGER_SHA = "220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a"
SIX = ["T-M1", "T-E2", "T-B4", "T-A1", "T-L3", "T-L5"]
# How each of the audit's six stands against the 199-row ledger (2026-11-06).  T-E2 and T-B4 were
# re-cited and moved to `next` after the audit, so they no longer resolve and grade OK; the other
# four still grade VALUE-NOT-FOUND.  Stated per row instead of pinning one aggregate membership,
# so a row that changes again fails by name.
NOW = {
    "T-M1": "VALUE-NOT-FOUND", "T-A1": "VALUE-NOT-FOUND",
    "T-L3": "VALUE-NOT-FOUND", "T-L5": "VALUE-NOT-FOUND",
    "T-E2": "left the resolved set (dispo `next`)",
    "T-B4": "left the resolved set (dispo `next`)",
}
# The six VALUE-NOT-FOUND rows the same rule now finds in the first 40 resolved rows.
CURRENT_SIX = ["T-A1", "T-L3", "T-L5", "T-M1", "T-MA1", "T-MA2"]

_raw_cache: dict[str, str] = {}


def raw(rel: str) -> str:
    if rel not in _raw_cache:
        _raw_cache[rel] = open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()
    return _raw_cache[rel]


def line_of(rel: str, needle: str) -> int:
    for i, line in enumerate(raw(rel).splitlines(), start=1):
        if needle in line:
            return i
    return 0


def evaluate(row: dict, index: dict, opened: dict) -> tuple[str, str]:
    """The first audit's status rule, applied to one row (same branches, same vocabulary)."""
    refs = E.refs_of(row)
    strong, weak = E.numbers_of(row)
    members = E.members_of(row)
    paths = []
    for ref in refs:
        direct = os.path.join(ROOT, ref)
        if os.path.isfile(direct):
            paths.append({"ref": ref, "path": os.path.relpath(direct, ROOT).replace("\\", "/"),
                          "how": "direct", "candidates": 1,
                          "file": opened.setdefault(direct, E.File(direct))})
            continue
        cand = sorted(index.get(os.path.basename(ref), []))
        if not cand:
            paths.append({"ref": ref, "path": None, "how": "dead", "candidates": 0, "file": None})
            continue
        files = [opened.setdefault(p, E.File(p)) for p in cand]
        if len(files) == 1:
            paths.append({"ref": ref, "path": os.path.relpath(cand[0], ROOT).replace("\\", "/"),
                          "how": "basename", "candidates": 1, "file": files[0]})
            continue
        toks = strong or weak
        exact_of = {f.path: sum(1 for t in toks if f.grade(t) == E.EXACT) for f in files}
        scored = sorted(((exact_of[f.path], f.count(toks), f.path, f) for f in files),
                        key=lambda t: (t[0], t[1]), reverse=True)
        best = (scored[0][0], scored[0][1])
        winners = [t for t in scored if (t[0], t[1]) == best]
        if best != (0, 0) and len(winners) == 1:
            _e, _n, _p, f = winners[0]
            paths.append({"ref": ref, "path": os.path.relpath(f.path, ROOT).replace("\\", "/"),
                          "how": f"basename x{len(files)}, resolved by content", "candidates": len(files),
                          "file": f})
        else:
            f = files[0]
            paths.append({"ref": ref, "path": os.path.relpath(f.path, ROOT).replace("\\", "/"),
                          "how": f"AMBIGUOUS: {len(files)} candidates", "candidates": len(files),
                          "file": f})
    live = [p for p in paths if p["file"] is not None]

    def grade(tok):
        top = E.ABSENT
        for p in live:
            g = p["file"].grade(tok)
            if g > top:
                top = g
        return top

    graded = {tok: grade(tok) for tok in (strong or weak)}
    exact = [t for t, g in graded.items() if g == E.EXACT]
    rounded = [t for t, g in graded.items() if g == E.ROUNDED]
    absent = [t for t, g in graded.items() if g == E.ABSENT]
    member_hits = [t for t in members if grade(t) != E.ABSENT]
    dead = [p["ref"] for p in paths if p["path"] is None]

    if not refs:
        return "NO PATH", "the row names no file"
    if dead:
        return "DEAD PATH", "not found: " + ", ".join(dead)
    if graded and not absent and not rounded:
        return "OK", f"all {len(exact)} quoted number(s) found"
    if graded and not absent:
        return "OK (rounded)", f"{len(rounded)} by rounding"
    if graded and (exact or rounded):
        return "PARTIAL", "absent: " + ", ".join(absent[:5])
    if graded:
        return "VALUE-NOT-FOUND", "none of " + ", ".join(list(graded)[:4]) + " occurs"
    if members:
        if member_hits:
            return "OK (member name)", f"member name found: {member_hits[0]}"
        return "VALUE-NOT-FOUND", "none of the member names occurs: " + ", ".join(members[:3])
    return "NOT-TESTABLE", "nothing searchable"


# --------------------------------------------------------------------------- the six, by hand
# facts: (file, needle, what the line records). Every needle must be on disk (checked below).
# absent: (file, needle) that must NOT occur - that is the mismatch being explained.
ROWS: dict[str, dict] = {
    "T-M1": {
        "cls": "wrong citation",
        "why": ("4,000 kg is not a fleet value: it is `FITS.md`'s own evaluation mass (\"the fit "
                "evaluated at 4000 kg (the built Batmobile's mass)\"). `T3_FLEET.md` holds the "
                "band, and it does support the proposed 6,000 kg - that is the 3-8 t p75. The "
                "chain clause in the same cell cannot be checked in the cited `CHAIN.json`: that "
                "file contains no `mass` and no `Mass` substring at all (0/0), so the "
                "`BatmobileMassRatio` / `MassScale` / `InertiaTensorMultiplier` names it quotes "
                "are not in the chain grab."),
        "facts": [("Working/Translation/FITS.md", "4000", "the fit table's evaluation mass: '(the built Batmobile's mass)'"),
                  ("Working/Translation/T3_FLEET.md", "3500", "`rigid body mass`, 3-8 t p25"),
                  ("Working/Translation/T3_FLEET.md", "5100", "`rigid body mass`, 3-8 t median"),
                  ("Working/Translation/T3_FLEET.md", "6000", "`rigid body mass`, 3-8 t p75 = the proposed 6,000 kg")],
        "absent": [("Research/BatmobileGrab/CHAIN.json", "mass"),
                   ("Research/BatmobileGrab/CHAIN.json", "Mass")],
        "cells": {1: ("— (**no absolute mass tag**: the chain's only mass members are neutral "
                      "multipliers — `BatmobileMassRatio` 1.0, `MassScale` 1.0, "
                      "`InertiaTensorMultiplier` [1, 1, 1] — so the sim scales a mass the streams "
                      "never store; the 4,000 kg this table is evaluated at is `FITS.md`'s own "
                      "figure, `FITS.md`)")},
        "why_row": None,
    },
    "T-E2": {
        "cls": "wrong citation (the comparison base is also a stale number)",
        "why": ("1393.5 is a decoded build value, not a fleet statistic: the built module carries "
                "`torque_factor_at_optimal_rpm` = 1393.5245361328125 (`LEDGER_AUDIT.json`) and "
                "`current.json` stores 1393.52454, which is where the row's number is. `FITS.md` "
                "cannot carry it - it is a fit table. The row's comparison base is also off: it "
                "says \"the fit's 1,121 at 6 t\", but `FITS.md` holds neither `1,121` nor `1121`; "
                "its `torque at optimal rpm` row reads 834.1 at 4,000 kg, and its 6-15 t median is "
                "1,100, which is the base behind the row's own x1.27. So x1.24 belongs to a "
                "number the file does not contain."),
        "facts": [("Working/Translation/current.json", "1393.52454", "the built `torque_factor_at_optimal_rpm`, nearest to the quoted 1393.5"),
                  ("Working/Translation/LEDGER_AUDIT.json", "1393.5245361328125", "the module's own float, same value"),
                  ("Working/Translation/FITS.md", "834.1", "`torque at optimal rpm` fit, evaluated at 4,000 kg"),
                  ("Working/Translation/FITS.md", "1100", "`torque at optimal rpm` median, 6-15 t mass class"),
                  ("Working/Translation/FITS.md", "2500", "`torque at optimal rpm` median, 15 t+ (the row's 95th-percentile figure)")],
        "absent": [("Working/Translation/FITS.md", "1393.5"),
                   ("Working/Translation/FITS.md", "1,121"),
                   ("Working/Translation/FITS.md", "1121")],
        "cells": {5: ("keep 1393.5 — the built `land_engine.torque_factor_at_optimal_rpm` = "
                      "1393.52454 (`current.json`) — x1.67 over the fit's **834.1** at 4 t and "
                      "x1.27 over the 6-15 t median (1,100); inside the fleet's 95th percentile "
                      "(2,500) (`FITS.md`)")},
        "why_row": None,
    },
    "T-B4": {
        "cls": "unit/format difference",
        "why": ("The two quoted tokens are globs (`arcade.heat_boost.*`, `turbo_jump*`) and a "
                "glob is not a substring of anything, so the literal test can only fail. "
                "`VOCABULARY.md` lists the expanded members, all ten present, and the donor "
                "column is exactly the row's numbers: blend 0, extra 80, grip 1.5, torque 2. "
                "Second, smaller correction: the row says 'every shipped car carries them "
                "(n=145)' - 145 is the count for the five `arcade.heat_boost` rows; the five "
                "`turbo_jump` rows are n=35. The `turbo_jump` figures the row quotes (punch "
                "0.1 s / 50 km/h / top 200 km/h) are those rows' medians, not a donor column "
                "(that column is empty for them), so 'Serpente defaults' overstates them."),
        "facts": [("Research/JC3Grab/VOCABULARY.md", "arcade.heat_boost.boost_blend_time", "n=145, donor column 0"),
                  ("Research/JC3Grab/VOCABULARY.md", "arcade.heat_boost.extra_top_speed", "n=145, donor 80"),
                  ("Research/JC3Grab/VOCABULARY.md", "arcade.heat_boost.grip_multiplier", "n=145, donor 1.5"),
                  ("Research/JC3Grab/VOCABULARY.md", "arcade.heat_boost.torque_multiplier", "n=145, donor 2"),
                  ("Research/JC3Grab/VOCABULARY.md", "turbo_jump.punch_delay_time", "n=35, range 0 .. 0.1"),
                  ("Research/JC3Grab/VOCABULARY.md", "turbo_jump.top_speed_kph", "n=35, median 200")],
        "absent": [("Research/JC3Grab/VOCABULARY.md", "arcade.heat_boost.*"),
                   ("Research/JC3Grab/VOCABULARY.md", "turbo_jump*")],
        "cells": {2: ("`arcade.heat_boost.boost_blend_time`, `turbo_jump.punch_delay_time` "
                      "(the two globs expanded: five `arcade.heat_boost` rows, five `turbo_jump` "
                      "rows in the donor vocabulary)"),
                  5: ("keep the donor's defaults: **no BmAK source exists** (chain-proven: no "
                      "arcade heat-boost or turbo-jump member anywhere; `HeatSteam*` is exhaust "
                      "steam and `Jump*` is landing physics, not a boost) and every shipped car "
                      "carries them (`VOCABULARY.md`: five `arcade.heat_boost` rows n=145, donor "
                      "column blend 0 / extra 80 / grip 1.5 / torque 2; five `turbo_jump` rows "
                      "n=35, medians punch delay 0.1 s / 50 km/h / top 200 km/h)")},
        "why_row": None,
    },
    "T-A1": {
        "cls": "wrong citation",
        "why": ("6.63 is the decoded build value: `frontal_area` = 6.634666919708252 in the "
                "built `land_aerodynamics.vmodc` (`LEDGER_AUDIT.json`), stored as 6.63466692 in "
                "`current.json`. `T3_FLEET.md` holds the band the row argues against, not the "
                "value: 6.5 median and 6.72 p75 for 3-8 t, 6.95 for 6 t+, and no 6.63 anywhere "
                "(0 occurrences). Nearest values in the cited fleet file are 6.72 (0.09 above) "
                "and 6.5 (0.13 below)."),
        "facts": [("Working/Translation/LEDGER_AUDIT.json", "6.634666919708252", "the built module's `frontal_area`"),
                  ("Working/Translation/current.json", "6.63466692", "the same value as stored by the build"),
                  ("Working/Translation/T3_FLEET.md", "6.5", "`aero frontal area`, 3-8 t median"),
                  ("Working/Translation/T3_FLEET.md", "6.72", "`aero frontal area`, 3-8 t p75 - nearest to 6.63"),
                  ("Working/Translation/T3_FLEET.md", "6.95", "`aero frontal area`, 6 t+ median")],
        "absent": [("Working/Translation/T3_FLEET.md", "6.63"),
                   ("Working/Translation/FITS.md", "6.63")],
        "cells": {1: ("body cross-section 3.5 x 2.27 m (mesh); frontal area decoded "
                      "6.634666919708252 in the built `land_aerodynamics.vmodc` "
                      "(`LEDGER_AUDIT.json`, `current.json`)")},
        "why_row": None,
    },
    "T-L3": {
        "cls": "wrong citation",
        "why": ("`t2_lg2.py` is a script, not its output: it contains no `Rear_Break` (0 "
                "occurrences) and no graph name at all, because it reads them from the `.epe` "
                "and prints the difference under `graph_objects_unused`. The name it reasons "
                "about is decoded in the donor entity dump recorded in `LEDGER_AUDIT.json` "
                "(`..._debug.epe@0x2CF9: 'Rear_Break'`). Citing the probe instead of the dump "
                "is the whole of the mismatch."),
        "facts": [("Working/Translation/LEDGER_AUDIT.json", "'Rear_Break'", "the donor `.epe` dump: `..._debug.epe@0x2CF9: 'Rear_Break'`"),
                  ("Tools/scripts/t2_lg2.py", "graph_objects_unused", "the script's own reporting key - what it prints, not what it contains")],
        "absent": [("Tools/scripts/t2_lg2.py", "Rear_Break")],
        "cells": {2: ("the **5 `TailLight` rows** — JC3 has no separate brake row; `Rear_Break` "
                      "is in the graph but **no module row references it** (decoded in the donor "
                      "`.epe` dump, `LEDGER_AUDIT.json`; `t2_lg2.py` prints the unreferenced set)")},
        "why_row": None,
    },
    "T-L5": {
        "cls": "wrong citation",
        "why": ("Same shape as T-L3: `Front_Secondary_Head` is not in `t2_lg2.py` (0 "
                "occurrences); the script computes the unreferenced set and prints it. The name "
                "is decoded in the same donor `.epe` dump (`..._debug.epe@0x4F28: "
                "'Front_Secondary_Head'`, `LEDGER_AUDIT.json`), which is the citation the row "
                "wants."),
        "facts": [("Working/Translation/LEDGER_AUDIT.json", "'Front_Secondary_Head'", "the donor `.epe` dump: `..._debug.epe@0x4F28: 'Front_Secondary_Head'`"),
                  ("Tools/scripts/t2_lg2.py", "graph_objects_unused", "the script's reporting key, as for T-L3")],
        "absent": [("Tools/scripts/t2_lg2.py", "Front_Secondary_Head")],
        "cells": {2: ("`Front_Secondary_Head` exists in the graph and is **unreferenced** — this "
                      "rig has no secondary spot row (decoded in the donor `.epe` dump, "
                      "`LEDGER_AUDIT.json`; `t2_lg2.py` prints the unreferenced set)")},
        "why_row": None,
    },
}


def main(write: bool) -> int:
    checks = []

    def ok(cond, label, detail=""):
        checks.append({"oracle": label, "ok": bool(cond), "detail": detail})
        return bool(cond)

    rawb = open(LEDGER, "rb").read()
    sha = hashlib.sha256(rawb).hexdigest()
    rows = [json.loads(line) for line in rawb.decode("utf-8").splitlines() if line.strip()]
    by_id = {r["id"]: r for r in rows}
    resolved = [r for r in rows if r["dispo"] in E.RESOLVED]
    # The ledger's size is read from the file (198 -> 199 rows on 2026-11-06, so the old literal
    # was a stale pin, not a fact about the build).  What matters is that the file parses whole:
    # every non-blank line is one row, and no id repeats.
    content = rawb.decode("utf-8")
    nonblank = sum(1 for line in content.splitlines() if line.strip())
    ids = [r["id"] for r in rows]
    if not (nonblank == len(rows) == len(set(ids))):
        raise SystemExit(f"FAIL the ledger does not parse cleanly: {nonblank} non-blank lines, "
                         f"{len(rows)} rows, {len(set(ids))} unique ids")
    if not resolved:
        raise SystemExit("FAIL no row resolves under the first audit's rule")

    index = E.build_index()
    opened: dict[str, E.File] = {}
    statuses = {r["id"]: evaluate(r, index, opened) for r in resolved[:40]}
    vnf = sorted(k for k, (s, _n) in statuses.items() if s == "VALUE-NOT-FOUND")

    ok(sha == LEDGER_SHA, "T_ROWS.jsonl sha256 is the ledger this sheet was built from "
       f"({LEDGER_SHA[:16]}...)", sha)
    ok(nonblank == len(rows) == len(set(ids)),
       f"T_ROWS.jsonl parses cleanly: {len(rows)} rows, {len(resolved)} resolved, no duplicate ids",
       f"{nonblank} non-blank lines / {len(rows)} rows / {len(set(ids))} ids")
    ok(len(vnf) == 6, f"the first 40 resolved rows re-derive to 6 VALUE-NOT-FOUND ({len(vnf)})",
       str(vnf))
    ok(vnf == CURRENT_SIX,
       "that window now yields T-A1, T-L3, T-L5, T-M1, T-MA1, T-MA2 (T-E2/T-B4 re-cited to `next`)",
       str(vnf))
    for rid in SIX:
        st_now, _note = evaluate(by_id[rid], index, opened)
        dispo = by_id[rid]["dispo"]
        if dispo in E.RESOLVED:
            ok(st_now == NOW[rid], f"{rid} still grades {NOW[rid]} against this ledger", st_now)
        else:
            ok(NOW[rid].startswith("left"),
               f"{rid} left the resolved set (dispo `{dispo}`); the audit's finding was closed by a "
               f"row edit, not by this sheet", st_now)
    ok(len(ROWS) == 6 and sorted(ROWS) == sorted(SIX), "one analysis block per row")

    # every hand-written fact is on disk; every absence is real
    for rid, spec in ROWS.items():
        for rel, needle, _why in spec["facts"]:
            ok(os.path.isfile(os.path.join(ROOT, rel)) and line_of(rel, needle) > 0,
               f"{rid}: `{needle}` occurs in `{rel}`", rel)
        for rel, needle in spec["absent"]:
            ok(os.path.isfile(os.path.join(ROOT, rel)) and raw(rel).count(needle) == 0,
               f"{rid}: `{needle}` does not occur in `{rel}` (the mismatch)", rel)

    # build the proposals, and prove each one now grades as a hit
    proposals: dict[str, dict] = {}
    for rid, spec in ROWS.items():
        base = by_id[rid]
        row = json.loads(json.dumps(base))
        for i, text in spec["cells"].items():
            row["cells"][i] = text
        if spec["why_row"]:
            row["why"] = spec["why_row"]
        proposals[rid] = row

        ok(set(row) == set(base), f"{rid}: proposal keeps the ledger's keys")
        ok(all(row["cells"][i] == base["cells"][i] for i in range(len(base["cells"]))
               if i not in spec["cells"]),
           f"{rid}: only the cell(s) {sorted(spec['cells'])} change")
        ok(row["dispo"] == base["dispo"] and row["edits"] == base["edits"],
           f"{rid}: disposition and edit count untouched")
        after, note = evaluate(row, index, opened)
        ok(after not in ("VALUE-NOT-FOUND", "DEAD PATH", "NO PATH", "NOT-TESTABLE"),
           f"{rid}: proposed row grades `{after}` (was VALUE-NOT-FOUND)", note)
        for rel in E.refs_of(row):
            direct = os.path.join(ROOT, rel)
            ok(os.path.isfile(direct) or rel in index,
               f"{rid}: newly cited `{rel}` resolves", rel)

    ok(opened and all(os.path.isfile(p) for p in opened),
       f"every file opened for grading exists ({len(opened)} files)")

    # ------------------------------------------------------------------ the document
    tally: dict[str, int] = {}
    for spec in ROWS.values():
        tally[spec["cls"]] = tally.get(spec["cls"], 0) + 1

    L: list[str] = []
    ap = L.append
    ap("# The six VALUE-NOT-FOUND rows, explained")
    ap("")
    ap("Sequel to `Working/Translation/ROW_EVIDENCE_AUDIT.md`, which flags six of its first 40")
    ap("resolved rows with a cited file that does not carry the quoted value. This document")
    ap("opens each cited file, records the nearest value it actually holds, classifies the")
    ap("mismatch, and prints a proposed corrected row. **Nothing is applied**: the ledger is")
    ap(f"opened only (sha256 `{sha}`, unchanged; {len(rows)} rows, {len(resolved)} resolved), and")
    ap("`--check` re-derives this text.")
    ap("")
    ap("Classification vocabulary, one per row: **wrong citation** (the value exists, in another")
    ap("file, named), **wrong value** (the cited file holds a different number, named),")
    ap("**unit/format difference** (same fact, other form - glob vs expanded name, pattern, unit).")
    ap("")
    ap(f"**Six rows: {tally.get('wrong citation', 0) + tally.get('wrong citation (the comparison base is also a stale number)', 0)} "
       f"wrong citations, {tally.get('wrong value', 0)} wrong values, "
       f"{tally.get('unit/format difference', 0)} unit/format difference.**")
    ap("")
    ap("## Drift since the first audit (re-derived, not assumed)")
    ap("")
    ap(f"* the ledger now holds **{len(rows)} rows** (198 when the audit ran) and resolves "
       f"**{len(resolved)}** under the audit's own rule; the audit's header quotes 145 of 198.")
    ap("* `T-E2` and `T-B4` were re-cited and moved to `next` after the audit, so they no longer "
       "resolve and grade **OK** today - their mismatches were closed by a ledger edit, not here.")
    ap(f"* the first {E.PICK} resolved rows now produce **{len(vnf)}** VALUE-NOT-FOUND: "
       + ", ".join(f"`{i}`" for i in vnf)
       + "; `T-MA1`/`T-MA2` are outside this sheet's six and are recorded, not analysed.")
    ap("")
    ap("| row | dispo | what it quotes | citation | nearest value in the cited file | classification | now |")
    ap("|---|---|---|---|---|---|---|")
    short = {
        "T-M1": ("**4,000 kg**", "`CHAIN.json`, `T3_FLEET.md`",
                 "3-8 t: 3500 / 5100 / 6000 (p25/median/p75); 4000 is in `FITS.md`"),
        "T-E2": ("1393.5", "`FITS.md`",
                 "`torque at optimal rpm`: 834.1 at 4 t, 1100 for 6-15 t; 1393.5 is in `current.json`"),
        "T-B4": ("`arcade.heat_boost.*`, `turbo_jump*`", "`VOCABULARY.md`",
                 "the ten expanded member names, donor column 0 / 80 / 1.5 / 2"),
        "T-A1": ("6.63", "`T3_FLEET.md`, `FITS.md`",
                 "`aero frontal area`: 6.5 median, 6.72 p75, 6.95 6 t+; 6.63 is in `LEDGER_AUDIT.json`"),
        "T-L3": ("`Rear_Break`", "`t2_lg2.py`",
                 "the script holds no graph name; it prints `graph_objects_unused`; the name is in `LEDGER_AUDIT.json`"),
        "T-L5": ("`Front_Secondary_Head`", "`t2_lg2.py`",
                 "same script shape; name in `LEDGER_AUDIT.json`"),
    }
    for rid in SIX:
        what, cite, near = short[rid]
        ap(f"| `{rid}` | {by_id[rid]['dispo']} | {what} | {cite} | {near} | "
           f"{ROWS[rid]['cls']} | {NOW[rid]} |")
    ap("")
    for rid in SIX:
        spec = ROWS[rid]
        base = by_id[rid]
        ap(f"## {rid} - {spec['cls']}")
        ap("")
        ap("Row as it stands:")
        ap("")
        ap(f"* value cell: {base['cells'][4]}")
        ap(f"* `why`: {base.get('why', '')}")
        ap(f"* cited: " + ", ".join(f"`{r}`" for r in E.refs_of(base)))
        st_now, _note = evaluate(base, index, opened)
        ap(f"* grades against today's ledger: **{st_now}**"
           + ("" if base["dispo"] in E.RESOLVED
              else f" (dispo `{base['dispo']}`, outside the resolved set)"))
        ap("")
        ap("What the file(s) actually hold (needle, file, line, what the line records):")
        ap("")
        for rel, needle, why in spec["facts"]:
            ap(f"* `{needle}` - `{rel}` line {line_of(rel, needle)} - {why}")
        for rel, needle in spec["absent"]:
            ap(f"* **absent:** `{needle}` - `{rel}` (0 occurrences)")
        ap("")
        ap("Classification: **" + spec["cls"] + "**. " + spec["why"])
        ap("")
        ap("Proposed corrected row (JSON, **not applied**):")
        ap("")
        ap("```json")
        for line in json.dumps(proposals[rid], ensure_ascii=False, indent=1).splitlines():
            ap(line)
        ap("```")
        ap("")
        after, note = statuses.get(rid) or evaluate(proposals[rid], index, opened)
        ap(f"Re-graded with the first audit's own helpers: proposed row -> "
           f"**{evaluate(proposals[rid], index, opened)[0]}** (was VALUE-NOT-FOUND).")
        ap("")
    ap("## Cross-cutting findings")
    ap("")
    ap("* **`CHAIN.json` holds no mass member at all.** The cited chain grab contains 0")
    ap("  occurrences of `mass` and 0 of `Mass`, so T-M1's parenthetical (`BatmobileMassRatio`")
    ap("  1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1]) is not evidenced by the file")
    ap("  it names. Where those three names are decoded is left UNKNOWN here; the mass value the")
    ap("  row actually needs, 4000, is in `FITS.md`.")
    ap("* **A stale comparison number in T-E2.** `FITS.md` has neither `1,121` nor `1121`; its")
    ap("  6-15 t median is 1,100. The row's x1.27 is right against 1,100 (1393.5/1100 = 1.267);")
    ap("  its x1.24 is right against 1,121 (1393.5/1121 = 1.243), a base the file does not hold.")
    ap("  The fit's own value at 4,000 kg is 834.1, so a correct comparison is x1.67.")
    ap("* **A count that mixes two vocabularies in T-B4.** n=145 is the five `arcade.heat_boost`")
    ap("  rows; the five `turbo_jump` rows are n=35 and have an empty donor column, so their")
    ap("  figures are fleet medians rather than the quoted 'Serpente defaults'.")
    ap("* **Two rows cite a probe instead of a dump (T-L3, T-L5).** Both mismatches vanish when")
    ap("  the citation moves from `t2_lg2.py` to the decoded `.epe` dump in `LEDGER_AUDIT.json`;")
    ap("  the script's `graph_objects_unused` output is what the claim rests on, and a script is")
    ap("  not its output.")
    ap("* **One row is only a format artefact (T-B4).** A glob is never a substring, so the")
    ap("  literal test could never pass; the ten members are all present, with the exact donor")
    ap("  numbers the row quotes.")
    ap("")
    ap("## What this does not decide")
    ap("")
    ap("* **Whether each proposal is the editorial choice to take** - the corrections move")
    ap("  citations and one comparison number; the decided values (4,000 -> 6,000 kg, 1393.5,")
    ap("  6.63, the donor defaults) are left as the ledger has them.")
    ap("* **Where `BatmobileMassRatio` / `MassScale` / `InertiaTensorMultiplier` are decoded.**")
    ap("  Not in the cited chain grab; `Working/Translation/LEDGER_G3*.json` mention them, but")
    ap("  those are derived audits, not the chain. UNKNOWN.")
    ap("* **Whether `FITS.md` ever carried 1,121** (a different mass evaluation); the file today")
    ap("  holds 1,100 and 834.1 only. UNKNOWN.")
    ap("* **The runtime half of T-L3/T-L5** (\"no module row references it\") - only the decoded")
    ap("  preset ids can be checked; no game was run, the test ban stays.")
    ap("")
    ap("## Oracles re-run by `--check`")
    ap("")
    for c in checks:
        ap(f"* {'PASS' if c['ok'] else 'FAIL'} {c['oracle']}")
    ap("")
    ap("## Labels")
    ap("")
    ap("Decoded: the ledger rows, the quoted cells, every file's contents and the line numbers,")
    ap("the built values in `current.json` / `LEDGER_AUDIT.json`. Derived: the classifications,")
    ap("the ratios x1.67 / x1.27 / x1.24, the nearest-value statements, the proposed rows.")
    ap("UNKNOWN: the points listed under \"What this does not decide\".")
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
    print("PASS document: VALUE_NOT_FOUND_SIX.md matches the regenerated text")
    after_sha = hashlib.sha256(open(LEDGER, "rb").read()).hexdigest()
    if after_sha != sha:
        print("FAIL ledger changed during the run")
        return 1
    print("PASS ledger: sha256 unchanged after the run")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write VALUE_NOT_FOUND_SIX.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args()
    sys.exit(main(write=args.write))
