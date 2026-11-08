#!/usr/bin/env python3
"""audit_g301b.py - audit COLLISION_GEOM.md (G3-01b) against the later collision cards.

Read-only on every input.  Writes exactly one file:
    Research/BatmobileGrab/AUDIT_G301B.md

    --write   regenerate that file
    --check   re-derive it and compare byte for byte (exit 1 on drift, 2 on a failed check)

What it does
------------
1. Parses the three box rows of COLLISION_GEOM.md and the same three rows of
   COLLISION_BOXES.md, then recomputes the agreement (extents, centres).
2. Reads the later cards (CONVEX, SHAPES, BOXES, BOX_FLAGS, MATRIX_ORDER,
   CYLINDERS, MODES, SELECTOR_POLARITY) for the facts that settle or leave open
   each G3-01b statement, and records the byte offsets/counts they state.
3. Scores every statement of COLLISION_GEOM.md and every point of the four
   review-G3-01b*.md files as  still holds / superseded / wrong / open, with the
   evidence substring that supports the score.  Every cited substring is checked
   against the file it names, so a citation that is not in the source fails --check.

Labels follow the project convention: decoded = read from bytes at a stated
offset; derived = a stated rule applied to decoded values; UNKNOWN = not decoded.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RG = "Research/BatmobileGrab"
RP = "tmp/freebuff/reports"

PATH = {
    "GEOM": f"{RG}/COLLISION_GEOM.md",
    "BOXES": f"{RG}/COLLISION_BOXES.md",
    "CONVEX": f"{RG}/COLLISION_CONVEX.md",
    "CYL": f"{RG}/COLLISION_CYLINDERS.md",
    "MODES": f"{RG}/COLLISION_MODES.md",
    "SHAPES": f"{RG}/COLLISION_SHAPES.md",
    "FLAGS": f"{RG}/BOX_FLAGS.md",
    "MATRIX": f"{RG}/MATRIX_ORDER.md",
    "POLARITY": f"{RG}/SELECTOR_POLARITY.md",
    "R_MAIN": f"{RP}/review-G3-01b.md",
    "R_BOXES": f"{RP}/review-G3-01b-boxes.md",
    "R_CYL": f"{RP}/review-G3-01b-cyl.md",
    "R_MODE": f"{RP}/review-G3-01b-mode.md",
}
OUT = ROOT / RG / "AUDIT_G301B.md"

STATUS_ORDER = ["still holds", "superseded", "wrong", "open"]


class AuditError(RuntimeError):
    pass


def read(key: str) -> str:
    p = ROOT / PATH[key]
    if not p.is_file():
        raise AuditError(f"missing input {PATH[key]}")
    return p.read_text(encoding="utf-8")


def need(rx: str, text: str, what: str, flags: int = 0) -> re.Match:
    m = re.search(rx, text, flags)
    if not m:
        raise AuditError(f"could not find {what}")
    return m


# ---------------------------------------------------------------- parsers

def geom_boxes(t: str) -> list[dict]:
    """The three `- box N: extents [...] cm, centre [...] cm` rows."""
    out: list[dict] = []
    export = None
    for line in t.splitlines():
        m = re.match(r"^- body export (\d+) bone `([^`]+)`", line)
        if m:
            export = int(m.group(1))
            continue
        m = re.match(
            r"^\s+- box (\d+): extents \[([^\]]+)\] cm, centre \[([^\]]+)\] cm", line
        )
        if m:
            out.append(
                {
                    "export": export,
                    "box": int(m.group(1)),
                    "ext": [float(x) for x in m.group(2).split(",")],
                    "centre": [float(x) for x in m.group(3).split(",")],
                }
            )
    return out


def boxes_extents(t: str) -> dict[tuple[int, int], list[float]]:
    """`| 0 | 8..125 (118 B) | ... | 690.305 / 374.536 / 207.500 | ...` rows."""
    out: dict[tuple[int, int], list[float]] = {}
    export = None
    for line in t.splitlines():
        m = re.match(r"^## Export (\d+) - ", line)
        if m:
            export = int(m.group(1))
            continue
        if export is None or not line.startswith("| "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not re.fullmatch(r"\d+", cells[0]):
            continue
        m = re.fullmatch(r"([\d.]+) / ([\d.]+) / ([\d.]+)", cells[3])
        if not m:
            continue
        out[(export, int(cells[0]))] = [float(g) for g in m.groups()]
    return out


def boxes_translations(t: str) -> dict[tuple[int, int], list[float]]:
    """`| 169750 | bone | 0 | rows | (9.000, 0.000, 106.750) | identity |` rows."""
    out: dict[tuple[int, int], list[float]] = {}
    for line in t.splitlines():
        if not line.startswith("| 1697"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not re.fullmatch(r"\d{5,6}", cells[0]):
            continue
        if not re.fullmatch(r"\d+", cells[2]):
            continue
        m = re.fullmatch(r"\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)", cells[4])
        if not m:
            continue
        out[(int(cells[0]), int(cells[2]))] = [float(g) for g in m.groups()]
    return out


def convex_cross(t: str) -> dict[int, dict]:
    """The `Cross-check against G3-01b` rows."""
    out = {}
    pat = re.compile(
        r"^\| (169748|169749) \| \{'nV': (\d+), 'triangles': (\d+), 'planes': (\d+)\} "
        r"\| \{'nV': (\d+), 'triangles': (\d+), 'planes': (\d+)\} \| yes \|"
    )
    for line in t.splitlines():
        m = pat.match(line)
        if m:
            g = [int(x) for x in m.groups()[1:]]
            out[int(m.group(1))] = {
                "a": {"nV": g[0], "tris": g[1], "planes": g[2]},
                "b": {"nV": g[3], "tris": g[4], "planes": g[5]},
            }
    return out


def shapes_counts(t: str) -> dict[int, dict]:
    """`| 169750 | bone | 1759 B | [0, 2, 0, 1] | 244 | 244 |` rows."""
    out = {}
    for line in t.splitlines():
        if not line.startswith("| 1697"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or not re.fullmatch(r"\d{5,6}", cells[0]):
            continue
        m = re.fullmatch(r"\[(\d+), (\d+), (\d+), (\d+)\]", cells[3])
        if not m:
            continue
        out[int(cells[0])] = {
            "counts": [int(g) for g in m.groups()],
            "sphyl_at": int(cells[4]),
        }
    return out


# ---------------------------------------------------------------- statements

def statement_rows(cmp_ok: bool, de: float, dt: float) -> list[dict]:
    """Every audited statement: id, text, status, what the later evidence says, citations."""
    numeric = "still holds" if cmp_ok else "wrong"
    numeric_txt = f"values agree (max abs diff {de:.4f} cm extents, {dt:.4f} cm centre)"
    return [
        # --- COLLISION_GEOM statements
        dict(id="G01", claim="169748 AggGeom 25907 B; u32 words +0..+12 = [0,0,0,43]",
             status="still holds",
             later="CONVEX decodes 43 elements and closes 25898+9 = 25907 B",
             ev=[("GEOM", "AggGeom 25907 bytes"), ("CONVEX", "convex elements **43** (43)")]),
        dict(id="G02", claim="the four words are a 16-byte header; word 3 = convex count",
             status="wrong",
             later="SHAPES: the counts are interleaved with their arrays, not a header; for a body with boxes, +12 is the box TM's first float (convex count at 248 / 130)",
             ev=[("SHAPES", "not four words of header"),
                 ("BOXES", "| 248 | 4 | convex_count |")]),
        dict(id="G03", claim="169748 element 0 = 10 verts / 16 tris / 7 planes, all on plane",
             status="still holds",
             later="CONVEX cross-check reproduces 10/16/7 for element 0",
             ev=[("GEOM", "10 vertices"), ("CONVEX", "| 169748 | {'nV': 10, 'triangles': 16, 'planes': 7}")]),
        dict(id="G04", claim="169749 AggGeom 8275 B; words [0,0,0,13]",
             status="still holds",
             later="CONVEX decodes 13 elements and closes 8266+9 = 8275 B",
             ev=[("GEOM", "AggGeom 8275 bytes"), ("CONVEX", "**8266** of 8275")]),
        dict(id="G05", claim="169749 element 0 = 8 verts / 12 tris / 6 planes, all on plane",
             status="still holds",
             later="CONVEX cross-check reproduces 8/12/6 for element 0",
             ev=[("GEOM", "8 vertices"), ("CONVEX", "| 169749 | {'nV': 8, 'triangles': 12, 'planes': 6}")]),
        dict(id="G06", claim="'UNKNOWN beyond element 0: the element chain does not close'",
             status="superseded",
             later="CONVEX decodes 56 elements (43+13) with byte accounting; the chain had read the ElemBox as a seventh array",
             ev=[("CONVEX", "decodes **56 elements**"),
                 ("CONVEX", "G3-01b's chain stopped because it read a seventh array")]),
        dict(id="G07", claim="block A (9 / 6 records): vertex components, semantic UNKNOWN",
             status="open",
             later="CONVEX calls it permuted 16-B data with semantics UNKNOWN; review tested and rejected the plane reading (0/16, 0/12)",
             ev=[("CONVEX", "(permuted data)")]),
        dict(id="G08", claim="169750 box 0 extents 690.305 / 374.536 / 207.5 cm",
             status=numeric, later=numeric_txt,
             ev=[("BOXES", "690.305 / 374.536 / 207.500")]),
        dict(id="G09", claim="169750 box 1 extents 679.585 / 345.688 / 103.5 cm",
             status=numeric, later=numeric_txt,
             ev=[("BOXES", "679.585 / 345.688 / 103.500")]),
        dict(id="G10", claim="169751 box 0 extents 166.177 / 189.365 / 39.8 cm",
             status=numeric, later=numeric_txt,
             ev=[("BOXES", "166.177 / 189.365 / 39.800")]),
        dict(id="G11", claim="centres (9, 0, 106.75), (0, 0, 79), (-30.5, 0, 93.25) cm",
             status=numeric, later=numeric_txt,
             ev=[("BOXES", "(9.000, 0.000, 106.750)"), ("BOXES", "(-30.500, 0.000, 93.250)")]),
        dict(id="G12", claim="centre read by the inherited '12 bytes before the tags' rule, labelled decoded",
             status="superseded",
             later="BOXES decodes the TM (16 floats, translation = floats 13..15); the old rule agrees on all 3 boxes",
             ev=[("BOXES", "The translation is byte-identical")]),
        dict(id="G13", claim="'rotation not decoded'",
             status="superseded",
             later="BOXES reading A: 3x3 orthonormal with det +1 on 131/131 boxes (reading B 0/131)",
             ev=[("BOXES", "131 / 131")]),
        dict(id="G14", claim="extents convention (full vs half lengths) undecided",
             status="superseded",
             later="BOXES verdict FULL lengths: worst deviation 0.150 full vs 0.575 half; containment 28.1 cm vs 359.7 cm",
             ev=[("BOXES", "**verdict: FULL lengths.**")]),
        dict(id="G15", claim="oracle: sorted spans of the chassis box vs the body box, 0.25 m window",
             status="superseded",
             later="BOXES uses its own containment oracle; the boxes review shows a stronger same-bone oracle (convex span 690.0/345.0/187.25 vs box 690.305/374.536/207.5)",
             ev=[("BOXES", "Oracle: are the extents full or half lengths?"),
                 ("R_BOXES", "690.0 / 345.0 / 187.25")]),
        dict(id="G16", claim="'extents: tagged floats 0x40/0x44/0x48 at byte 92'",
             status="still holds",
             later="BOXES confirms the three FloatProperty tags at logical 0x40/0x44/0x48 inside an 0x50-byte element",
             ev=[("BOXES", "0x40/0x44/0x48")]),
        dict(id="G17", claim="cylinder floats 78.0 / 175.0: radius vs height UNKNOWN",
             status="superseded",
             later="CYLINDERS: 540 = CollisionHeight, 544 = CollisionRadius (78.0 / 175.0 cm on both cylinders)",
             ev=[("CYL", "| 540 (0x21C) | `CollisionHeight` |"),
                 ("CYL", "| 544 (0x220) | `CollisionRadius` |")]),
        dict(id="G18", claim="active collision mesh per mode UNKNOWN",
             status="open",
             later="MODES still returns 3 UNKNOWN; SELECTOR_POLARITY decodes the setter's branch (body on true, 4/4) but no card decodes which component is attached at runtime",
             ev=[("MODES", "### BatmanVsBatmobileCollisionMode (layout 5895) picks the component"),
                 ("POLARITY", "body runs when the comparison is TRUE")]),
        dict(id="G19", claim="V3 PhysicsAsset: bodies [169750, 169751], constraint [171462], BoundsBodies [0, 1]",
             status="still holds",
             later="BOXES decodes both bodies byte for byte; no later card contradicts the ref arrays",
             ev=[("BOXES", "Export 169750 - `Batmobile_V3_Physics.RB_BodySetup`")]),
        dict(id="G20", claim="constraint 171462 offset names UNKNOWN",
             status="open",
             later="no later card re-decodes 171462; its offsets 84/92/100/144/156/168 stay unnamed",
             ev=[("GEOM", "constraint export 171462")]),
        dict(id="G21", claim="Bounds array (72 B) not decoded",
             status="open",
             later="BOXES U-4 and CONVEX U-4 keep the StaticMesh/Bounds route open; no layout found",
             ev=[("BOXES", "| U-4 | the StaticMesh Bounds as a second extents oracle")]),
        dict(id="G22", claim="actor frame -> PSK frame link UNKNOWN",
             status="open",
             later="not addressed by any later collision card",
             ev=[("GEOM", "Actor frame to PSK frame link")]),

        # --- review-G3-01b.md (the card's own review)
        dict(id="M1", claim="review: header-word meanings printed as decoded (sphere/convex counts)",
             status="superseded",
             later="SHAPES settles the layout (interleaved counts) and refutes the header model; the count named 'convex' is right only because the first three counts are 0",
             ev=[("R_MAIN", "header-word meanings"),
                 ("SHAPES", "the four counts are **interleaved**")]),
        dict(id="M2", claim="review: box centres labelled decoded though inherited by a rule",
             status="superseded",
             later="BOXES decodes the TM translation, so the label is now earned",
             ev=[("R_MAIN", "box centres labelled decoded"), ("BOXES", "translation (cm)")]),
        dict(id="M3", claim="review: section headings assert the mode attribution unlabelled",
             status="open",
             later="later cards still name the meshes from G3-01c's export names; no card decodes the component -> StaticMesh -> BodySetup link",
             ev=[("R_MAIN", "Headings assert the mode attribution")]),
        dict(id="M4", claim="review: 'RB_BodySetup 169748 (Batmobile_V2)' reads like a decoded object name",
             status="open",
             later="CONVEX/BOXES still print a label next to the export; the export's own name is RB_BodySetup",
             ev=[("R_MAIN", "reads like an object name")]),
        dict(id="M5", claim="review: the chassis/body oracle is weaker than the wording suggests",
             status="superseded",
             later="BOXES replaces it with a containment oracle and the boxes review adds a same-bone oracle; the claim no longer rests on the 0.25 m sorted-span test",
             ev=[("R_MAIN", "oracle is weaker than the wording suggests")]),
        dict(id="M6", claim="review: elements 1..N look resolvable by the script's own oracle",
             status="superseded",
             later="CONVEX resolved them: 56 elements, every payload closes to the 9-byte footer",
             ev=[("R_MAIN", "AggGeom elements 1..N"), ("CONVEX", "**56 of 56**")]),
        dict(id="M7", claim="review: block A is not a plane table, so its UNKNOWN is corroborated",
             status="open",
             later="CONVEX keeps the same UNKNOWN; nothing names the 16-B records",
             ev=[("R_MAIN", "corroborated"), ("CONVEX", "## UNKNOWN")]),
        dict(id="M8", claim="review: the Bounds array is not resolvable from these bytes",
             status="open",
             later="BOXES U-4: even the SDK tree ships no StaticMesh layout",
             ev=[("R_MAIN", "`Bounds` array (72 B, count 2)")]),

        # --- review-G3-01b-boxes.md
        dict(id="B1", claim="boxes review I-1: the 0x4C bool has a name (FKBoxElem, mask 64)",
             status="superseded",
             later="BOX_FLAGS census of 4648 boxes: bit 6 = bInterVehicleCollision on 5 boxes / 4 bodies; the card's U-1 name is closed",
             ev=[("R_BOXES", "U-1 is a scope gap"),
                 ("FLAGS", "| 6 | `0x40` | `bInterVehicleCollision` |")]),
        dict(id="B2", claim="boxes review I-2: the zero count before convex is the sphyl count",
             status="superseded",
             later="SHAPES proves it from bytes (25 sphere bodies, 271 capsule bodies, 3276 bodies close); the same two offsets 244/126",
             ev=[("R_BOXES", "U-2 is resolvable"), ("SHAPES", "271 bodies carry capsules")]),
        dict(id="B3", claim="boxes review I-3: the planes are rows, so the 4 deg sign is fixed",
             status="open",
             later="MATRIX_ORDER leaves row/column UNSETTLED (no known row/column case in the build), so BOXES' conditional sign stands and the review's fix is not adopted",
             ev=[("R_BOXES", "U-3 is resolvable"), ("MATRIX", "row/column order: **UNSETTLED**")]),
        dict(id="B4", claim="boxes review I-4: the decisive oracle (169750's own convex element) was unused",
             status="open",
             later="BOXES.md still bases its verdict on the cross-body hull; the same-bone numbers appear only in the review",
             ev=[("R_BOXES", "The decisive oracle was in the same export")]),
        dict(id="B5", claim="boxes review I-5: 'two independent tests' is one comparison measured twice",
             status="open",
             later="BOXES.md's four conditions are still the two statistics of one hull comparison",
             ev=[("R_BOXES", "one comparison measured twice")]),
        dict(id="B6", claim="boxes review I-6: containment ignores the rotation the card decoded",
             status="open",
             later="BOXES.md still computes t +/- e/2 axis-aligned and calls it box containment",
             ev=[("R_BOXES", "Containment ignores the rotation")]),
        dict(id="B7", claim="boxes review I-7: '12 bytes before the tag stream' points at the wrong offset",
             status="open",
             later="the sentence is still in COLLISION_BOXES.md",
             ev=[("R_BOXES", "Wording that points at the wrong offset"),
                 ("BOXES", "12 bytes before the tag stream")]),
        dict(id="B8", claim="boxes review I-8: provenance of the two hulls is unlabelled",
             status="superseded",
             later="BOXES cites COLLISION_CONVEX.json as the hull source; the mode names still originate in G3-01c",
             ev=[("R_BOXES", "Unlabelled provenance for the two hulls"),
                 ("BOXES", "hull source: `COLLISION_CONVEX.json`")]),
        dict(id="B9", claim="boxes review I-9: the report overstates the extents convention's status",
             status="superseded", moot=True,
             later="moot in the artifact: COLLISION_BOXES.md already labels the rule 'derived:' as the review asks",
             ev=[("R_BOXES", "overstates the convention's status"),
                 ("BOXES", "- rule: derived: compare sorted spans")]),
        dict(id="B10", claim="boxes review I-10: cosmetic (rotations token, field names, strides)",
             status="open",
             later="COLLISION_BOXES.md is unchanged; 'rotations 3/131' and the Extent X/Y/Z names remain",
             ev=[("R_BOXES", "Cosmetic")]),

        # --- review-G3-01b-cyl.md
        dict(id="C1", claim="cyl review I1: 'the only reading the types allow' overstates the argument",
             status="open",
             later="COLLISION_CYLINDERS.md still carries the sentence; the chain=declaration premise is not added",
             ev=[("R_CYL", "Ascending is the only reading the types allow"),
                 ("CYL", "Ascending is the only")]),
        dict(id="C2", claim="cyl review I2: the bool bits and CylinderColor type are resolvable",
             status="open",
             later="the card still lists both as UNKNOWN",
             ev=[("R_CYL", "two UNKNOWNs are resolvable"), ("CYL", "**Which bit of the bool word at 556")]),
        dict(id="C3", claim="cyl review I3: BmSDK was not used as the independent check",
             status="open",
             later="no later collision card adds the BmSDK cross-check to CYLINDERS.md",
             ev=[("R_CYL", "BmSDK was not used as the independent check")]),
        dict(id="C4", claim="cyl review I4: check 2 is a drift guard, not an oracle",
             status="open",
             later="the check list is unchanged",
             ev=[("R_CYL", "check 2 is a drift guard")]),
        dict(id="C5", claim="cyl review I5: report splits decoded from derived poorly",
             status="open",
             later="report-only; the card's own table header is already correct",
             ev=[("R_CYL", "minor labelling")]),

        # --- review-G3-01b-mode.md
        dict(id="D1", claim="mode review I1 (blocking): the selector IS referenced by UnrealScript (10894)",
             status="superseded",
             later="COLLISION_SELECTOR/2 + SELECTOR_POLARITY decode 10894: 6 guards, value->mesh table, body runs when the comparison is true (4/4 decisive)",
             ev=[("R_MODE", "the selector *is* referenced by UnrealScript"),
                 ("POLARITY", "4 of 4")]),
        dict(id="D2", claim="mode review I2: 178 State-owned vehicle functions and the mode switch are outside the corpus",
             status="open",
             later="MODES.md's corpus filter is unchanged; 105028 / 10552 / 10701 / 10895 are still not searched by that card",
             ev=[("R_MODE", "the corpus is not \"every vehicle function\"")]),
        dict(id="D3", claim="mode review I3: the 22/16-byte slice exclusion is unstated",
             status="open",
             later="MODES.md still presents script bytes as the whole body",
             ev=[("R_MODE", "38-byte head/tail exclusion")]),
        dict(id="D4", claim="mode review I4: Playable_Batmobile_SF is claimed as input but never opened",
             status="open",
             later="MODES.md's tables are BmGame/Startup only; the claim lives in the G3-01b-mode report and was not corrected there",
             ev=[("R_MODE", "is claimed as an input but the script never opens it")]),
        dict(id="D5", claim="mode review I5: the four counts are wrong",
             status="open",
             later="MODES.md still says 'Problems - none' and keeps the six-function table",
             ev=[("R_MODE", "counts that do not match"), ("MODES", "## Problems")]),
        dict(id="D6", claim="mode review I6: parts of --check are vacuous",
             status="open",
             later="the check list is unchanged",
             ev=[("R_MODE", "parts of `--check` are vacuous")]),
        dict(id="D7", claim="mode review I7: absence treated as a finding",
             status="open",
             later="MODES.md still asserts the selector 'appears in no state or Batmobile/vehicle function body'; the question is now answered elsewhere, so the assertion is moot but still printed",
             ev=[("R_MODE", "absence treated as a finding")]),
        dict(id="D8", claim="mode review I8: three class-default chains treated as one",
             status="open",
             later="MODES.md still calls all of them base templates; ownership still not separated",
             ev=[("R_MODE", "three different class-default chains")]),
    ]


# ---------------------------------------------------------------- build

def build() -> str:
    src = {k: read(k) for k in PATH}
    checks: list[tuple[str, bool, str]] = []

    # ---- Q1: the three boxes, re-read from both cards
    geom = geom_boxes(src["GEOM"])
    ext = boxes_extents(src["BOXES"])
    tr = boxes_translations(src["BOXES"])
    if len(geom) != 3:
        raise AuditError(f"expected 3 boxes in COLLISION_GEOM.md, parsed {len(geom)}")
    if len(ext) != 3 or len(tr) != 3:
        raise AuditError(f"expected 3 boxes in COLLISION_BOXES.md, parsed {len(ext)} extents / {len(tr)} translations")

    cmp_rows = []
    for g in geom:
        key = (g["export"], g["box"])
        be, bt = ext.get(key), tr.get(key)
        de = max(abs(a - b) for a, b in zip(g["ext"], be)) if be else float("inf")
        dt = max(abs(a - b) for a, b in zip(g["centre"], bt)) if bt else float("inf")
        cmp_rows.append({"key": key, "g": g, "ext": be, "tr": bt, "de": de, "dt": dt,
                         "ok": de <= 0.001 and dt <= 0.001})
    cmp_ok = all(r["ok"] for r in cmp_rows)
    de_max = max(r["de"] for r in cmp_rows)
    dt_max = max(r["dt"] for r in cmp_rows)
    checks.append(("the 3 GEOM boxes are all present in COLLISION_BOXES.md",
                   len(cmp_rows) == 3 and all(r["ext"] and r["tr"] for r in cmp_rows),
                   ", ".join(f"{r['key'][0]}/{r['key'][1]}" for r in cmp_rows)))
    checks.append(("extents and centres agree for the same 3 boxes", cmp_ok,
                   f"max abs diff {de_max:.4f} cm extents, {dt_max:.4f} cm centre"))

    # ---- Q1: what BOXES settles
    m = need(r"size` is exactly the 64 bytes", src["BOXES"], "TM size sentence")
    checks.append(("BOXES fixes the element stride at 0x50 (TM 0x00-0x3F)", bool(m), "TM 64 B + floats + bool + end"))
    m2 = need(r"0x40/0x44/0x48/0x4C", src["BOXES"], "extent tag offsets")
    checks.append(("BOXES places the extents at 0x40/0x44/0x48", bool(m2), "FloatProperty tags"))
    m3 = need(r"\*\*verdict: FULL lengths\.\*\*", src["BOXES"], "extents verdict")
    checks.append(("BOXES decides full vs half lengths", bool(m3), "FULL lengths"))
    m4 = need(r"1759 of 1759 bytes mapped, exact = True", src["BOXES"], "169750 byte map")
    m5 = need(r"143 of 143 bytes mapped, exact = True", src["BOXES"], "169751 byte map")
    checks.append(("both V3 bodies are byte-mapped exactly", bool(m4 and m5), "1759/1759 and 143/143"))
    m6 = need(r"131 / 131", src["BOXES"], "orthonormality count")
    checks.append(("the rotation reading is orthonormal on 131/131 boxes", bool(m6), "reading A"))

    # ---- Q1/Q3: the header model
    m = need(r"not four words of header", src["SHAPES"], "interleaved-count statement")
    checks.append(("SHAPES refutes the four-word header model", bool(m), "counts are interleaved with their arrays"))
    hdr = re.search(r"header words \[([0-9, ]+)\]", src["GEOM"])
    if not hdr:
        raise AuditError("no 'header words [...]' in COLLISION_GEOM.md")
    words = [int(x) for x in hdr.group(1).split(",")]

    # ---- Q2: the V3 bodies elsewhere
    sh = shapes_counts(src["SHAPES"])
    if sorted(sh) != [169750, 169751]:
        raise AuditError(f"expected SHAPES rows for 169750/169751, got {sorted(sh)}")
    checks.append(("SHAPES re-decodes both V3 bodies with all four counts",
                   sh[169750]["counts"] == [0, 2, 0, 1] and sh[169751]["counts"] == [0, 1, 0, 0],
                   f"169750 {sh[169750]['counts']}, 169751 {sh[169751]['counts']}"))
    checks.append(("SHAPES puts the sphyl count at the byte GEOM called a header word",
                   sh[169750]["sphyl_at"] == 244 and sh[169751]["sphyl_at"] == 126,
                   "244 / 126"))
    m = need(r"\| 6 \| `0x40` \| `bInterVehicleCollision` \|", src["FLAGS"], "bit-6 census row")
    checks.append(("BOX_FLAGS names the 0x4C bit and censuses it", bool(m), "bit 6 = bInterVehicleCollision"))
    checks.append(("the constraint 171462 is decoded only in COLLISION_GEOM.md",
                   "171462" not in src["BOXES"] and "171462" not in src["CONVEX"] and "171462" not in src["SHAPES"],
                   "no later card names it"))

    # ---- Q3: the four reviews' own figures
    cx = convex_cross(src["CONVEX"])
    checks.append(("CONVEX's element-0 cross-check reproduces GEOM's 10/16/7 and 8/12/6",
                   cx.get(169748, {}).get("a") == cx.get(169748, {}).get("b") == {"nV": 10, "tris": 16, "planes": 7}
                   and cx.get(169749, {}).get("a") == cx.get(169749, {}).get("b") == {"nV": 8, "tris": 12, "planes": 6},
                   "169748 10/16/7, 169749 8/12/6"))
    checks.append(("CONVEX closes both payloads with the 9-byte footer",
                   bool(re.search(r"\*\*25898\*\* of 25907", src["CONVEX"]))
                   and bool(re.search(r"\*\*8266\*\* of 8275", src["CONVEX"])),
                   "25898+9 / 8266+9"))
    checks.append(("MATRIX_ORDER leaves row/column UNSETTLED",
                   "row/column order: **UNSETTLED**" in src["MATRIX"], "sign stays conditional"))
    checks.append(("COLLISION_MODES.md still returns 3 UNKNOWN verdicts",
                   src["MODES"].count("**UNKNOWN**") == 3, "3 verdicts"))

    # ---- statement table + citation validation
    rows = statement_rows(cmp_ok, de_max, dt_max)
    bad = []
    for r in rows:
        for key, sub in r["ev"]:
            if sub not in src[key]:
                bad.append(f"{r['id']}: {sub!r} not in {PATH[key]}")
    checks.append(("every citation in the statement table is present in the file it names",
                   not bad, f"{sum(len(r['ev']) for r in rows)} citations" if not bad else "; ".join(bad[:3])))
    if bad:
        raise AuditError("citation validation failed:\n  " + "\n  ".join(bad))

    counts = {s: 0 for s in STATUS_ORDER}
    for r in rows:
        counts[r["status"]] += 1
    review_rows = [r for r in rows if not r["id"].startswith("G")]
    rev_sup = sum(1 for r in review_rows if r["status"] == "superseded")
    rev_open = sum(1 for r in review_rows if r["status"] == "open")
    rev_moot = sum(1 for r in review_rows if r.get("moot"))

    # ------------------------------------------------------------ render
    L: list[str] = []
    a = L.append
    a("# AUDIT_G301B - COLLISION_GEOM.md (G3-01b) against the later collision cards")
    a("")
    a("Generated by `Tools/scripts/audit_g301b.py` (`--write`); `--check` re-derives this file,")
    a("re-runs every check and fails if the text differs by one byte. Read-only on every input:")
    a("`COLLISION_GEOM.md` is audited, never edited; the later cards are quoted, never rewritten.")
    a("")
    a("Labels: **decoded** = read from bytes at a stated package/export/offset; **derived** = a")
    a("stated rule applied to decoded values; **UNKNOWN** = not decoded, with the reason. A status")
    a("word is one of: **still holds** (a later card reproduces it), **superseded** (a later card")
    a("replaces it with a stronger result), **wrong** (the bytes say otherwise), **open** (no later")
    a("card settles it).")
    a("")
    a("## 0. Answers")
    a("")
    a("1. **Yes - `COLLISION_BOXES.md` settles both halves of the question** (the box inventory")
    a("   and the extents convention) and every number still agrees. It decodes the chassis **2**")
    a("   boxes and the weapons **1** box inside byte-mapped")
    a("   payloads (1759/1759 and 143/143 B), states the element struct as **0x50** bytes with the")
    a("   extents at **0x40/0x44/0x48** and a bool word at **0x4C**, and decides the extents")
    a("   convention as **FULL lengths**. All three boxes' extents and centres match the G3-01b")
    a(f"   values to **{de_max:.4f} cm** (extents) and **{dt_max:.4f} cm** (centres).")
    a("2. **The `Batmobile_V3_Physics` bodies are decoded later** - `COLLISION_BOXES.md` maps every")
    a("   byte of 169750/169751, and `COLLISION_SHAPES.md` re-decodes them as the four-array")
    a("   aggregate (counts [0,2,0,1] and [0,1,0,0]). Their **constraint 171462** and the **Bounds**")
    a("   arrays are still open: no later card returns to them.")
    a(f"3. **{rev_open} of the {len(review_rows)} review points are still open; {rev_sup - rev_moot} are fixed by later")
    a(f"   cards and {rev_moot} (B9) is moot** because the artifact already carries the label the review")
    a("   asked for. The eight fixes: the 10894 selector reference, the 0x4C name, the sphyl count,")
    a("   the centres' label, the element chain, the oracle, the hull provenance, and the header-word")
    a("   model. The blocking mode review point is fixed by the selector cards; the boxes/cylinders")
    a("   reviews were never answered in their own artifacts.")
    a("")
    a("## 1. Inputs")
    a("")
    a("| key | file | bytes | sha256 | date |")
    a("|---|---|---:|---|---|")
    for k in ["GEOM", "BOXES", "CONVEX", "SHAPES", "FLAGS", "MATRIX", "CYL", "MODES", "POLARITY",
              "R_MAIN", "R_BOXES", "R_CYL", "R_MODE"]:
        p = ROOT / PATH[k]
        b = p.read_bytes()
        a(f"| {k} | `{PATH[k]}` | {len(b)} | `{hashlib.sha256(b).hexdigest()[:12]}` | {time.strftime('%Y-%m-%d', time.localtime(p.stat().st_mtime))} |")
    a("")
    a("Lineage (derived from the file mtimes): COLLISION_GEOM 11-03 01:16 -> CONVEX 01:59 ->")
    a("MODES 02:18 -> BOXES 02:47 -> CYLINDERS 03:43 -> SELECTOR 06:06 -> SHAPES 11-04 12:43 ->")
    a("BOX_FLAGS 14:43 -> MATRIX_ORDER 15:14 -> SELECTOR_POLARITY 22:13. \"Later card\" below means")
    a("a file later in that list.")
    a("")
    a("## 2. Question 1 - the three boxes")
    a("")
    a("### 2.1 What COLLISION_GEOM.md left open, and what settled it")
    a("")
    a("| open item in COLLISION_GEOM.md | settled by COLLISION_BOXES.md? | evidence (label) |")
    a("|---|---|---|")
    a("| chassis 2 boxes + weapons 1 box decoded | **yes** | header `box_count` 2 / 1 equals the decoded 2 / 1; 3 boxes decoded; payload 1759/1759 and 143/143 B exact (decoded) |")
    a("| extents at 0x40/0x44/0x48 | **yes, and now tag-proven** | three `FloatProperty` tags at logical 0x40/0x44/0x48 inside an 0x50-byte element (decoded) |")
    a("| extents convention (full vs half) | **yes: FULL lengths** | worst deviation 0.150 full vs 0.575 half; containment 28.1 cm vs 359.7 cm (derived + oracle) |")
    a("| centre by the inherited '12 bytes before the tags' rule | **superseded** | TM decoded: 16 floats, translation = floats 13..15; agrees on all 3 boxes (decoded) |")
    a("| rotation not decoded | **decoded** | 3x3 reading A orthonormal with det +1 on 131/131 boxes; reading B 0/131 (decoded) |")
    a("| sign of the 4.00 deg Y tilt | **still open** | MATRIX_ORDER: row/column order UNSETTLED, so the sign stays conditional (UNKNOWN) |")
    a("")
    a("### 2.2 Do the numbers still agree for the same boxes?")
    a("")
    a("| export / box | bone | GEOM extents (cm) | BOXES extents (cm) | abs diff (cm) | GEOM centre | BOXES translation | abs diff (cm) |")
    a("|---|---|---|---|---:|---|---|---:|")
    for r in cmp_rows:
        g = r["g"]
        bone = {169750: "Batmobile_Chassis", 169751: "Batmobile_Rig_Weapons_Trans"}[g["export"]]
        a("| {e} / {b} | `{bone}` | {ge} | {be} | {de:.4f} | {gc} | {bt} | {dt:.4f} |".format(
            e=g["export"], b=g["box"], bone=bone,
            ge=", ".join(f"{v:g}" for v in g["ext"]),
            be=", ".join(f"{v:g}" for v in r["ext"]),
            de=r["de"],
            gc=", ".join(f"{v:g}" for v in g["centre"]),
            bt=", ".join(f"{v:g}" for v in r["tr"]),
            dt=r["dt"]))
    a("")
    a(f"- derived: every row agrees within {de_max:.4f} cm on extents and {dt_max:.4f} cm on the")
    a("  centre. Both cards print 3 d.p.; the BOXES byte map carries one more digit (374.5361 /")
    a("  679.5852 / 345.6876 / 166.1769 / 189.3649), so the agreement is exact at the printed")
    a("  precision and within 0.001 cm with that extra digit (largest gap 345.6876 vs 345.688).")
    a("- decoded: the boxes are the same three (same exports, same indices, same extents), so no")
    a("  row was silently re-assigned.")
    a("")
    a("## 3. Question 2 - the `Batmobile_V3_Physics` bodies")
    a("")
    a("| object | decoded after G3-01b? | where | state |")
    a("|---|---|---|---|")
    a("| body 169750, bone `Batmobile_Chassis`, AggGeom 1759 B | **yes** | BOXES byte map 1759/1759; SHAPES counts [0,2,0,1] | decoded |")
    a("| body 169751, bone `Batmobile_Rig_Weapons_Trans`, AggGeom 143 B | **yes** | BOXES byte map 143/143; SHAPES counts [0,1,0,0] | decoded |")
    a("| box records of both bodies (3 boxes) | **yes** | BOXES: TM + 0x40/0x44/0x48 + 0x4C word + end, 118 B each | decoded |")
    a("| 0x4C bool word | **name only** | BOX_FLAGS: bit 6 = `bInterVehicleCollision`, 5 boxes / 4 bodies | name decoded from the SDK, behaviour UNKNOWN |")
    a("| 169750's single convex element (1498 B) | **yes** | BOXES, using G3-01c's proven layout; `ElemBox == vertex bounds` holds | decoded |")
    a("| constraint 171462 (names at 84/92/100, vectors at 144/156/168) | **no** | only COLLISION_GEOM.md decodes it | UNKNOWN (offset names) |")
    a("| PhysicsAsset `Bounds` array (72 B, count 2) | **no** | BOXES U-4 / CONVEX U-4 | UNKNOWN (layout) |")
    a("| StaticMesh `Bounds` (175973 / 175974) | **no** | CONVEX: 4 unnamed tags, no Bounds struct | UNKNOWN (layout) |")
    a("")
    a("So the bodies are not still open: two later cards decode them completely. What remains open")
    a("is the **constraint** and the **bounds** - neither body is missing.")
    a("")
    a("## 4. Question 3 - the reviews, point by point")
    a("")
    a("The G3-01b work carries four reviews. Their verdicts: main **minor issues**, boxes **minor")
    a("issues**, cylinders **minor issues**, mode **needs rework**. The table lists every point and")
    a("whether a later card fixed it.")
    a("")
    a("| review | point | fixed by a later card? | how |")
    a("|---|---|---|---|")
    origin = {"M": "main", "B": "boxes", "C": "cylinders", "D": "mode"}
    for r in review_rows:
        a(f"| {origin[r['id'][0]]} | {r['id']} - {r['claim'].split(': ', 1)[-1]} | "
          f"{'yes' if r['status'] == 'superseded' else 'no'} | {r['later']} |")
    a("")
    a("### 4.1 The one blocking point")
    a("")
    a("The mode review's I1 said the selector *is* referenced by UnrealScript and the card's")
    a("\"native, unreferenced\" conclusion was false. Two later cards settle it: `COLLISION_SELECTOR.md`")
    a("decodes export 10894 and its value -> mesh table, and `SELECTOR_POLARITY.md` decides the")
    a("branch polarity (body runs when the comparison is true; 4 of 4 decisive cases, 6 of 6")
    a("cases in total). `COLLISION_MODES.md` itself was never revised, so its three UNKNOWN")
    a("verdicts still print - the answer exists, the card does not carry it.")
    a("")
    a("### 4.2 Where the reviews and the later cards disagree")
    a("")
    a("- **boxes review I-3** proposed that the 4.00 deg tilt's sign is fixed because the planes are")
    a("  rows. `MATRIX_ORDER.md` (later than the review's target cards) reports **row/column order")
    a("  UNSETTLED**: the build stores no transform both as a 64-byte FMatrix and as a quaternion,")
    a("  and the one candidate (the mesh reference pose) is the identity. So `COLLISION_BOXES.md`'s")
    a("  conditional +/-4.00 deg is the correct state, and the review's proposed fix is not adopted.")
    a("- **boxes review I-1/I-2** are fixed, but by different later cards than the ones the review")
    a("  named: I-1 by `BOX_FLAGS.md` (a 4648-box census, bit 6 = `bInterVehicleCollision`) and I-2")
    a("  by `COLLISION_SHAPES.md` (25 bodies with spheres, 271 with capsules, 3276 bodies closing).")
    a("")
    a("## 5. Statement table")
    a("")
    a("Every statement of `COLLISION_GEOM.md` (G ids) and every review point (M/B/C/D ids).")
    a("")
    a("| # | statement | status | later evidence |")
    a("|---|---|---|---|")
    for r in rows:
        a(f"| {r['id']} | {r['claim']} | **{r['status']}** | {r['later']} |")
    a("")
    a("### 5.1 Tally")
    a("")
    a("| status | statements | of which GEOM | of which review |")
    a("|---|---:|---:|---:|")
    for s in STATUS_ORDER:
        n_all = counts[s]
        n_g = sum(1 for r in rows if r["status"] == s and r["id"].startswith("G"))
        a(f"| {s} | {n_all} | {n_g} | {n_all - n_g} |")
    a(f"| **total** | **{len(rows)}** | **{sum(1 for r in rows if r['id'].startswith('G'))}** | "
      f"**{sum(1 for r in rows if not r['id'].startswith('G'))}** |")
    a("")
    a("## 6. Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for name, ok, detail in checks:
        a(f"| {name} | **{'PASS' if ok else 'FAIL'}** | {detail} |")
    a("")
    a(f"{sum(1 for _, ok, _ in checks if ok)}/{len(checks)} checks passed.")
    a("")
    a("## 7. UNKNOWN")
    a("")
    a("- **Constraint 171462's field names** (offsets 84/92/100 name bones, 144/156/168 carry")
    a("  vectors). Only G3-01b decodes them; no later card re-reads the export, so the names are")
    a("  not established. It would be settled by an `RB_ConstraintSetup` layout (G3-06) or by a")
    a("  second constraint setup with a known field set.")
    a("- **The Bounds arrays** (PhysicsAsset 72 B / 2 elements; StaticMesh 175973/175974). Both")
    a("  stay UNKNOWN in `COLLISION_BOXES.md` and `COLLISION_CONVEX.md`; the SDK tree ships no")
    a("  StaticMesh layout either.")
    a("- **The 0x4C bit's behaviour.** The name (`bInterVehicleCollision`) comes from the SDK layout")
    a("  and the census, not from an observed effect; `Batmobile_Chassis` box 0 is the only drivable")
    a("  box with bit 6 set, so the flag is present but its consequence is unobserved.")
    a("- **The 4.00 deg tilt's sign** (rows vs columns). `MATRIX_ORDER.md`: UNSETTLED.")
    a("- **Which collision component is attached at runtime.** The setter's branch is decoded, the")
    a("  sampler logs the mode value, but no card logs an attachment, so the mode -> mesh step is")
    a("  still an inference from the value -> mesh table.")
    a("")
    a("## 8. Reproduce")
    a("")
    a("```bash")
    a("cd \"E:/Modding/JC3-Batmobile\"")
    a("python Tools/scripts/audit_g301b.py --write   # writes this file")
    a("python Tools/scripts/audit_g301b.py --check   # re-derives, byte-compares, re-runs checks")
    a("```")
    a("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write the audit")
    g.add_argument("--check", action="store_true", help="re-derive and compare")
    args = ap.parse_args(argv)

    try:
        text = build()
    except AuditError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2

    failed = [ln for ln in text.splitlines() if "**FAIL**" in ln]
    if failed:
        print("FAIL: check(s) did not pass:\n  " + "\n  ".join(failed), file=sys.stderr)
        if args.write:
            OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
        return 2

    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
        n = text.count("\n") + 1
        print(f"WROTE {OUT.relative_to(ROOT)} ({n} lines)")
        return 0

    if not OUT.is_file():
        print(f"FAIL: {OUT.relative_to(ROOT)} does not exist (run --write)", file=sys.stderr)
        return 1
    on_disk = OUT.read_text(encoding="utf-8")
    if on_disk != text + "\n":
        print(f"DRIFT: {OUT.relative_to(ROOT)} differs from a fresh derivation (run --write)",
              file=sys.stderr)
        return 1
    print(f"AUDIT_G301B.md current ({text.count(chr(10)) + 1} lines, all checks pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
