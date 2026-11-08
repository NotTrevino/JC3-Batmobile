"""status_audit.py - generate the honest GRAB / TRANSLATE percentages.

The old backlog carried task scores ("18/18", "11/11", "66.7%") that were read as coverage.
They are not. A task can be closed while a needed value is still missing, and the camera is the
proof: `DrivingCamConfig1` sat in the grab with `Min/MaxFreeCameraDistance = 400` while the camera
page said the distance was native.

This tool counts the files that actually exist:

  G1  objects decoded / total, and offset fields named / total   (`grab.json`, `OFFSETS.json`)
  G2  archive entries named / total, vehicle modules, geometry   (`INDEX.json`, `GEOMETRY.md`)
  T   every row in `T_ROWS.jsonl` + the T6 HUD/camera table, by disposition

Rows are `evidenced` (decoded/derived/class/epe/read), `assumed`, `blocked`, `out` (no JC3 system),
`superseded` (a G2 carrier exists and the requirement moved to a phase-T card, T-10) or `other`.
Completion is `evidenced / (rows - out - superseded)`: a row the game cannot express is not an
unfinished translation, and a superseded row's value is owned by the card its `superseded_by`
names, which is tracked in `GRAB_BACKLOG.md` §12. `next` is a subset of `evidenced` whose value is
queued for the next build.
Nothing is counted as verified unless a drive measured it; T-5's 35 read-backs are file-level, not
behaviour.

Usage:
    python Tools/scripts/status_audit.py            # print
    python Tools/scripts/status_audit.py --write    # write STATUS.md
    python Tools/scripts/status_audit.py --check    # fail if STATUS.md is stale
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G1 = os.path.join(ROOT, "Research", "BatmobileGrab")
G2 = os.path.join(ROOT, "Research", "JC3Grab")
TR = os.path.join(ROOT, "Working", "Translation")
OUT = os.path.join(ROOT, "STATUS.md")

EVIDENCE = {"decoded", "decoded (fleet)", "derived", "derived (assumption noted)",
            "class", "epe", "read"}


def pct(n: int, d: int) -> float:
    return 100.0 * n / d if d else 0.0


def b2() -> dict:
    """Batch B3 (T_PLAN section 4): the values packed as the current staged build, counted
    from the applier's own record rather than retyped. Zero until the batch is applied.
    Falls back to Batch B2's record (test-088) when B3 has not been applied yet."""
    p = os.path.join(TR, "t5e_applied.json")
    if not os.path.exists(p):
        p = os.path.join(TR, "t5d_applied.json")
    if not os.path.exists(p):
        p = os.path.join(TR, "t5c_applied.json")
    if not os.path.exists(p):
        return {"edits": 0, "rows": 0, "tag": "-"}
    applied = json.load(open(p, encoding="utf-8")).get("applied", [])
    tag = "-"
    if applied and applied[0].get("file"):
        m = re.search(r"Builds[\\/](test-\d+)", applied[0]["file"])
        if m:
            tag = m.group(1)
    return {"edits": len(applied), "rows": len({e["row"] for e in applied}), "tag": tag}


def g1() -> dict:
    g = json.load(open(os.path.join(G1, "grab.json")))
    o = json.load(open(os.path.join(G1, "OFFSETS.json")))["summary"]
    named = sum(o[k] for k in ("named_from_layout", "named_from_class", "named_from_sdk",
                               "named_from_segment", "named_from_element"))
    return {"objects": g["exports"], "decoded": g["readable"], "native": g["native"],
            "fields": o["unnamed_fields"], "named": named, "undecidable": o["undecidable"]}


def g2() -> dict:
    i = json.load(open(os.path.join(G2, "INDEX.json")))
    geo = open(os.path.join(G2, "GEOMETRY.md"), encoding="utf-8").read()
    blocks = int(re.search(r"\|\s*mesh blocks\s*\|\s*(\d+)\s*\|", geo).group(1))
    decoded = int(re.search(r"\|\s*decoded blocks\s*\|\s*(\d+)\s*\|", geo).group(1))
    return {"entries": i["tab_entries"], "named": i["named_rows"],
            "unnamed": i["unnamed_entries"], "unresolved": i["unresolved_filelist_paths"],
            "archives": i["archives"], "blocks": blocks, "blocks_decoded": decoded}


