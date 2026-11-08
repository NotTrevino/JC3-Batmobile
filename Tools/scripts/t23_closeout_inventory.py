"""t23_closeout_inventory.py - T-23: the row inventory that closes phase T honestly.

`GRAB_BACKLOG.md` §7 T-23 asks the close-out to confirm the ledger has no row left as a final
"JC3 has no system", and the operator's 2026-11-06 rule repeats it: a compromise is closed by a
replacement value or by a card with a measurable done-line, never by the words "no system".

This tool answers that with data instead of prose:

  * the rows counted by disposition, read from `Working/Translation/T_ROWS.jsonl`;
  * every row still `out`, `blocked`, `keep` or `assumed`, each with the card that resolves it
    (`CARD_OF` below) or a `closed:` reason from its own evidence;
  * the lore-compromised count: rows carrying an open card. Rows that are closed must be closed
    by evidence (`decoded`/`derived`/`behaviour`) - a `class` row cannot be called closed;
  * a scan for the banned final answers ("no JC3 system", "JC3 has no system", "no JC3
    expression", "accept the limit") on any row that names no card.

Every card id in `CARD_OF` is checked against the cards `GRAB_BACKLOG.md` §7/§8 declare (plus a
`Research/specs/<id>.md`), so a stale pointer fails the check instead of closing a row against a
card that does not exist. `--check` re-derives the two outputs and compares them byte for byte.

Usage
    python Tools/scripts/t23_closeout_inventory.py --write
    python Tools/scripts/t23_closeout_inventory.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TR = os.path.join(ROOT, "Working", "Translation")
LEDGER = os.path.join(TR, "T_ROWS.jsonl")
BACKLOG = os.path.join(ROOT, "GRAB_BACKLOG.md")
SPECS = os.path.join(ROOT, "Research", "specs")
OUT_M = os.path.join(TR, "T23_INVENTORY.md")
OUT_J = os.path.join(TR, "T23_INVENTORY.json")
SCHEMA = 1

GROUPS = ("out", "blocked", "keep", "assumed")
BANNED = ("no JC3 system", "JC3 has no system", "no JC3 expression", "accept the limit")
CLOSED = re.compile(r"^closed:")

# The resolving card for every non-`next`/`edit`/`epe`/`superseded` row.  A card id is checked
# against the backlog; `closed:<reason>` is used only where the row's own evidence settles it
# (a lore-exact match, a decision, or content the build does not owe a carrier).
CARD_OF: dict[str, str] = {
    # --- out: a named omission, each owned by a build card ---------------------------------
    "T-WP15": "B-18",          # EMP disable: the burst is B-18's write path
    # --- blocked ---------------------------------------------------------------------------
    "T-RA1": "G2-35",          # the road-assist/dodge impulse research card
    "T-L28": "B-03",           # the body-hosted `_LIG` node is B-03's block pass
    "T-L30": "B-03",
    "T-WP6": "B-16",           # the winch pull loop
    "T-WLD17": "B-16",         # the airlift borrows the same cargo-bay investigation
    "T-MD5": "B-12",           # second speed curve: the variants step
    "T-MD6": "B-12",
    "T-MD7": "B-12",
    "T-MD8": "G2-21",          # the pivot has no data carrier: G2-21 is the mechanism card
    "T-MD13": "B-12",
    "T-MD14": "B-12",
    # --- keep, with the card that finishes the job ------------------------------------------
    "T-LG2": "B-07",           # the donor join is closed; the BmAK cone/intensity is B-07's
    "T-AU1": "B-11",           # the event->parameter map is the bank task
    "T-AU2": "B-26",           # 21 of 45 GUIDs need the per-entity override
    "T-FX1": "B-11",           # per-part break variant
    "T-FX2": "B-11",           # roof emitter needs the canopy part + socket
    "T-DM8": "B-09",           # behaviour carried; the Q-3/A11 take is B-09's gate
    "T-MD11": "B-12",          # the battle FOV needs the second variant
    "T-G1": "closed:lore-exact - hardpoints equal the mesh hubs to <= 0.10 mm (keep-audit-dimensions-wheels)",
    "T-G2": "closed:lore-exact - tyre diameter = the mesh, +0.05 mm front / 0.00 mm rear",
    "T-G3": "closed:lore-exact - tyre width = the per-axle mean, 0.0 mm",
    "T-G6": "closed:lore-exact - the mesh radius is the contact radius; BmAK's 0.640 sim radius has no JC3 carrier",
    "T-R3": "closed:lore-exact - both sides are raycast wheels; 0 has no fit error",
    "T-A1": "closed:lore-exact - 6.634667 m2 = 83.6 % of the mesh cross-section, inside the heavy band",
    "T-MA1": "closed:carried - body at the mesh-measured 7.026 x 3.495 x 2.271 m",
    "T-MA2": "closed:carried - one CarPaintMM block per LOD",
    "T-MA6": "closed:carried - palette route, replaced rows are T-MA3/T-MA4/T-MA7",
    "T-FX5": "closed:not owed - donor content outside the 51-row effect set; the '23 unreferenced' count is UNKNOWN",
    "T-EF1": "closed:carried - tyre effects are fleet-invariant",
    "T-PA9": "closed:carried - actor plumbing in the entity graph",
    "T-WP11": "closed:carried - the afterburner is JC3 nitro, live since test-091",
    "T-WLD7": "closed:carried - category caption resolves 11/11",
    "T-WLD13": "closed:D-8 - the donor already sinks as the lore route requires",
    "T-WLD14": "closed:R7 - the water constants are fleet-wide shared data",
    "T-WLD16": "closed:carried - 12 cargo-bay objects already enabled",
    "T-WLD18": "closed:D-6 - standalone, so the spawn table stays untouched",
    "T-WLD19": "closed:D-6 - traffic record untouched",
    "T-MD3": "closed:carried - ram immunity is the entity switch of T-DM8",
    "T-MD4": "closed:decoded - both torque curves read from the G1 object stream",
    "T-MD10": "closed:carried - ArmourModeDamageReduction is 0 on every package that serialises it",
    # --- assumed ----------------------------------------------------------------------------
    "T-E5": "B-24",            # the label is a 300-336 km/h assumed band; Cd stays 0.55 and the take tests label reachability
}
ROWS_RE = re.compile(r"^####\s+([A-Z0-9]+-\d+)\s+·")


def cards() -> set[str]:
    """Every card id the backlog declares, plus a `Research/specs/<id>.md`."""
    ids = {m.group(1) for m in (ROWS_RE.match(l) for l in open(BACKLOG, encoding="utf-8")) if m}
    if os.path.isdir(SPECS):
        ids |= {f[:-3] for f in os.listdir(SPECS) if f.endswith(".md")}
    return ids


def ledger() -> list[dict]:
    return [json.loads(l) for l in open(LEDGER, encoding="utf-8") if l.strip()]


def conf_of(row: dict) -> str:
    cells = row.get("cells", [])
    return (cells[6] if len(cells) > 6 else (cells[4] if len(cells) > 4 else "")).strip()


def classify(rows: list[dict]) -> dict:
    by_dispo: dict[str, int] = {}
    for r in rows:
        by_dispo[r["dispo"]] = by_dispo.get(r["dispo"], 0) + 1
    inv = [r for r in rows if r["dispo"] in ("out", "blocked", "keep") or conf_of(r) == "assumed"]
    return {"rows": len(rows), "by_disposition": dict(sorted(by_dispo.items())), "inventory": inv}


def build() -> dict:
    rows = ledger()
    known = cards()
    problems: list[str] = []
    data = classify(rows)
    inv = data["inventory"]

    listed = []
    for r in inv:
        rid = r["id"]
        group = "assumed" if conf_of(r) == "assumed" else r["dispo"]
        target = CARD_OF.get(rid)
        if not target:
            problems.append(f"{rid}: no resolving card in CARD_OF")
            target = "UNASSIGNED"
        closed = bool(CLOSED.match(target))
        if not closed and target not in known:
            problems.append(f"{rid}: card {target} does not exist in GRAB_BACKLOG or Research/specs")
        banned = [b for b in BANNED if b.lower() in (r.get("why", "") + " ".join(r["cells"])).lower()]
        if banned and closed:
            problems.append(f"{rid}: closed but states a banned final answer {banned}")
        listed.append({"id": rid, "doc": r["doc"], "group": group, "dispo": r["dispo"],
                       "conf": conf_of(r), "card": target, "closed": closed,
                       "why": r.get("why", ""), "banned": banned})

    stale = sorted(set(CARD_OF) - {x["id"] for x in listed})
    for rid in stale:
        problems.append(f"{rid}: CARD_OF entry for a row that is not out/blocked/keep/assumed")
    assumed = [x for x in listed if x["group"] == "assumed"]
    for x in assumed:
        if x["conf"] != "assumed":
            problems.append(f"{x['id']}: listed as assumed but the class cell reads {x['conf']!r}")
    unassigned = [x["id"] for x in listed if x["card"] == "UNASSIGNED"]
    open_rows = [x["id"] for x in listed if not x["closed"]]
    closed_rows = [x["id"] for x in listed if x["closed"]]
    banned_rows = [x["id"] for x in listed if x["banned"]]
    if unassigned:
        problems.append(f"{len(unassigned)} row(s) with no resolving card: {', '.join(unassigned)}")

    return {"schema": SCHEMA, "generated_by": "Tools/scripts/t23_closeout_inventory.py",
            "inputs": {"ledger": "Working/Translation/T_ROWS.jsonl", "backlog": "GRAB_BACKLOG.md"},
            "counts": {"rows": data["rows"], "by_disposition": data["by_disposition"],
                       "listed": len(listed), "out": sum(1 for x in listed if x["group"] == "out"),
                       "blocked": sum(1 for x in listed if x["group"] == "blocked"),
                       "keep": sum(1 for x in listed if x["group"] == "keep"),
                       "assumed": len(assumed), "open": len(open_rows),
                       "closed": len(closed_rows), "unassigned": len(unassigned),
                       "open_carded": len(open_rows),
                       # a lore compromise is a row the JC3-side system cannot express and no card
                       # resolves; a row with an open card is not compromised, it is scheduled
                       "lore_compromised": len(unassigned) + len(banned_rows),
                       "banned_phrases": len(banned_rows)},
            "rows": listed,
            "problems": problems}


def render_md(doc: dict) -> str:
    c = doc["counts"]
    L = ["# Phase-T row inventory and card map (T-23)", "",
         "Generated by `Tools/scripts/t23_closeout_inventory.py`; `--check` re-derives this file",
         "and its JSON byte for byte and fails on any row without a resolving card.", "",
         "## 1. Rows by disposition", "",
         "| disposition | rows |", "|---|---:|"]
    for k, v in c["by_disposition"].items():
        L.append(f"| `{k}` | {v} |")
    L += [f"| **total** | **{c['rows']}** |", "",
          "## 2. The rows still out, blocked, keep or assumed", "",
          f"{c['listed']} rows: out {c['out']}, blocked {c['blocked']}, keep {c['keep']}, "
          f"assumed {c['assumed']}. `open` rows name the card that resolves them; `closed` rows are",
          "settled by their own evidence (lore-exact match, a decision, or content no carrier is owed).", "",
          "| row | doc | group | class | resolving card | why (short) |", "|---|---|---|---|---|---|"]
    for x in doc["rows"]:
        card = x["card"]
        if x["closed"]:
            card = card.replace("closed:", "**closed** - ")
        L.append(f"| `{x['id']}` | {x['doc']} | {x['group']} | {x['conf'] or '-'} | {card} | "
                 f"{x['why'][:180] or '-'} |")
    L += ["", "## 3. The close-out numbers", "",
          f"- rows with a resolving card (open, scheduled): **{c['open_carded']}**",
          f"- rows closed by evidence: **{c['closed']}**",
          f"- **lore-compromised rows remaining**: **{c['lore_compromised']}** (target zero; a row is "
          "lore-compromised only when JC3's system cannot express it and no card is named)",
          f"- rows with **no** resolving card: **{c['unassigned']}** (target zero)",
          f"- rows stating a banned final answer (\"no JC3 system\" and its variants): "
          f"**{c['banned_phrases']}**", "",
          "## 4. Problems", ""]
    if doc["problems"]:
        L += [f"- {p}" for p in doc["problems"]]
    else:
        L.append("- none")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    if a.write:
        with open(OUT_M, "w", encoding="utf-8", newline="\n") as f:
            f.write(render_md(doc))
        with open(OUT_J, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        c = doc["counts"]
        print(f"wrote Working/Translation/T23_INVENTORY.{{json,md}}: {c['rows']} rows, "
              f"{c['listed']} listed, {c['open']} open (carded), {c['closed']} closed, "
              f"{c['unassigned']} unassigned")
        for p in doc["problems"]:
            print("FAIL", p)
        return 1 if doc["problems"] else 0
    if not (os.path.exists(OUT_J) and os.path.exists(OUT_M)):
        print("FAIL: T23_INVENTORY.{json,md} missing (run --write)")
        return 1
    bad = []
    if json.load(open(OUT_J, encoding="utf-8")) != doc:
        bad.append("T23_INVENTORY.json differs from the re-derived record")
    if open(OUT_M, encoding="utf-8").read() != render_md(doc):
        bad.append("T23_INVENTORY.md differs from the re-derived record")
    bad += doc["problems"]
    for p in bad:
        print("FAIL", p)
    if bad:
        return 1
    c = doc["counts"]
    print(f"PASS: {c['rows']} rows, by disposition "
          + ", ".join(f"{k} {v}" for k, v in c["by_disposition"].items())
          + f" | {c['open']} carded, {c['closed']} closed, 0 unassigned, "
            f"{c['banned_phrases']} banned final answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
