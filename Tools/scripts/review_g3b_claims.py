#!/usr/bin/env python3
"""review_g3b_claims.py - audit G3-20b's own verdicts against the cards it cites.

G3-20b (`Working/Translation/LEDGER_G3B.md/.json`, `Tools/scripts/ledger_g3b.py`) claims that of
G3-20's 18 keyword-matched rows only 6 HOLD, 9 cite the wrong card and 3 have the wrong value.
This review checks that claim the same way G3-20b checked G3-20: it opens every card the 10
checked rows cite, at the cited line, and asks

  * is the stored quote really a substring of that line?      (mechanical: what --check proves)
  * does that line carry the number the row itself states?     (what G3-20b's own HOLDS defines)
  * for three WRONG_CARD rows, does any card answer the row?

Writes:
    Working/Translation/REVIEW_G3B.md
    Working/Translation/REVIEW_G3B.json

Reads (never writes): Working/Translation/LEDGER_G3B.json and the cards below.

Usage:
    python Tools/scripts/review_g3b_claims.py --write
    python Tools/scripts/review_g3b_claims.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LEDGER = os.path.join(REPO, "Working", "Translation", "LEDGER_G3B.json")
OUT_MD = os.path.join(REPO, "Working", "Translation", "REVIEW_G3B.md")
OUT_JSON = os.path.join(REPO, "Working", "Translation", "REVIEW_G3B.json")

# The 6 HOLDS rows of the 105-row set, the 7th HOLDS row of the first pass (T-MD1, outside the
# three groups), and the 3 WRONG_VALUE rows.
CHECKED = [
    ("T-M1", "HOLDS", "105"),
    ("T-M4", "HOLDS", "105"),
    ("T-ST5", "HOLDS", "105"),
    ("T-B2", "HOLDS", "105"),
    ("T-PA3", "HOLDS", "105"),
    ("T-PA6", "HOLDS", "105"),
    ("T-MD1", "HOLDS", "first pass, outside the three groups"),
    ("T-MA1", "WRONG_VALUE", "105"),
    ("T-MA3", "WRONG_VALUE", "105"),
    ("T-MA4", "WRONG_VALUE", "105"),
]

# The three WRONG_CARD rows chased for an answering card, and where that card would have to be.
WRONG_CARD_CHASE = ["T-MA2", "T-P3", "T-CO1"]

# Verdict text per row - the human finding, keyed to the computed evidence in the same block.
FINDING = {
    "T-M1": ("holds for the card's census, not for the row's value: the line states 56 blocks and "
             "the total 1627.097155 (and line 54 the 800.0 block), which is exactly the "
             "'no single rigid-body mass' argument; the row's own 4,000 / 6,000 kg never appear "
             "on either cited line, and the 6,000 is a T3_FLEET.md class choice."),
    "T-M4": ("holds for the value's existence, not for the attribution: line 49 does carry "
             "`'25.0': 10`. The card never says those ten 25.0 blocks are wheels - it lists 56 "
             "anonymous shape-mass blocks by offset - so 'wheel mass = 25' is an inference the "
             "cited line does not make."),
    "T-ST5": ("holds exactly: line 317 decodes `DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) "
              "= 1.0, which is the row's source cell word for word. The row's 2.0 / 1.5 proposal "
              "is donor data and is not claimed from this card."),
    "T-B2": ("does NOT hold as cited: line 93 documents the boost *state bit* "
             "(`RBatmobileBooster.bBoosting` @2396, mask 1), while the row's quantity is an extra "
             "top speed computed from `FakeExtraSpeedMax` 3500 / `FakeExtaSpeedAccel` 600 / "
             "`BoostDuration` 2.0 - members that are not in SAMPLER_FIELDS2.md at all. They are "
             "in CLASS_DEFAULTS.md:265-266 (3500.0, 600.0); `BoostDuration` is in no .md card "
             "under Research/BatmobileGrab. By G3-20b's own definition this is the wrong card "
             "for the row's quantity."),
    "T-PA3": ("does NOT hold as cited: line 41 names the *body entry's* +0x0C word. The row is "
              "`parts[].world_collision_body_id` / `raycast_body_id` - a parts-table field, which "
              "G3-20b's own note points at PHYSICS_ROLES.md §2 / PARTS_TABLE.jsonl. The card "
              "supplies one end of the mapping, not the row."),
    "T-PA6": ("holds for the record shape, not for the row's count: line 25 states the 24-byte "
              "record and that no second body id is stored, and §1 lists 11 records (0..10, "
              "offsets 0x4880..0x4970). The row's claim is that `DeformPoints.constraint_indices` "
              "has 11 entries; the cited card does not read DeformPoints. The note's uncited "
              "G3-10d claim (constant 0 word = body 0 in 494/494) also contradicts the same "
              "card's 'partner is not stored'."),
    "T-MD1": ("holds: line 93 gives `bBoosting` @2396 mask 0x1 and line 37 gives "
              "`RPlayerInput.bVehicleBoostButton` @781, which are the row's two states."),
    "T-MA1": ("the WRONG_VALUE label is wrong for this row: its own value cell is a block count "
              "('17 blocks per LOD (16 CarPaintMM + 1 Window); 200 CarPaintMM + 35 Window across "
              "35 meshes'), not a colour, so a colour line cannot be its wrong *value* - by "
              "G3-20b's definitions this is a WRONG_CARD. The underlying fact stands (line 69 does "
              "not answer the row), but the row's 17 / 200 / 35 counts were never checked."),
    "T-MA3": ("holds: line 69 is the authored override [0.025787, 0.025787, 0.03, 1] and the row "
              "states the effective [0.056738, 0.05158, 0.06]; the card's §5 (line 228-230) and "
              "§6 item 1 (line 240) do say the combine rule is UNKNOWN (944 of 944 expression "
              "slots zero), so the card cannot supply the effective colour."),
    "T-MA4": ("the verdict is defensible but the citation is empty: line 25 is the section "
              "heading '## 2. Overrides carried by the chain's MICs (52)' - it carries no value. "
              "The numbers in the note are real but on other lines: Material0_Roughness 0.4 "
              "(MIC, line 33) and 0.25 (chain, line 111); Material0_Reflectivity 0.2 (line 32) "
              "and 0.25 (line 120). 'gloss' appears nowhere in COLOUR_PARAMS.md. Under G3-20b's "
              "definition (a different quantity) this is again a WRONG_CARD, not a WRONG_VALUE."),
}

# This review's own label, by G3-20b's own definitions.  "loose" = the cited line supports the row's
# source cell but never states the row's value; under G3-20b's wording ("the quoted line states
# what the row claims") that is not a HOLDS.
CORRECTED = {
    "T-M1": ("HOLDS (loose)", "the line proves the census, not the row's 4,000 / 6,000 kg"),
    "T-M4": ("HOLDS (loose)", "25.0 appears; the card never says those blocks are wheels"),
    "T-ST5": ("HOLDS", "the line states the row's 1.0"),
    "T-B2": ("WRONG_CARD", "the line documents the boost state bit, not the speed members"),
    "T-PA3": ("WRONG_CARD", "the line documents the body entry's word, not the parts field"),
    "T-PA6": ("HOLDS (loose)", "the record shape is stated; the row's 11 indices are not"),
    "T-MD1": ("HOLDS", "both offsets the row names are on the cited lines"),
    "T-MA1": ("WRONG_CARD", "the row's value is a block count, not a colour"),
    "T-MA3": ("WRONG_VALUE", "the card carries the authored colour, not the effective one"),
    "T-MA4": ("WRONG_CARD", "the card has no gloss parameter at all (and the line is a heading)"),
}

ANSWER_FINDING = {
    "T-MA2": ("partly answerable. `Research/BatmobileGrab/TEXTURES.md:15` names the texture the "
              "row's source cell names (`NEW_Batmobile_V2_BODY_D`, 4096x2048, bound as "
              "DiffuseColor of `Batmobile_Body_MASTER`), and `SLOTS.md:27` maps the CarPaintMM "
              "slot (2, `Batmobile_V3_Mainbody_NEW_MIC`) into that chain. The row's '28 Batmobile "
              "textures shipped' is in neither card: TEXTURES.md lists 405 texture rows across 5 "
              "packages."),
    "T-P3": ("answerable, and G3-20b's own routing names it: "
             "`Working/Translation/t16_collision.json` exists and carries `hull_set`, `bindings`, "
             "`decomposition`, `stations`, `donor_parts` - the hull set and slot binding the row "
             "asks for. So for this row a card does exist; G3-20b simply did not open it."),
    "T-CO1": ("partly answerable. `Research/JC3Grab/SHAPES.md` is the G2-8 card for the donor's "
              "`.physicsc` hulls (line 4: 233 entities, 18,865 convex hulls, 6,382 compounds, "
              "35,499 instance records) and it has a hull->part wiring section. But its vehicle "
              "table prints only the 80 largest hull bboxes, the Serpente is not one of them, and "
              "the per-entity JSON it points at (`Research/JC3Grab/_JC3grab/hkx/out/`) is not in "
              "the repository - so the donor's own hull list is not in the card."),
}


# --------------------------------------------------------------------------- helpers

def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read().splitlines()


def line_at(path, n):
    lines = read_lines(path)
    return lines[n - 1] if 1 <= n <= len(lines) else None


NUM = re.compile(r"\d[\d,_]*(?:\.\d+)?")


def numbers(text):
    out = []
    for m in NUM.finditer(text or ""):
        tok = m.group(0).rstrip(",.")
        if tok and tok not in out:
            out.append(tok)
    return out


def norm(tok):
    return str(tok).replace(",", "").replace("_", "")


def contains(text, tok):
    """Token test that ignores thousands separators on either side."""
    return norm(tok) in norm(text or "")


# The tokens each row's own value rests on.  Curated, not scraped: a scrape picks up incidental
# page numbers and one-digit part ids, which say nothing about whether the card answers the row.
VALUE_TOKENS = {
    "T-M1": [("4,000", "the row's 'now' mass"), ("6,000", "the row's proposed mass")],
    "T-M4": [("25", "the wheel mass the row quotes as its 'now'"),
             ("75", "the rear mass the row proposes")],
    "T-ST5": [("1.0", "the BmAK steering factor the row's source cites")],
    "T-B2": [("3500", "FakeExtraSpeedMax"), ("600", "FakeExtaSpeedAccel"),
             ("43.2", "the row's proposed km/h")],
    "T-PA3": [("world_collision_body_id", "the field the row targets"),
              ("raycast_body_id", "the field the row targets")],
    "T-PA6": [("11", "the constraint-index count the row states")],
    "T-MD1": [("2396", "the booster bit offset"), ("781", "the input byte offset")],
    "T-MA1": [("17", "the block count per LOD the row states")],
    "T-MA3": [("0.056738", "the effective colour the row states"),
              ("0.025787", "the authored override the card carries")],
    "T-MA4": [("0.45", "the gloss the row states")],
}

# Where a token that is absent from the cited line actually lives (searched, then quoted by line).
SEARCH_FILES = [
    "Working/Translation/T3_FLEET.md",
    "Research/BatmobileGrab/CLASS_DEFAULTS.md",
    "Research/BatmobileGrab/CLASS_DEFAULTS.json",
    "Research/BatmobileGrab/SPEEDOMETER.md",
    "Research/BatmobileGrab/SLOTS.json",
    "Research/JC3Grab/PARTS_TABLE.jsonl",
    "Research/BatmobileGrab/COLOUR_PARAMS.md",
]


def find_token(tok, skip=None):
    """First (file, line) among SEARCH_FILES that contains the token."""
    n = norm(tok)
    for rel in SEARCH_FILES:
        path = os.path.join(REPO, rel)
        if rel == (skip or "") or not os.path.exists(path):
            continue
        for i, line in enumerate(read_lines(path), 1):
            if n in norm(line):
                return {"file": rel, "line": i, "line_text": line}
    return None


def evidence_lines(evidence):
    """Every cited (file, line, quote) triple, with the line's text and the substring result."""
    out = []
    for e in evidence:
        path = os.path.join(REPO, e["file"])
        text = line_at(path, e["line"]) if os.path.exists(path) else None
        out.append({
            "file": e["file"], "line": e["line"], "quote": e["quote"],
            "card_exists": os.path.exists(path),
            "line_text": text,
            "quote_is_substring": bool(text is not None and e["quote"] in text),
            "is_heading": bool(text is not None and text.lstrip().startswith("#")),
        })
    return out