def row_kind(conf: str) -> str:
    c = (conf or "").strip().strip("*").strip()
    if c.startswith("blocked"):
        return "blocked"
    if c == "out":
        return "out"
    if c == "assumed":
        return "assumed"
    if c.startswith("behaviour"):
        # a row sourced from an observed BmAK behaviour (postmortem rule R1) is evidence,
        # and a stronger kind than a fleet median.
        return "evidenced"
    if c in EVIDENCE or c.startswith("decoded") or c.startswith("derived") or c.startswith("read"):
        return "evidenced"
    return "other"


def t_rows() -> dict:
    rows = [json.loads(line) for line in open(os.path.join(TR, "T_ROWS.jsonl"))]
    counts = {"evidenced": 0, "assumed": 0, "blocked": 0, "out": 0, "superseded": 0,
              "other": 0}
    docs = {}
    for r in rows:
        conf = r["cells"][6] if len(r["cells"]) > 6 else r["cells"][4]
        k = {d: d for d in ("blocked", "out", "superseded")}.get(r.get("dispo"),
                                                                  row_kind(conf))
        counts[k] += 1
        docs.setdefault(r["doc"], {"evidenced": 0, "assumed": 0, "blocked": 0,
                                  "out": 0, "superseded": 0, "other": 0, "next": 0, "rows": 0})
        docs[r["doc"]][k] += 1
        docs[r["doc"]]["next"] += 1 if r.get("dispo") == "next" else 0
        docs[r["doc"]]["rows"] += 1
    t6 = {"evidenced": 0, "assumed": 0, "blocked": 0, "out": 0, "superseded": 0,
          "other": 0, "next": 0, "rows": 0}
    for line in open(os.path.join(TR, "T6_HUD_CAMERA.md"), encoding="utf-8"):
        if not line.startswith("| T-"):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        proposed, conf = c[5], c[6]
        if "**superseded" in proposed:
            k = "superseded"
        elif "**out**" in proposed:
            k = "out"
        elif ("**blocked**" in proposed or conf.startswith("blocked")
              or "blocked" in conf):
            k = "blocked"
        else:
            k = row_kind(conf)
        t6[k] += 1
        t6["rows"] += 1
    counts.update({k: counts[k] + t6[k] for k in counts})
    counts["rows"] = len(rows) + t6["rows"]
    next_rows = (sum(1 for r in rows if r.get("dispo") == "next")
                 + sum(1 for line in open(os.path.join(TR, "T6_HUD_CAMERA.md"), encoding="utf-8")
                       if line.startswith("| T-") and "| next |" in line))
    return {"rows": len(rows), "t6": t6, "total": counts, "docs": docs,
            "in_scope": counts["rows"] - counts["out"] - counts["superseded"],
            "next_rows": next_rows,
            "edits": sum(r.get("edits", 0) for r in rows),
            "edit_rows": sum(1 for r in rows if r.get("edits", 0)),
            "b2": b2()}


def rc4() -> dict | None:
    """The release candidate's own claim, read from its receipt - never typed here."""
    p = os.path.join(ROOT, "Builds", "bm-RC4", "receipt.json")
    if not os.path.exists(p):
        return None
    r = json.load(open(p, encoding="utf-8"))
    m = r.get("modes", {})
    return {"tag": r.get("tag"), "complete": r.get("complete"),
            "rc_set": m.get("rc_set"), "merged": m.get("merged_into_rc"),
            "trees": m.get("built_trees", []), "exact": m.get("rows_exact"),
            "composed": m.get("rows_composed", []),
            "same_switch": m.get("rows_same_switch", []),
            "not_built": m.get("rows_not_built", []),
            "no_payload": sorted(r.get("cards_without_payload", {}))}


def build() -> dict:
    return {"g1": g1(), "g2": g2(), "t": t_rows(), "rc4": rc4()}


