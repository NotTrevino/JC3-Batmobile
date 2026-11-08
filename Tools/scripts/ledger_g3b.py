"""ledger_g3b.py - GRB-G3-20b: value-by-value check of the control, physics and collision ledger rows.

The first pass (`ledger_g3.py`) matched rows to research cards by keyword and never opened the
value. This pass quotes the supplying line, or leaves the row OPEN and names the card that would
supply it. No translation decision is made and no research file is written.

Scope: every row of `Working/Translation/T_ROWS.jsonl` in groups T-1, T-2b and T-13, plus a
verdict on each of the 18 rows the first pass marked SUPPLIED or CORRECTED.

Every entry in `EVIDENCE` is a (file, line, quote) triple. `--check` re-opens the file, reads that
line and fails unless the quote is a substring of it, so a card that changes invalidates the row
instead of silently drifting. Statuses:

  HOLDS       - the quoted line supplies exactly what the row claims
  WRONG_VALUE - the card gives a different value than the row's, or the row's quantity is not in it
  WRONG_CARD  - the card answers a different question than the row asks
  OPEN        - no card read here carries it; `open_with` names the card that would

    python Tools/scripts/ledger_g3b.py --write
    python Tools/scripts/ledger_g3b.py --check
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3B.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3B.json")
GROUPS = ("T-1", "T-2b", "T-13")

CR = "Research/BatmobileGrab/COLOUR_PARAMS.md"
SAMP = "Research/BatmobileGrab/SAMPLER_FIELDS2.md"
CD = "Research/BatmobileGrab/CLASS_DEFAULTS.md"
SEL2 = "Research/BatmobileGrab/COLLISION_SELECTOR2.md"
PR = "Research/JC3Grab/PHYSICS_ROLES.md"
PR2 = "Research/JC3Grab/PHYSICS_ROLES2.md"
PR3 = "Research/JC3Grab/PHYSICS_ROLES3.md"

# row id -> [(file, line, quote)] ; the quote must appear on that line in --check
EVIDENCE = {
    # ---- physics: mass and inertia (T-1) and their first-pass corrections
    "T-M1": [(PR2, 48, "total over all 56 blocks: **1627.097155**"),
             (PR2, 54, "| 0x5970 | 800.0 |")],
    "T-M4": [(PR2, 49, "'25.0': 10")],
    # ---- steering: the one chain value a card in the named list carries
    "T-ST5": [(CD, 317, "`DriftCorrectionSteerSpeed` (RVehicleBatmobileBase) | FloatProperty | 1.0")],
    # ---- boost / input rows whose claim is the sampler observable
    "T-B2": [(SAMP, 93, "`RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1")],
    "T-MD1": [(SAMP, 93, "`RBatmobileBooster.bBoosting` | 2396 (0x95c) | `bit` | 1"),
              (SAMP, 37, "`RPlayerInput.bVehicleBoostButton` | 781 (0x30d)")],
    # ---- parts / constraints (T-2b)
    "T-PA3": [(PR3, 41, "| +0x0C | body id |")],
    "T-PA6": [(PR3, 25, "**Decoded negative:** the record is 24 bytes")],
    # ---- colour rows: the card carries the authored override, not the effective colour
    "T-MA1": [(CR, 69, "`Material0_BaseColour` | vector | [0.025787, 0.025787, 0.03, 1]")],
    "T-MA3": [(CR, 69, "`Material0_BaseColour` | vector | [0.025787, 0.025787, 0.03, 1]")],
    "T-MA4": [(CR, 25, "## 2. Overrides carried by the chain's MICs (52)")],
}

# row id -> (status, note).  A HOLDS entry must have EVIDENCE.
JUDGE = {
    # --- the 18 rows the first pass marked SUPPLIED / CORRECTED: verdict on the first pass
    "T-M1": ("HOLDS", "CORRECTED was right: 56 per-shape blocks, total 1627.097155, so there is no "
                      "single rigid-body mass tag. The 6,000 kg proposal is a class choice, not a "
                      "grab value."),
    "T-M2": ("OPEN", "the row's premise holds - PHYSICS_ROLES3 §3 reports the 24 bytes as not "
                      "floats and only +0x1C tracking mass - but the tensor itself is still UNKNOWN: "
                      "G3-10d (PHYSICS_ROLES4.md) measures the best packed reading at 33 % off the "
                      "AABB box inertia, which is inside the oracle's own error."),
    "T-M4": ("HOLDS", "CORRECTED was right: the donor masses are per-hull (+0x28), and 25.0 appears "
                      "10 times - the wheel value the row quotes as its 'now'."),
    "T-ST5": ("HOLDS", "the BmAK half of the row is exact: DriftCorrectionSteerSpeed = 1.0 at "
                       "CLASS_DEFAULTS.md:317. The JC3 half (2.0/1.5, the identity proposal) is "
                       "donor data and not in these cards."),
    "T-B2": ("HOLDS", "the boost state bit the first pass cited is real and at the stated offset: "
                      "bBoosting @2396 mask 0x1 (SAMPLER_FIELDS2.md:93)."),
    "T-B3": ("WRONG_CARD", "the row asks whether BmAK has any grip/traction member (absence proof) and "
                           "proposes 5.68; the booster *state bit* answers neither. What would answer "
                           "it is the chain absence scan (CHAIN.json / OFFSETS.json)."),
    "T-B4": ("WRONG_CARD", "the row is 'no BmAK source exists for arcade heat-boost / turbo-jump'; the "
                           "sampler offsets do not test that absence."),
    "T-P3": ("WRONG_CARD", "the row is the G2-30 write mapping (11 driveable boxes onto 7 donor hull "
                           "slots); a body/shape *census* does not supply the mapping. "
                           "t16_collision.json / COLLISION_BOXES.md would."),
    "T-MA1": ("WRONG_VALUE", "the card's only body base colour is the MIC override "
                             "[0.025787, 0.025787, 0.03, 1] (COLOUR_PARAMS.md:69). The row's value is "
                             "the *effective* [0.056738, 0.05158, 0.06], and the card says the combine "
                             "rule is UNKNOWN (§5, §6.1) - so it cannot supply that number."),
    "T-MA2": ("WRONG_CARD", "the row counts 28 shipped Batmobile textures; the card counts parameter "
                            "expressions and textures inside the paint package (56 texture parameters), "
                            "not shipped assets."),
    "T-MA3": ("WRONG_VALUE", "same as T-MA1: authored override 0.025787/0.025787/0.03 is not the "
                             "effective 0.056738/0.05158/0.06 the row states."),
    "T-MA4": ("WRONG_VALUE", "the card has no gloss 0.45. It has Material0_Roughness 0.4 (MIC) / 0.25 "
                             "(chain) and Material0_Reflectivity 0.2 / 0.25 - a different quantity and "
                             "different numbers than the row's 'gloss 0.45'."),
    "T-MA5": ("WRONG_CARD", "the row is the `Window` block's tint and opacity; COLOUR_PARAMS covers the "
                            "Mainbody paint chain only, and has no Window block."),
    "T-MA7": ("WRONG_CARD", "the row is the donor's JC3 `Palette.tints[]` (10 tints, specular_gloss "
                            "0.45); the card has no palette at all."),
    "T-PA3": ("HOLDS", "world body id = body entry +0x0C (PHYSICS_ROLES3.md:41); the per-part ids the "
                       "row lists are the parts table in PHYSICS_ROLES.md §2."),
    "T-PA6": ("HOLDS", "11 records of 24 bytes with one body id each (PHYSICS_ROLES3.md:25 and §1). "
                       "G3-10d adds the partner reading: the constant 0 word is body 0 in 494/494 "
                       "records, so 'one body id each' holds but the partner is no longer UNKNOWN."),
    "T-CO1": ("WRONG_CARD", "the row asks for the donor's hull set (SHAPES.md) and whether the write "
                            "side is proven; the cited card only counts objects."),
    "T-CO2": ("WRONG_CARD", "the row is a 3.1615 x 0.6342 x 1.0988 m box fitted against a donor hull; "
                            "the body-entry words cited do not answer it. COLLISION_BOXES.md or "
                            "COLLISION_CONVEX.md would."),
    "T-WP11": ("WRONG_CARD", "the row is JC3's `arcade.nitro_boost` block plus the gadget mesh; the "
                             "sampler gives the boost *observable*, not the arcade values or the mesh."),
    "T-MD1": ("HOLDS", "the row's claim is exactly the card's: afterburner state is the booster bit "
                       "@2396 mask 0x1 and the input byte is RPlayerInput+781."),
}

# rows with verified evidence but no first-pass verdict
JUDGE.update({
    "T-MA5": JUDGE["T-MA5"],
})

# card families for the rows that stay OPEN (named so the next pass knows where to look)
FAMILY = [
    ("T-G", "Working/Translation/stations.json + the §70 mesh measurement (not a G3 card)"),
    ("T-M", "Research/BatmobileGrab/CHAIN.json (mass/inertia members) + Working/Translation/T3_FLEET.md"),
    ("T-S", "Research/BatmobileGrab/CHAIN.json (SVehicleWheel/Suspension archetype) + Working/Translation/T3_FLEET.md"),
    ("T-R", "Research/BatmobileGrab/CHAIN.json (absence scan) + Working/Translation/T3_FLEET.md"),
    ("T-ST", "Research/BatmobileGrab/CHAIN.json / CLASS_DEFAULTS.md + Research/JC3Grab/VOCABULARY.md"),
    ("T-E", "Research/BatmobileGrab/CHAIN.json (torque curve) + Working/Translation/FITS.md"),
    ("T-B", "Research/BatmobileGrab/CHAIN.json (boost members) + Research/JC3Grab/TANKTURN.md"),
    ("T-A", "Research/BatmobileGrab/CHAIN.json (aero members) + Working/Translation/T3_FLEET.md"),
    ("T-K", "Research/BatmobileGrab/CHAIN.json (brake members) + Working/Translation/T3_FLEET.md"),
    ("T-L", "Research/BatmobileGrab/T14_LIGHTS.md + LIGHT_SYSTEM.md"),
    ("T-P", "Research/BatmobileGrab/PARTS_TABLE.jsonl (+ t16_collision.json for T-P3)"),
    ("T-MA", "Research/BatmobileGrab/COLOUR_PARAMS.md (checked) / COLOUR.md / VALUES.json"),
    ("T-PA", "Research/BatmobileGrab/PARTS_TABLE.jsonl + Research/JC3Grab/PHYSICS_ROLES.md §2"),
    ("T-LG", "Research/BatmobileGrab/LIGHT_SYSTEM.md + T14_LIGHTS.md"),
    ("T-AU", "Research/JC3Grab/JC3_AUDIO.md + Research/BatmobileGrab/AUDIO_*.json"),
    ("T-FX", "Research/JC3Grab/FX_TABLE.jsonl + FX.md"),
    ("T-DM", "Research/BatmobileGrab/DAMAGE_MODEL.md + Research/JC3Grab/DAMAGE_MECHANISMS.md"),
    ("T-CO", "Research/BatmobileGrab/COLLISION_BOXES.md / COLLISION_CONVEX.md / SHAPES.md"),
]


def _at(cells, i):
    """Some rows carry fewer than eight cells (a value with a comma split it); never index hard."""
    return cells[i] if len(cells) > i else ""


def open_with(row_id: str) -> str:
    for pref, card in FAMILY:
        if row_id.startswith(pref):
            return card
    return "the G3 card for this area (not read in this pass)"


def rows():
    out = []
    for line in open(ROWS, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            if r["doc"] in GROUPS:
                out.append(r)
    return out


def verify_evidence():
    """Every quote must still be on its line; returns (ok, problems)."""
    problems = []
    cache = {}
    for rid, evs in EVIDENCE.items():
        for path, line_no, quote in evs:
            if path not in cache:
                full = os.path.join(ROOT, path)
                if not os.path.exists(full):
                    problems.append("%s: missing %s" % (rid, path))
                    cache[path] = None
                    continue
                cache[path] = open(full, encoding="utf-8").read().splitlines()
            lines = cache[path]
            if lines is None:
                continue
            if line_no > len(lines):
                problems.append("%s: %s has %d lines, wanted %d" % (rid, path, len(lines), line_no))
                continue
            text = lines[line_no - 1]
            if quote not in text:
                problems.append("%s: %s:%d does not contain %r" % (rid, path, line_no, quote))
    return (not problems), problems


def build():
    rs = rows()
    out = []
    for r in rs:
        rid = r["id"]
        evs = EVIDENCE.get(rid, [])
        status, note = JUDGE.get(rid, ("OPEN", None))
        if status == "HOLDS" and not evs:
            status, note = "OPEN", "no quoted line in this pass"
        if status != "OPEN" and not evs:
            status, note = "OPEN", "no quoted line in this pass"
        out.append({
            "id": rid, "doc": r["doc"], "dispo": r["dispo"],
            "source": _at(r["cells"], 1), "target": _at(r["cells"], 2),
            "now": _at(r["cells"], 4), "proposed": _at(r["cells"], 5),
            "confidence": _at(r["cells"], 6), "verify": _at(r["cells"], 7),
            "status": status,
            "evidence": [{"file": f, "line": n, "quote": q} for f, n, q in evs],
            "note": note if note else ("no card read in this pass carries it" if status == "OPEN"
                                       else ""),
            "open_with": open_with(rid) if status == "OPEN" else None,
        })
    counts = {}
    for o in out:
        counts[o["status"]] = counts.get(o["status"], 0) + 1
    was = first_pass_status()
    inside = {o["id"] for o in out}
    verdicts = {rid: {"was": was[rid], "now": JUDGE[rid][0]}
                for rid in was if rid in JUDGE and rid in inside}
    outside = [{"id": rid, "was": was[rid], "now": JUDGE[rid][0], "note": JUDGE[rid][1],
                "evidence": [{"file": f, "line": n, "quote": q} for f, n, q in EVIDENCE.get(rid, [])]}
               for rid in was if rid not in inside and rid in JUDGE]
    return {
        "schema": 1,
        "card": "GRB-G3-20b - ledger rows checked against the cards, value by value",
        "ledger": os.path.relpath(ROWS, ROOT).replace("\\", "/"),
        "groups": list(GROUPS),
        "rows": out,
        "counts": counts,
        "first_pass": {
            "method": "the first pass (LEDGER_G3.md / .json) matched rows to cards by keyword; these "
                      "are exactly its SUPPLIED/CORRECTED rows, re-checked against a quoted line",
            "source": "Working/Translation/LEDGER_G3.json",
            "rows_checked": len(verdicts) + len(outside),
            "verdicts": verdicts,
            "outside_groups": outside,
            "summary": _summ([v["now"] for v in verdicts.values()] +
                             [o["now"] for o in outside]),
        },
        "method": "each status names the card and line quoted in evidence; OPEN names the card that "
                  "would supply it. No value is filled from general knowledge.",
    }


def first_pass_status():
    """id -> the status the first pass gave it, for its SUPPLIED/CORRECTED rows in our groups."""
    path = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3.json")
    if not os.path.exists(path):
        return {}
    doc = json.load(open(path, encoding="utf-8"))
    out = {}
    for r in doc.get("rows", []):
        if r.get("status") in ("SUPPLIED", "CORRECTED"):
            out[r["id"]] = r["status"]
    return out


def _summ(statuses):
    out = {}
    for s in statuses:
        out[s] = out.get(s, 0) + 1
    return out


def render(doc):
    L = []
    A = L.append
    A("# Ledger rows checked value by value (G3-20b)")
    A("")
    A("Generated by `Tools/scripts/ledger_g3b.py --write` from `%s`; `--check` re-opens every quoted "
      "line. Groups: %s - **%d rows**. Statuses: HOLDS / WRONG_VALUE / WRONG_CARD / OPEN."
      % (doc["ledger"], ", ".join(doc["groups"]), len(doc["rows"])))
    A("")
    A("## 1. Status counts")
    A("")
    A("| status | rows |")
    A("|---|---|")
    for k, v in sorted(doc["counts"].items()):
        A("| %s | %d |" % (k, v))
    A("")
    A("## 2. The 18 rows the first pass marked SUPPLIED or CORRECTED")
    A("")
    A("Verdicts: %s." % ", ".join("%s %d" % (k, v) for k, v in sorted(doc["first_pass"]["summary"].items())))
    A("")
    A("| row | first-pass status | verdict now | why (card and line in the row's evidence) |")
    A("|---|---|---|---|")
    for r in doc["rows"]:
        v = doc["first_pass"]["verdicts"].get(r["id"])
        if v:
            A("| %s | %s | **%s** | %s |" % (r["id"], v["was"], v["now"],
                                             r["note"].replace("|", "\\|")))
    for o in doc["first_pass"]["outside_groups"]:
        A("| %s (group outside T-1/T-2b/T-13) | %s | **%s** | %s |" %
          (o["id"], o["was"], o["now"], o["note"].replace("|", "\\|")))
    A("")
    A("## 3. Every row")
    A("")
    A("| row | group | target | status | card: line - quote |")
    A("|---|---|---|---|---|")
    for r in doc["rows"]:
        if r["evidence"]:
            q = "; ".join("`%s:%d` - %s" % (e["file"].split("/")[-1], e["line"],
                                            e["quote"].replace("|", "\\|")) for e in r["evidence"])
        else:
            q = "—"
        A("| %s | %s | %s | **%s** | %s |" % (r["id"], r["doc"],
                                             r["target"].replace("|", "\\|")[:90], r["status"], q))
    A("")
    A("## 4. What the OPEN rows need")
    A("")
    A("| card | rows |")
    A("|---|---|")
    by = {}
    for r in doc["rows"]:
        if r["status"] == "OPEN":
            by.setdefault(r["open_with"], []).append(r["id"])
    for card, ids in sorted(by.items(), key=lambda kv: -len(kv[1])):
        A("| %s | %d (%s) |" % (card, len(ids), ", ".join(ids[:12]) + (" …" if len(ids) > 12 else "")))
    A("")
    A("## 5. Findings that change the first pass")
    A("")
    A("- The first pass never opened a value: its evidence table quoted card-level summaries (a "
      "census, a mass total, a JSON pointer) and paired them with rows whose claim is a different "
      "quantity. %d of its 18 rows are `WRONG_CARD`: the cited card answers another question."
      % doc["first_pass"]["summary"].get("WRONG_CARD", 0))
    A("- %d rows are `WRONG_VALUE`: the card's number is not the row's number - for colour, the card "
      "carries the *authored override* (0.025787 / 0.025787 / 0.03) while the row states the "
      "*effective* colour (0.056738 / 0.05158 / 0.06), and the card itself says the combine rule is "
      "UNKNOWN." % doc["first_pass"]["summary"].get("WRONG_VALUE", 0))
    A("- %d rows `HOLDS`, each on a line that states the value the row uses." %
      doc["first_pass"]["summary"].get("HOLDS", 0))
    A("- One card in the named list does carry a physics value the ledger never used: "
      "`CLASS_DEFAULTS.md:317` decodes `DriftCorrectionSteerSpeed` = 1.0, which is exactly T-ST5's "
      "BmAK side. `CLASS_DEFAULTS.md:158` also decodes `ChassisMass` (SVehicle) = 210.0 - relevant "
      "to T-M1, which currently rests on a fleet class choice (6,000 kg) rather than on this number.")
    A("")
    A("## 6. Method and limits")
    A("")
    A("- Each status names one card and one line. `--check` re-reads that line and requires the quote "
      "to be a substring of it, so a rewritten card fails the row rather than silently passing.")
    A("- A row is `OPEN` when none of the cards read here carries it, even when the row itself cites a "
      "card: the cited file (`CHAIN.json`, `T3_FLEET.md`, `VALUES.json`, `PARTS_TABLE.jsonl`, "
      "`FX_TABLE.jsonl`) is named in §4 instead of being quoted from memory.")
    A("- No value here is a translation decision; the rows keep their own proposals.")
    A("")
    return "\n".join(L) + "\n"


def write():
    doc = build()
    md = render(doc)
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
    open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT).replace("\\", "/"),
                               os.path.relpath(OUT_JSON, ROOT).replace("\\", "/")))
    print("rows: %d; %s" % (len(doc["rows"]), doc["counts"]))
    print("first pass: %s" % doc["first_pass"]["summary"])
    ok, problems = verify_evidence()
    if not ok:
        print("EVIDENCE FAIL")
        for p in problems:
            print("  -", p)
        return 1
    print("evidence lines: %d quoted, all present" % sum(len(v) for v in EVIDENCE.values()))
    return 0


def check():
    doc = build()
    md = render(doc)
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("LEDGER_G3B.md is stale")
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(
            json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"):
        fails.append("LEDGER_G3B.json is stale")
    ok, problems = verify_evidence()
    fails.extend(problems)
    src = rows()
    ids = [r["id"] for r in doc["rows"]]
    if ids != [r["id"] for r in src]:
        fails.append("row ids do not match T_ROWS.jsonl for the three groups")
    if len(set(ids)) != len(ids):
        fails.append("duplicate row ids")
    for r in doc["rows"]:
        if r["status"] not in {"HOLDS", "WRONG_VALUE", "WRONG_CARD", "OPEN"}:
            fails.append("%s: bad status %s" % (r["id"], r["status"]))
        if r["status"] != "OPEN" and not r["evidence"]:
            fails.append("%s: %s without a quoted line" % (r["id"], r["status"]))
        if r["status"] == "OPEN" and not r["open_with"]:
            fails.append("%s: OPEN without a named card" % r["id"])
    if doc["first_pass"]["rows_checked"] != len(doc["first_pass"]["verdicts"]) + len(
            doc["first_pass"]["outside_groups"]):
        fails.append("first-pass verdict count mismatch")
    if doc["first_pass"]["rows_checked"] != 18:
        fails.append("first pass had %d SUPPLIED/CORRECTED rows, expected 18"
                     % doc["first_pass"]["rows_checked"])
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d rows (%s); 18 first-pass rows re-checked %s; evidence quotes all present"
          % (len(doc["rows"]), doc["counts"], doc["first_pass"]["summary"]))
    return 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("--write", "--check"):
        print("usage: ledger_g3b.py --write | --check")
        return 2
    return write() if sys.argv[1] == "--write" else check()


if __name__ == "__main__":
    raise SystemExit(main())