# --------------------------------------------------------------------------- build

def build():
    doc = json.load(open(LEDGER, encoding="utf-8"))
    rows = {r["id"]: r for r in doc["rows"]}
    first_pass = doc["first_pass"]

    def first_pass_row(rid):
        if rid in first_pass.get("verdicts", {}):
            return first_pass["verdicts"][rid]
        for r in first_pass.get("outside_groups", []):
            if r["id"] == rid:
                return {"was": r["was"], "now": r["now"], "note": r["note"],
                        "evidence": r.get("evidence", [])}
        return None

    checked = []
    for rid, status, where in CHECKED:
        r = rows.get(rid)
        fp = first_pass_row(rid) or {}
        evidence = (r["evidence"] if r else (fp.get("evidence") or []))
        ev = evidence_lines(evidence)
        cited_text = " ".join((e["line_text"] or "") for e in ev)
        tokens = []
        for tok, means in VALUE_TOKENS[rid]:
            here = contains(cited_text, tok)
            tokens.append({"token": tok, "means": means, "on_cited_line": here,
                           "found_at": None if here else find_token(
                               tok, skip=(ev[0]["file"] if ev else None))})
        checked.append({
            "row": rid, "g3b_status": status, "in": where,
            "target": (r or {}).get("target") or fp.get("target"),
            "now": (r or {}).get("now"),
            "source": (r or {}).get("source"),
            "proposed": (r or {}).get("proposed"),
            "first_pass": fp.get("was"),
            "evidence": ev,
            "value_tokens": tokens,
            "row_value_on_cited_line": all(t["on_cited_line"] for t in tokens),
            "row_value_partly_on_cited_line": any(t["on_cited_line"] for t in tokens),
            "citation_is_heading": any(e["is_heading"] for e in ev),
            "review_label": CORRECTED[rid][0],
            "review_label_why": CORRECTED[rid][1],
            "finding": FINDING[rid],
        })

    chase = []
    for rid in WRONG_CARD_CHASE:
        r = rows.get(rid) or {}
        answers = []
        if rid == "T-MA2":
            answers = [
                {"file": "Research/BatmobileGrab/TEXTURES.md", "line": 15,
                 "quote": "`NEW_Batmobile_V2_BODY_D` | 4096×2048"},
                {"file": "Research/BatmobileGrab/SLOTS.md", "line": 27,
                 "quote": "| 2 | `Batmobile_V3_Mainbody_NEW_MIC`"},
            ]
        elif rid == "T-P3":
            answers = []
        elif rid == "T-CO1":
            answers = [
                {"file": "Research/JC3Grab/SHAPES.md", "line": 4,
                 "quote": "**233 vehicle entities / 234 `.physicsc` files**"},
            ]
        answers = evidence_lines(answers)
        extra = {}
        if rid == "T-MA2":
            tex = read_lines(os.path.join(REPO, "Research", "BatmobileGrab", "TEXTURES.md"))
            body = [ln for ln in tex[6:] if ln.startswith("| ")]
            pkgs = sorted({ln.split("|")[1].strip() for ln in body})
            extra = {"textures_md_rows": len(body), "textures_md_packages": len(pkgs)}
        if rid == "T-P3":
            p = os.path.join(REPO, "Working", "Translation", "t16_collision.json")
            keys = list(json.load(open(p, encoding="utf-8")).keys()) if os.path.exists(p) else []
            extra = {"t16_collision_exists": os.path.exists(p), "t16_collision_keys": keys}
        if rid == "T-CO1":
            p = os.path.join(REPO, "Research", "JC3Grab", "_JC3grab", "hkx", "out")
            extra = {"per_entity_json_dir_exists": os.path.exists(p)}
        chase.append({
            "row": rid, "target": r.get("target"), "now": r.get("now"),
            "g3b_status": r.get("status"), "g3b_open_with": r.get("open_with"),
            "answering_card": answers, "extra": extra, "finding": ANSWER_FINDING[rid],
        })

    # ---- cross-checks that re-derive G3-20b's own arithmetic and its mechanical guarantee
    statuses = [r["status"] for r in doc["rows"]]
    tally = {s: statuses.count(s) for s in sorted(set(statuses))}
    fp_tally = {k: list(first_pass["verdicts"].values()).count(k)
                for k in ("HOLDS", "WRONG_CARD", "WRONG_VALUE")}
    fp_tally = {}
    for v in first_pass["verdicts"].values():
        fp_tally[v["now"]] = fp_tally.get(v["now"], 0) + 1
    for v in first_pass.get("outside_groups", []):
        fp_tally[v["now"]] = fp_tally.get(v["now"], 0) + 1
    all_quotes = [e for r in doc["rows"] for e in r["evidence"]]
    all_quotes += [e for r in first_pass.get("outside_groups", []) for e in r.get("evidence", [])]
    quote_ok = 0
    quote_total = 0
    for e in all_quotes:
        path = os.path.join(REPO, e["file"])
        quote_total += 1
        if os.path.exists(path):
            text = line_at(path, e["line"])
            if text is not None and e["quote"] in text:
                quote_ok += 1
    # the T-M1 mass histogram on PHYSICS_ROLES2.md:49 vs the total on :48
    hist_line = line_at(os.path.join(REPO, "Research", "JC3Grab", "PHYSICS_ROLES2.md"), 49) or ""
    pairs = re.findall(r"'([\d.]+)': *(\d+)", hist_line)
    hist_sum = sum(float(v) * int(n) for v, n in pairs)
    hist_count = sum(int(n) for _v, n in pairs)
    total_line = line_at(os.path.join(REPO, "Research", "JC3Grab", "PHYSICS_ROLES2.md"), 48) or ""
    stated = re.search(r"\*\*([\d.]+)\*\*", total_line)
    stated_total = float(stated.group(1)) if stated else None

    notes = [
        {"note": "T-M1's cited total cannot be rebuilt from the histogram quoted next to it",
         "detail": ("PHYSICS_ROLES2.md:48 states the total %s; the histogram on :49 lists %d of the "
                    "56 masses and sums to %.6f, leaving %.6f on %d values that line does not "
                    "enumerate (the 275.0 of the first-eight list on :47 is one of them). The "
                    "cited lines are correct; they are just not sufficient on their own."
                    % (stated_total, hist_count, hist_sum,
                       (stated_total - hist_sum) if stated_total is not None else float("nan"),
                       56 - hist_count))},
        {"note": "G3-20b's §4 routing names `PARTS_TABLE.jsonl` without its directory",
         "detail": ("the file is Research/JC3Grab/PARTS_TABLE.jsonl; Research/BatmobileGrab has no "
                    "PARTS_TABLE.jsonl, so a reader following §4 from the BatmobileGrab listing "
                    "finds nothing")},
    ]

    cross = [
        {"check": "row statuses sum to the 105-row set",
         "detail": "%d rows; %s" % (len(doc["rows"]), tally),
         "ok": len(doc["rows"]) == 105 and sum(tally.values()) == len(doc["rows"])},
        {"check": "the 18 first-pass rows tally as 6 HOLDS / 9 WRONG_CARD / 3 WRONG_VALUE",
         "detail": "%s over %d verdicts + %d outside-group rows"
                   % (fp_tally, len(first_pass["verdicts"]),
                      len(first_pass.get("outside_groups", []))),
         "ok": fp_tally == {"HOLDS": 6, "WRONG_CARD": 9, "WRONG_VALUE": 3}},
        {"check": "every stored quote is a substring of the line it names",
         "detail": "%d/%d quotes present" % (quote_ok, quote_total),
         "ok": quote_ok == quote_total and quote_total > 0},
        {"check": "the T-M1 total quoted by G3-20b is the number on the cited line",
         "detail": "PHYSICS_ROLES2.md:48 total %s, quote present: %s"
                   % (stated_total, "1627.097155" in total_line),
         "ok": stated_total == 1627.097155 and "1627.097155" in total_line},
    ]

    n_checked = len(checked)
    n_value_on_line = sum(1 for c in checked if c["row_value_on_cited_line"])
    n_value_partly = sum(1 for c in checked if c["row_value_partly_on_cited_line"])
    n_heading = sum(1 for c in checked if c["citation_is_heading"])
    relabel = {k: sum(1 for c in checked if c["review_label"].startswith(k))
               for k in ("HOLDS", "WRONG_CARD", "WRONG_VALUE")}
    kept = sum(1 for c in checked if c["review_label"] == c["g3b_status"])
    n_loose = sum(1 for c in checked if c["review_label"] == "HOLDS (loose)")
    return {
        "tool": "review_g3b_claims.py",
        "subject": {"ledger": "Working/Translation/LEDGER_G3B.json",
                    "report": "tmp/freebuff/reports/G3-20b.md"},
        "verdict": {
            "short": (
                f"On the {n_checked} rows checked, {kept} keep exactly the label G3-20b gave them "
                f"({relabel['HOLDS'] - n_loose} strict HOLDS, {relabel['WRONG_VALUE']} WRONG_VALUE); "
                f"{n_loose} more are HOLDS only loosely - the cited line proves the row's source "
                f"cell but never states the row's value; {n_checked - kept - n_loose} rows change "
                f"class, all in the same direction, a line being cited for a quantity it does not carry "
                f"(2 HOLDS cite a different quantity, 2 WRONG_VALUE cite a different quantity "
                f"rather than a different value), and {n_heading} of the {n_checked} citations is a "
                f"section heading; every stored quote (12/12) is a genuine line substring, so its "
                f"--check works but cannot detect a citation that carries no value"),
            "checked_rows": n_checked,
            "row_value_on_cited_line": n_value_on_line,
            "row_value_partly_on_cited_line": n_value_partly,
            "citations_that_are_headings": n_heading,
            "labels_kept": kept,
            "review_labels": relabel,
        },
        "checked_rows": checked,
        "wrong_card_chase": chase,
        "cross_checks": cross,
        "notes": notes,
        "readme": {
            "definitions_from_g3_20b": {
                "HOLDS": "the quoted line states what the row claims (LEDGER_G3B.md §1)",
                "WRONG_VALUE": "the card's number is not the row's number (§1)",
                "WRONG_CARD": "the card answers a different question than the row asks (§1)",
            },
            "limit": ("this review judges the card/row pair only; a row can be right about the game "
                      "and still be answered by the wrong card"),
        },
    }


