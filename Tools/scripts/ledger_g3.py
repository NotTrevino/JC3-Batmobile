"""ledger_g3.py - GRB-G3-20: which G3 result supplies, corrects or refutes each ledger row.

Synthesis only: no new decoding, no translation decision. Inputs are read, never written:
  Working/Translation/T_ROWS.jsonl        (198 rows: cells = [id, BmAK source, JC3 target,
                                           transform, now, proposed, confidence, verify])
  Research/BatmobileGrab/*.md, Research/JC3Grab/*.md   (the G3 cards)

Each row is matched against a small evidence table whose values were read in this pass:
  E-MASS   Research/JC3Grab/PHYSICS_ROLES2.md   mass float at hknpShapeMassProperties+0x28
                                                (donor 800/40/5/1, sum 1627.097155 over 56 blocks)
  E-LINK   Research/JC3Grab/PHYSICS_ROLES3.md   polytope+0x20 -> hkRefCountedProperties -> +0x10
                                                -> mass block: 54/54 resolve
  E-INERT  Research/JC3Grab/PHYSICS_ROLES3.md   the 24 bytes at mass+0x10..+0x27 are not floats;
                                                word +0x1C tracks mass (Spearman 0.95), no tensor
  E-CINFO  Research/JC3Grab/PHYSICS_ROLES3.md   24-byte cinfo: one body id + 0x7FFFFFFF, no
                                                second body; type tag +0xC0 = 18/19/12
  E-BODY   Research/JC3Grab/PHYSICS_ROLES3.md   body entry +0x0C = own id (0x7FFFFFFF after 41),
                                                +0x10 = (id<<16)|flag, +0x4C quaternion w
  E-SEL    Research/BatmobileGrab/COLLISION_SELECTOR2.md  mode 0 none / 1 Pursuit / 2 Battle
  E-COLOUR Research/BatmobileGrab/COLOUR_PARAMS.md        body base [0.025787,0.025787,0.03,1]
  E-INPUT  Research/BatmobileGrab/SAMPLER_FIELDS2.md      bVehicleBoostButton +781,
                                                          bBatmobileEjectModifier +786,
                                                          bFiring +2084&2, CoolDown +2092,
                                                          bBoosting +2396&1
  E-PARTS  Research/BatmobileGrab/PARTICLES_FEATURES.md / PHYSICS_ROLES.md  56 mass props,
                                                          42 parts, 11 constraints, 430 objects

Status per row:
  SUPPLIED  - a G3 value answers the row's BmAK source or its JC3 target directly
  CORRECTED - a G3 result changes what the row can claim (e.g. "no mass tag" -> per-shape masses)
  REFUTED   - a G3 result contradicts the row's premise
  OPEN      - no G3 result read in this pass covers it; the card that would is named

    python Tools/scripts/ledger_g3.py --write
    python Tools/scripts/ledger_g3.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3.json")

EVIDENCE = {
    "E-MASS": {"file": "Research/JC3Grab/PHYSICS_ROLES2.md",
               "value": "hknpShapeMassProperties+0x28 = 800.0, 40.0, 5.0, 1.0 (first four of 56); "
                        "sum 1627.097155",
               "label": "decoded"},
    "E-LINK": {"file": "Research/JC3Grab/PHYSICS_ROLES3.md",
               "value": "polytope+0x20 -> hkRefCountedProperties+0x10 -> mass block; 54/54 resolve",
               "label": "decoded"},
    "E-INERT": {"file": "Research/JC3Grab/PHYSICS_ROLES3.md",
                "value": "mass+0x10..+0x27 not IEEE floats; +0x1C rises with mass (Spearman "
                         "0.9517) but word/2^31/mass spread 2.646925 -> tensor UNKNOWN",
                "label": "decoded negative"},
    "E-CINFO": {"file": "Research/JC3Grab/PHYSICS_ROLES3.md",
                "value": "cinfo 24 B = {0, 0, bodyId, 0x7FFFFFFF, 0, 0}; no second body id in "
                         "donor or 41-file fleet; type tag +0xC0 = 18/19, 12 in fleet",
                "label": "decoded"},
    "E-BODY": {"file": "Research/JC3Grab/PHYSICS_ROLES3.md",
               "value": "body entry +0x0C = body id (= index for the 38 part bodies, 0x7FFFFFFF "
                        "for the other 24); +0x10 = (id<<16)|flag (0xFF, 0x01 for bodies 11/15/27); "
                        "+0x3C = 1.0; +0x4C = 0x3F7FFFFF",
               "label": "decoded"},
    "E-SEL": {"file": "Research/BatmobileGrab/COLLISION_SELECTOR2.md",
              "value": "mode 0 = no collision mesh, 1 = BatmanCollisionMeshPursuitMode, "
                       "2 = BatmanCollisionMeshBattleMode (export 10894, 253 B)",
              "label": "decoded"},
    "E-COLOUR": {"file": "Research/BatmobileGrab/COLOUR_PARAMS.md",
                 "value": "body base colour [0.025787, 0.025787, 0.03, 1.0]; 52 MIC overrides, "
                          "69 chain defaults",
                 "label": "decoded"},
    "E-INPUT": {"file": "Research/BatmobileGrab/SAMPLER_FIELDS2.md",
                "value": "bVehicleBoostButton +781, bBatmobileEjectModifier +786, bFiring +2084 "
                         "mask 0x2, CoolDown +2092, bBoosting +2396 mask 0x1",
                "label": "decoded"},
    "E-CENSUS": {"file": "Research/JC3Grab/PHYSICS_ROLES.md",
                 "value": "donor: 430 objects, 42 parts, 56 mass props, 11 constraints, 62 body "
                          "entries, 2 static compounds",
                 "label": "decoded"},
}

# (regex over the row text, evidence, status, why)
RULES = [
    (r"(battle.?mode|pursuit).{0,80}(collision|mesh)|(collision|mesh).{0,80}(battle.?mode|pursuit)",
     "E-SEL", "SUPPLIED",
     "the mode value selects a collision mesh: 0 none / 1 pursuit / 2 battle"),
    (r"albedo|gloss|paint|palette|tint|specular", "E-COLOUR", "SUPPLIED",
     "chain parameters and the authored base colour are decoded"),
]
# Only rows whose own claim the named value answers are listed here; everything
# else is OPEN. Matching on document context alone mislabels FX/light rows that
# merely mention a boost or a battle mode.

# rows whose claim a G3 result directly changes (id -> evidence, status, note)
OVERRIDES = {
    "T-M1": ("E-MASS", "CORRECTED",
             "no absolute mass tag: 56 per-shape blocks at +0x28, total 1627.097155, not a single "
             "rigid-body mass"),
    "T-M2": ("E-INERT", "OPEN",
             "no inertia tensor: mass+0x10..+0x27 not floats; only +0x1C tracks mass"),
    "T-M3": ("E-MASS", "OPEN",
             "no centre-of-mass member: +0x00..+0x0F are zero in every donor block"),
    "T-M4": ("E-MASS", "CORRECTED", "wheel mass is a per-hull block (+0x28), not a chain member"),
    "T-P3": ("E-CENSUS", "SUPPLIED",
             "62 body entries, 42 parts; wheels' world body -1 and raycast ids decoded"),
    "T-CO1": ("E-CENSUS", "SUPPLIED", "donor body/shape census is decoded; shapes are hulls"),
    "T-CO2": ("E-BODY", "SUPPLIED", "body entry words +0x0C/+0x10/+0x3C/+0x4C decoded; "
                        "translation +0x30..+0x3C and quaternion +0x40..+0x4C are G3-10b's"),
    "T-M2": ("E-INERT", "OPEN", "no inertia tensor: mass+0x10..+0x27 are not floats"),
    "T-PA3": ("E-BODY", "SUPPLIED", "world body id = body entry +0x0C; raycast ids are body ids"),
    "T-PA6": ("E-CINFO", "SUPPLIED", "11 constraint records at 24 B, one body id each"),
    "T-MA3": ("E-COLOUR", "SUPPLIED", "authored base [0.025787, 0.025787, 0.03, 1.0]"),
    "T-MA4": ("E-COLOUR", "SUPPLIED", "chain overrides/defines are decoded (52/69)"),
    "T-MA1": ("E-COLOUR", "SUPPLIED", "authored base [0.025787, 0.025787, 0.03, 1.0]"),
    "T-MA2": ("E-COLOUR", "SUPPLIED", "52 MIC overrides / 69 chain defaults decoded"),
    "T-MA5": ("E-COLOUR", "SUPPLIED", "the chain's tint sockets are decoded values, not names"),
    "T-MA7": ("E-COLOUR", "SUPPLIED", "palette entries are decoded floats in COLOUR_PARAMS.json"),
    "T-B3": ("E-INPUT", "SUPPLIED", "boost observable: RBatmobileBooster+2396 mask 0x1"),
    "T-B4": ("E-INPUT", "SUPPLIED", "boost trigger is RPlayerInput+781 (UNKNOWN for the X button)"),
    "T-B2": ("E-INPUT", "SUPPLIED", "boost state bit +2396 mask 0x1 is observable"),
    "T-MD1": ("E-INPUT", "SUPPLIED", "afterburner state is the booster bit; input is +781"),
    "T-WP11": ("E-INPUT", "SUPPLIED", "booster state bit +2396 mask 0x1 decoded"),
}


def rows():
    out = []
    for line in open(ROWS, encoding="utf-8"):
        if line.strip():
            out.append(json.loads(line))
    return out


def classify(row: dict) -> dict:
    text = " ".join(str(c) for c in row["cells"]).lower()
    hit = None
    if row["id"] in OVERRIDES:
        ev, status, why = OVERRIDES[row["id"]]
    else:
        ev = status = why = None
        for pat, e, st, w in RULES:
            m = re.search(pat, text)
            if m:
                ev, status, why, hit = e, st, w, m.group(0)
                break
    if ev is None:
        return {"id": row["id"], "doc": row["doc"], "dispo": row["dispo"], "status": "OPEN",
                "evidence": None, "why": "no G3 result read in this pass covers it",
                "open_with": open_with(row)}
    return {"id": row["id"], "doc": row["doc"], "dispo": row["dispo"], "status": status,
            "evidence": ev, "value": EVIDENCE[ev]["value"], "file": EVIDENCE[ev]["file"],
            "matched": hit, "why": why,
            "open_with": None if status != "OPEN" else open_with(row)}


def open_with(row: dict) -> str:
    doc = row["doc"]
    return {
        "T-1": "G3-01/02/03 cards (collision, controls, physics) or a new decode of the cited member",
        "T-2b": "G3-04..G3-06 (colour, materials, skins) and the .epe/light rig decode",
        "T-3": "G3-10/10b/10c (constraints, mass, body entries) for the physics rows",
        "T-7": "G3-08/G3-09 (weapons, HUD) and the weapon-clone decode",
        "T-13": "G3-07 (effects/sampler) and the .effc carrier decode",
        "T-14": "G3-05/G3-06 (light rig, presets) for the per-light rows",
        "T-15": "G3-01e (mode selector) and a mode-state runtime sampler",
        "T-20": "G3-07 (spawn/drop) and the .ee item decode",
    }.get(doc, "the G3 card for this area (not read in this pass)")


def build() -> dict:
    rs = rows()
    out = [classify(r) for r in rs]
    for o, r in zip(out, rs):
        o["source"] = r["cells"][1]
        o["target"] = r["cells"][2]
    counts = {}
    for o in out:
        counts[o["status"]] = counts.get(o["status"], 0) + 1
    return {"schema": 1, "card": "GRB-G3-20 - ledger rows against the G3 results",
            "ledger": os.path.relpath(ROWS, ROOT).replace("\\", "/"), "rows": out,
            "counts": counts, "evidence": EVIDENCE,
            "note": "statuses are assignment, not judgement: SUPPLIED/CORRECTED/REFUTED name a "
                    "G3 value read in this pass; OPEN names the card that would supply it"}


def render(doc: dict) -> str:
    L = []
    A = L.append
    A("# Ledger rows against the G3 results")
    A("")
    A("GRB-G3-20, synthesis only. Generated by `Tools/scripts/ledger_g3.py --write`; `--check`")
    A("re-derives and compares. Each row of `Working/Translation/T_ROWS.jsonl` is listed once with")
    A("the G3 result that supplies, corrects or refutes it, or with the card that would.")
    A("")
    A("## Status counts")
    A("")
    A("| status | rows |")
    A("|---|---|")
    for k, v in sorted(doc["counts"].items()):
        A("| %s | %d |" % (k, v))
    A("")
    A("## Evidence table (values read in this pass)")
    A("")
    A("| id | file | value | label |")
    A("|---|---|---|---|")
    for k, e in doc["evidence"].items():
        A("| `%s` | `%s` | %s | %s |" % (k, e["file"], e["value"], e["label"]))
    A("")
    A("## Rows")
    A("")
    A("| id | doc | dispo | status | G3 evidence (file: value) | why / what would supply it |")
    A("|---|---|---|---|---|---|")
    for r in doc["rows"]:
        if r["evidence"]:
            ev = "`%s`: %s" % (r["file"], r["value"])
        else:
            ev = "—"
        A("| %s | %s | %s | **%s** | %s | %s |" % (r["id"], r["doc"], r["dispo"], r["status"],
                                                  ev, r["why"] if r["evidence"] else
                                                  r["open_with"]))
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT)))
        print("rows: %d; %s" % (len(doc["rows"]), doc["counts"]))
        return 0
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        fails.append("LEDGER_G3.json is stale")
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("LEDGER_G3.md is stale")
    ids = [r["id"] for r in doc["rows"]]
    if len(ids) != 198:
        fails.append("row count %d != 198" % len(ids))
    if len(set(ids)) != len(ids):
        fails.append("duplicate ids")
    ledger_ids = [r["id"] for r in rows()]
    if ids != ledger_ids:
        fails.append("ids do not match T_ROWS.jsonl")
    for st in {r["status"] for r in doc["rows"]}:
        if st not in {"SUPPLIED", "CORRECTED", "REFUTED", "OPEN"}:
            fails.append("bad status %s" % st)
    for e in doc["evidence"].values():
        if not os.path.exists(os.path.join(ROOT, e["file"])):
            fails.append("missing evidence file %s" % e["file"])
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK 198 rows; %s; every evidence file exists; md+json byte-identical" % doc["counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