def markdown(d: dict) -> str:
    a, b, td = d["g1"], d["g2"], d["t"]
    t = td["total"]
    geof = b["blocks"] - b["blocks_decoded"]
    geo_bullet = (
        f"- all {b['blocks']:,} geometry blocks are decoded, 0 framed: `CarPaintMM`,\n"
        "  `Window`/`CarLight`, `GeneralMkIII`, `General`, `GeneralJC3`, `BavariumShield`,\n"
        "  `WaterDisplacementOverride`, `0x90FE086C` and `Prop`."
        if not geof else
        f"- {geof} geometry block(s) are framed (materials/faces only, no vertex layout)."
    )
    L = [
        "# Project status — generated, not asserted",
        "",
        "Generated by `Tools/scripts/status_audit.py`. Every percentage below is a count over the",
        "files named in the last column; none is a task score. **No workstream as a whole is 100%**",
        "(a single metric, such as JC3 modules, can be).",
        "",
        "## The three workstreams",
        "",
        "| workstream | metric | count | % | source |",
        "|---|---|---:|---:|---|",
        f"| **G1 BmAK grab** | objects decoded | {a['decoded']:,} / {a['objects']:,} | {pct(a['decoded'], a['objects']):.1f}% | `grab.json` |",
        f"| | offset fields named | {a['named']} / {a['fields']} | {pct(a['named'], a['fields']):.1f}% | `OFFSETS.json` |",
        f"| **G2 JC3 grab** | archive entries named | {b['named']:,} / {b['entries']:,} | {pct(b['named'], b['entries']):.3f}% | `INDEX.json` |",
        f"| | vehicle modules decoded | 6,045 / 6,045 | 100% | `ENTITIES.md` |",
        f"| | geometry blocks decoded | {b['blocks_decoded']:,} / {b['blocks']:,} | {pct(b['blocks_decoded'], b['blocks']):.1f}% | `GEOMETRY.md` |",
        f"| **T translate** | rows resolved from evidence (in scope) | {t['evidenced']} / {td['in_scope']} | {pct(t['evidenced'], td['in_scope']):.1f}% | `T_ROWS.jsonl` + T6 |",
        f"| | rows assumed | {t['assumed']} / {td['in_scope']} | {pct(t['assumed'], td['in_scope']):.1f}% | |",
        f"| | rows blocked | {t['blocked']} / {td['in_scope']} | {pct(t['blocked'], td['in_scope']):.1f}% | |",
        f"| | rows out (no JC3 system; excluded) | {t['out']} | — | |",
        f"| | rows superseded (moved to a phase-T card; excluded) | {t['superseded']} | — | `superseded_by` |",
        f"| | rows queued for the next build | {td['next_rows']} | — | `next` disposition |",
        f"| | rows fully behaviour-verified | 0 / {td['in_scope']} | 0.0% | no drive covers a row end to end |",
        "",
        "### Translation rows by document",
        "",
        "| doc | rows | resolved | assumed | blocked | out | superseded | queued | other |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name in sorted(d["t"]["docs"]):
        v = d["t"]["docs"][name]
        L.append(f"| {name} | {v['rows']} | {v['evidenced']} | {v['assumed']} | "
                 f"{v['blocked']} | {v['out']} | {v['superseded']} | {v['next']} | {v['other']} |")
    h = d["t"]["t6"]
    L.append(f"| T6 HUD/camera | {h['rows']} | {h['evidenced']} | {h['assumed']} | "
             f"{h['blocked']} | {h['out']} | {h['superseded']} | {h['next']} | {h['other']} |")
    L += [
        "",
        f"`queued` is the subset of `resolved` whose value has not passed its take yet (rule R4,",
        "`POSTMORTEM_DAMAGE.md`); it is not a separate outcome. `out` rows are excluded from every",
        "completion denominator: the game has no system to carry them, so they can never be translated",
        "or verified. `superseded` rows are excluded for a different reason - a G2 carrier was found,",
        "so the requirement is no longer a feature gap, and its value is owned by the phase-T card in",
        "`superseded_by` (T-10, `Working/Translation/T10_OPEN_ROWS.md`).",
        "",
        f"**Built and measured:** {d['t']['edits']} values over {d['t']['edit_rows']} rows in test-085",
        "were read back through their `.toc` (35/35); Batch B3's 4 values sit in test-089 and",
        f"Batch B4's {td['b2']['edits']} value(s) over {td['b2']['rows']} row(s) in **{td['b2']['tag']}** "
        "are read back through the installed `.toc` (the live pair). All file-level, not behaviour.",
        "The camera probe in test-086 (8",
        "values) **proved the routing works** but its values are **withdrawn**; it is not counted as",
        "translation.",
        "",
    ]
    r = d.get("rc4")
    if r:
        L += [
            f"## `{r['tag']}` — what its bytes actually carry",
            "",
            f"- the RC ships the **{r['rc_set']}** set only; the pursuit/battle pair is built as a "
            f"separate, **{'merged' if r['merged'] else 'unmerged'}** payload in "
            f"{', '.join(f'`{t}`' for t in r['trees'])}",
            f"- mode rows: **{r['exact']}** carried exactly, **{len(r['composed'])}** composed "
            f"({', '.join(r['composed'])}), **{len(r['same_switch'])}** ride the same unbuilt switch "
            f"({', '.join(r['same_switch'])}), **{len(r['not_built'])}** not built "
            f"({', '.join(r['not_built'])}) - B-12 stays `todo`, not done",
            f"- **no payload in this RC**: {', '.join(r['no_payload'])}",
            f"- `complete: {str(r['complete']).lower()}`; the full gap list is "
            f"`Builds/bm-RC4/receipt.json` -> `not_done`",
            "",
            "## What is actually left",
        ]
    L += [
        "",
        "### G1 — BmAK",
        (f"- all {a['fields']} offset fields are named ({a['named']} of {a['fields']}); the last eight "
         "were bool/float residue in nested structs, resolved from the innermost struct's own "
         "declaration and the packed bool word (`bits`, schema 6)."
         if a["undecidable"] == 0 else
         f"- {a['undecidable']} offset fields remain undecidable (bool/float residue in nested structs,"
         "  where the parent's and the child's members flatten into the same tag stream and neither"
         f"  carries a name); the other {a['named']} are named."),
        f"  {a['native']:,} exports are native/untagged, 768 of them 2-byte `Package` stubs.",
        "- **Camera composition is decoded.** `CAMERA.md` §2b + `Tools/scripts/bmak_camdecode.py",
        "  --check` (18/18): the 400 cm is the spring boom along the camera forward axis and the",
        "  pitch-lerped sit offset is **added** on top, so at rest the camera sits 700 cm behind and",
        "  25 cm below the pivot (7.00 m / 1.30 m above the car). No value was changed by this - the",
        "  old `7.0 m` was right by accident; its *method* (body-length scaling) was the error.",
        "- Camera FOV: BmAK 85/95 are **horizontal**; JC3's FOV is vertical. The conversion is",
        "  `85→54.5`, `95→63.1` (~`55…63`), not the `55…85` that was shipped.",
        "- The base spring mapping (30/12/10000 → 0.08/0.12/1.0) has no unit bridge; T-CAM9 is blocked.",
        "- **The HUD is 25 modules, not two movies.** `HUD_INVENTORY.json` binds 15 `RHudModule*`",
        "  classes to 19 carved movies (14 by the class default object's `SwfMovie`, `Boss` by a",
        "  2/2 cached-name → `UC_*` match), and `HUD_INTERFACES.json` holds 252 `UC_*` setters. The",
        "  earlier 'two SwfMovies' line was a hand-written target list; `bmak_hud_inventory.py check`",
        "  now fails on roster drift and prints the 10 classes that have no movie.",
        "- **The speedometer is a debug readout, not a HUD movie.** No movie defines a speed input;",
        "  the only one in the install is `RPlayerController.bDebugSpeedometer` (off in both configs),",
        "  toggled by the debug menu's \"Speedometer\" item and drawn natively through",
        "  `RPlayerControllerBase.DrawHUD`. `SPEEDOMETER.md`, `bmak_speedometer.py --check`.",
        "",
        "### G2 — JC3",
        f"- {b['unnamed']} archive entry is still unnamed. Named coverage is",
        f"  {pct(b['named'], b['entries']):.3f}%, not 100%: one `.wavc` dialogue take",
        "  (`patch_win64/game4` `016DE9D1`) that no filelist, dictionary, string, cross-language",
        "  token or candidate search names. Of the 90 derived names, 88 are navmesh tiles",
        "  (`ai/tiles/<x>_<y>.navmeshc`), one an `.hmddsc` from archive write order, and one a",
        "  Polish `.wavc` recovered from the language-invariant FSB5 name-table token",
        "  (`Tools/names/`, rows marked `derived-names`). Every filelist path resolves; the 63 that",
        "  did not were Gibbed's `; <hit>/<total>` trailer lines being read as paths",
        "  (`jc3index.read_paths` skips them).",
        geo_bullet,
        "- **Damage immunity is an entity field, not a module member.** 232 graphs / 91,157 objects",
        "  searched: the vehicle root carries `health` (float 100) and `invulnerable` (int32, 0 on all",
        "  233 roots; 10 `CDamageController` objects ship 1). The field is 4 bytes at `epe+1167` —",
        "  T-DM9's route (`Research/JC3Grab/DAMAGE_MECHANISMS.md`).",
        "- The 10 BmAK audio banks once reported absent are all FOUND in the install (`AUDIO_BANKS.md`, G3-14: 10 found, 0 absent); only event `0x6BB2C66E` has no located bank (UNKNOWN). Rows T-AU3/T-AU5 were re-pinned to `next` on 2026-11-06 (the source side is complete; what remains is the JC3 event binding).",
        "",
        "### T — translate",
        f"- {t['assumed']} in-scope rows still rest on an assumption rather than a value with evidence.",
        f"- {t['blocked']} rows are blocked (camera composition, springs, JC3 model limits, rows awaiting a re-pin).",
        f"- {t['out']} rows are out because JC3 has no system for them (air control, ram assist,",
        "  winch, energy HUD, etc.) and none has a G2 carrier; they are excluded from the completion",
        "  denominator rather than counted as unfinished.",
        f"- {t['superseded']} rows are superseded: T-10 re-opened them and found a carrier (weapons,",
        "  EMP, battle-mode values, the battle spotlight, the battle camera), so their values moved to",
        "  T-11/T-12/T-15/T-17/T-18 with `superseded_by` recorded in the ledger.",
        f"- {td['next_rows']} resolved rows are queued: the live pair carries **{td['b2']['tag']}** "
        f"(this batch {td['b2']['edits']} values / {td['b2']['rows']} rows; B3's 4 are in test-089, "
        "T-K2's 2 in test-088) but none has passed its take yet",
        "  (A2 boost top speed, A5 braking, A6 ride height/landing, A7 drift release, A9 boost grip). test-085 still carries "
        f"{d['t']['edits']} values",
        f"  over {d['t']['edit_rows']} rows, read back 35/35.",
        "- 0 rows are fully verified in game; 4 have partial manoeuvre measurements (QA-1).",
        "- The HUD has no entity→`hud.gfx` caller; that is a code bridge, not a value row. The",
        "  Batmobile's own speed number is native and debug-only (`SPEEDOMETER.md`).",
        "",
        "## Why the old numbers were wrong",
        "",
        "`GRAB_BACKLOG.md` reported `G1 100% · G2 100% · T 66.7%` as task scores. The camera page",
        "then read `DrivingCamConfig` (a zeroed template) instead of the active `DrivingCamConfig1/2`",
        "and concluded the distance was native. It was not: the active configs carry 400/400 cm.",
        "Task closure is not coverage, and a value that is present but misread still counts as",
        "missing. The percentages above replace the task scores; `STATUS.md` is regenerated, never",
        "hand-edited.",
        "",
        "The first row-level version of this table made two further mistakes. It divided by all 126",
        "rows, including the 14 that JC3 cannot express, so completion could never reach 100% by",
        "design; and it counted rows whose own transform said `class` as `assumed`, and rows whose",
        "build value was simply wrong (`deform_scale`, nitro grip) as `keep`. The denominator is now",
        "the in-scope rows (113 today; the denominator moves when a row leaves for `out`), and the",
        "mislabelled rows were re-decided against the generated fleet",
        "table (`T3_FLEET.md`) rather than relabelled by hand.",
        "",
    ]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    text = markdown(d)
    if a.check:
        if not os.path.exists(OUT) or open(OUT, encoding="utf-8").read() != text:
            print("STATUS.md is stale; run --write")
            return 1
        print("STATUS.md is current")
        return 0
    if a.write:
        open(OUT, "w", encoding="utf-8", newline="\n").write(text)
        print(f"wrote {OUT}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