# --------------------------------------------------------------------------- render

def cell(text, n=150):
    t = " ".join(str(text or "").split())
    return t if len(t) <= n else t[:n - 1] + "…"


def render(d):
    L = []
    A = L.append
    v = d["verdict"]
    A("# Review of G3-20b's ledger verdicts")
    A("")
    A("**VERDICT: partially supported.** %s." % v["short"])
    A("")
    A("Checked: the 6 HOLDS rows of the 105-row set, the first pass's 7th HOLDS row (`T-MD1`,")
    A("outside the three groups) and the 3 WRONG_VALUE rows — 10 rows, every cited line re-opened.")
    A("Three WRONG_CARD rows were then chased for an answering card.")
    A("")
    A("| | count |")
    A("|---|---:|")
    A("| rows checked | %d |" % v["checked_rows"])
    A("| rows whose *whole* stated value is on a cited line | %d |" % v["row_value_on_cited_line"])
    A("| rows with at least one stated value on a cited line | %d |"
      % v["row_value_partly_on_cited_line"])
    A("| citations that are section headings, not values | %d |" % v["citations_that_are_headings"])
    A("")
    A("## 1. The 10 rows, line by line")
    A("")
    A("| row | G3-20b | this review | quoted line | quote is a substring | the row's own value on that line |")
    A("|---|---|---|---|---|---|")
    for c in d["checked_rows"]:
        ev = c["evidence"][0] if c["evidence"] else None
        if c["row_value_on_cited_line"]:
            verdict = "yes"
        elif c["row_value_partly_on_cited_line"]:
            verdict = "partly (" + ", ".join("%s %s" % (t["token"], "yes" if t["on_cited_line"] else "no")
                                             for t in c["value_tokens"]) + ")"
        else:
            verdict = "no"
        A("| %s | %s | %s | `%s:%s` | %s | %s |"
          % (c["row"], c["g3b_status"], c["review_label"],
             ev["file"].split("/")[-1] if ev else "-", ev["line"] if ev else "-",
             ("yes" if all(e["quote_is_substring"] for e in c["evidence"]) else "NO")
             if c["evidence"] else "no line cited",
             verdict))
    A("")
    for c in d["checked_rows"]:
        A("### %s — `%s` (%s)" % (c["row"], cell(c["target"], 90), c["g3b_status"]))
        A("")
        A("row says (now): %s" % cell(c["now"], 220))
        if c["proposed"]:
            A("row proposes : %s" % cell(c["proposed"], 220))
        A("")
        for e in c["evidence"]:
            A("cited `%s:%d`%s:" % (e["file"], e["line"],
                                    " (HEADING)" if e["is_heading"] else ""))
            A("")
            A("```")
            A((e["line_text"] or "<line missing>").rstrip())
            A("```")
            A("")
            A("quote present: **%s**%s" % (e["quote_is_substring"],
                                           "" if e["quote_is_substring"]
                                           else " — the stored quote is not in this line"))
        A("")
        A("the row's own tokens:")
        A("")
        A("| token | what it is | on the cited line | found at |")
        A("|---|---|---|---|")
        for t in c["value_tokens"]:
            A("| `%s` | %s | %s | %s |"
              % (t["token"], t["means"], "yes" if t["on_cited_line"] else "no",
                 "—" if not t["found_at"] else "`%s:%d`" % (t["found_at"]["file"],
                                                             t["found_at"]["line"])))
        A("")
        A("this review's label: **%s** — %s" % (c["review_label"], c["review_label_why"]))
        A("")
        A("finding: %s" % c["finding"])
        A("")
    A("## 2. The three WRONG_CARD rows: is there a card that does answer them?")
    A("")
    for c in d["wrong_card_chase"]:
        A("### %s — `%s`" % (c["row"], cell(c["target"], 90)))
        A("")
        A("row says (now): %s" % cell(c["now"], 220))
        A("G3-20b routed it to: `%s`" % c["g3b_open_with"])
        A("")
        for e in c["answering_card"]:
            A("answering card `%s:%d`:" % (e["file"], e["line"]))
            A("")
            A("```")
            A((e["line_text"] or "<line missing>").rstrip())
            A("```")
            A("")
        if c["extra"]:
            A("checked: %s" % json.dumps(c["extra"], sort_keys=True))
            A("")
        A("finding: %s" % c["finding"])
        A("")
    A("## 3. Cross-checks of G3-20b's own arithmetic")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for c in d["cross_checks"]:
        A("| %s | **%s** | %s |" % (c["check"], "PASS" if c["ok"] else "FAIL", c["detail"]))
    A("")
    A("## 3b. Notes")
    A("")
    for n in d["notes"]:
        A("- **%s** — %s" % (n["note"], n["detail"]))
    A("")
    A("## 4. Definitions this review uses")
    A("")
    for k, t in d["readme"]["definitions_from_g3_20b"].items():
        A("- **%s** — %s" % (k, t))
    A("")
    A("Limit: %s." % d["readme"]["limit"])
    A("")
    A("## 5. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/review_g3b_claims.py --write")
    A("python Tools/scripts/review_g3b_claims.py --check")
    A("```")
    A("")
    return "\n".join(L)


# --------------------------------------------------------------------------- cli

def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1) + "\n"
    failed = [c for c in doc["cross_checks"] if not c["ok"]]

    if a.write:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote REVIEW_G3B.md and REVIEW_G3B.json (%d rows checked, %d with the row's value "
              "on the cited line, %d heading citations, %d/%d cross-checks)"
              % (doc["verdict"]["checked_rows"], doc["verdict"]["row_value_on_cited_line"],
                 doc["verdict"]["citations_that_are_headings"],
                 len(doc["cross_checks"]) - len(failed), len(doc["cross_checks"])))
        for c in failed:
            print("FAILED CROSS-CHECK: %s -> %s" % (c["check"], c["detail"]))
        return 0 if not failed else 1

    ok = True
    for path, text, what in ((OUT_MD, md, "md"), (OUT_JSON, js, "json")):
        if not os.path.exists(path):
            print("MISSING: %s" % path)
            ok = False
            continue
        old = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if old != text:
            print("MISMATCH: %s (recomputed %d bytes, stored %d bytes)" % (what, len(text), len(old)))
            ok = False
    for c in failed:
        print("FAILED CROSS-CHECK: %s -> %s" % (c["check"], c["detail"]))
    print("%s: %s; rows %d, value-on-line %d, heading citations %d, cross-checks %d/%d"
          % ("OK" if ok and not failed else "BAD", doc["verdict"]["short"][:60],
             doc["verdict"]["checked_rows"], doc["verdict"]["row_value_on_cited_line"],
             doc["verdict"]["citations_that_are_headings"],
             len(doc["cross_checks"]) - len(failed), len(doc["cross_checks"])))
    return 0 if ok and not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
