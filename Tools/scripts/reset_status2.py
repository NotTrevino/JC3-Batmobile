#!/usr/bin/env python3
"""reset_status2.py - G3-21b: RESET_FINDINGS R-1..R-6 re-rated against every G3 report on disk.

This is the G3-21 refresh.  It keeps G3-21's method (a verdict is computed from cited cards'
own STATUS lines, their reviews and re-runnable evidence probes) and adds two things:

  1. every card in tmp/freebuff/reports/G3-*.md is scanned, including the follow-up cards that
     have no GRAB_BACKLOG row (G3-01e-fix, G3-02g..02k, G3-04d, G3-06b, G3-09c, G3-10c..10i,
     G3-11c/11d, G3-12c..12e, G3-19b, G3-20b..20d);
  2. each item declares the **newest card it cites** (`newest`), and `--check` recomputes the
     newest cited card from the reports' mtimes and fails if the declaration is wrong.  So an
     item rated before G3-10i or G3-19b landed cannot stay stale without the check failing.

Reads (never edits): RESET_FINDINGS.md, GRAB_BACKLOG.md, tmp/freebuff/reports/G3-*.md,
tmp/freebuff/reports/review-*.md, and the Research/ or Working/ outputs each probe names.

Writes: Research/RESET_STATUS2.md

Usage:
    uv run python Tools/scripts/reset_status2.py --write
    uv run python Tools/scripts/reset_status2.py --check
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BACKLOG = os.path.join(REPO, "GRAB_BACKLOG.md")
REPORTS = os.path.join(REPO, "tmp", "freebuff", "reports")
OUT = os.path.join(REPO, "Research", "RESET_STATUS2.md")
PREV = os.path.join(REPO, "Research", "RESET_STATUS.md")
# this refresh's own report is never evidence (it is rewritten after the document)
SELF = {"G3-21.md", "G3-21b.md"}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def mtime(path):
    return time.strftime("%Y-%m-%dT%H:%M", time.localtime(os.path.getmtime(path)))


# ------------------------------------------------------------------ backlog + reports
def backlog_cards():
    cards = []
    for line in read(BACKLOG).splitlines():
        if not line.startswith("#### G3-"):
            continue
        body = line[5:]
        cid, _, rest = body.partition("·")
        cid = cid.strip()
        rest = rest.strip()
        m = re.search(r"\b([SML])\s*·\s*deps:\s*([^·]*?)\s*(?:·\s*serves:\s*(.*))?$", rest)
        if m:
            title = rest[:m.start(1)].strip(" ·")
            cards.append({"id": cid, "title": title, "size": m.group(1),
                          "deps": m.group(2).strip(), "serves": (m.group(3) or "").strip()})
        else:
            cards.append({"id": cid, "title": rest, "size": "", "deps": "", "serves": ""})
    return cards


def report_status(path):
    for line in read(path).splitlines()[:16]:
        m = re.search(r"STATUS:?\s*(.+)", line, re.I)
        if m:
            return m.group(1).strip().strip("*").strip()
    return None


def classify(raw):
    if raw is None:
        return None
    low = raw.lower().lstrip("*_` ")
    if low.startswith("done"):
        return "done"
    if low.startswith("partial") or low.startswith("split"):
        return "partial"
    return "stated"


def review_verdict(path):
    if not os.path.exists(path):
        return None
    for line in read(path).splitlines()[:40]:
        m = re.search(r"VERDICT:\s*\**([A-Za-z][A-Za-z ]+?)\**\s*$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def reports_for(card_id, available):
    exact = [f for f in available if f[:-3] == card_id]
    if exact:
        return exact
    return sorted(f for f in available if f[:-3].startswith(card_id + "-"))


def card_info(cid, available, by_id):
    reps = reports_for(cid, available)
    st = [report_status(os.path.join(REPORTS, r)) for r in reps]
    kinds = [classify(s) for s in st]
    if not reps:
        status = None
    elif "partial" in kinds:
        status = "partial"
    elif all(k == "done" for k in kinds):
        status = "done"
    else:
        status = kinds[0] or "stated"
    reviews = []
    for r in reps:
        v = review_verdict(os.path.join(REPORTS, "review-" + r))
        if v and v not in reviews:
            reviews.append(v)
    newest = max(((mtime(os.path.join(REPORTS, r)), r) for r in reps), default=None)
    return {"id": cid, "reports": reps, "status": status, "status_raw": st, "reviews": reviews,
            "newest_mtime": newest[0] if newest else None,
            "newest_report": newest[1] if newest else None,
            "title": by_id[cid]["title"] if cid in by_id
                     else "(follow-up card, no GRAB_BACKLOG row)"}


def run_probe(p):
    if p.get("glob"):
        hits = glob.glob(os.path.join(REPO, p["glob"]))
        return {"ok": len(hits) >= p.get("min", 1), "seen": "%d file(s)" % len(hits),
                "want": ">= %d file(s)" % p.get("min", 1), "path": p["glob"],
                "label": p["label"]}
    path = os.path.join(REPO, p["path"])
    if not os.path.exists(path):
        return {"ok": False, "seen": "missing", "want": "exists", "path": p["path"],
                "label": p["label"]}
    if p.get("needle") is None:
        return {"ok": True, "seen": "exists", "want": "exists", "path": p["path"],
                "label": p["label"]}
    text = read(path)
    ok = p["needle"] in text
    return {"ok": ok, "seen": "contains" if ok else "does not contain",
            "want": repr(p["needle"]), "path": p["path"], "label": p["label"]}


# ------------------------------------------------------------------ the six items
ITEMS = [
    {
        "id": "R-1",
        "question": "find BmAK's drivable collision: package, class, shape.",
        "core": ["G3-01c", "G3-01d", "G3-01e", "G3-10", "G3-10d", "G3-10e"],
        "supporting": ["G3-01", "G3-01b", "G3-01e-fix", "G3-10b", "G3-10c", "G3-10f",
                       "G3-10g", "G3-10h", "G3-10i"],
        "newest": "G3-10i",
        "newest_note": "the runtime treatment of a constraint whose second body is absent; it "
                       "closes the 'which JC3 body is the partner' row of this item",
        "facts": [
            ("Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "the selector is UnrealScript: `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`, "
             "export 10894, 253 script bytes, 7 calls, mesh table {0: none, 1: "
             "BatmanCollisionMeshPursuitMode, 2: BatmanCollisionMeshBattleMode} (G3-01e)"),
            ("Research/BatmobileGrab/COLLISION_CONVEX.md",
             "56 convex elements decoded (43 battle / 13 pursuit) with the FKConvexElem accounting "
             "oracles (G3-01c)"),
            ("Research/BatmobileGrab/COLLISION_BOXES.md",
             "131/131 box transforms orthonormal with det +1; extents at 0x40/0x44/0x48, packed bool "
             "word at 0x4C, element stride 0x50 (G3-01b-boxes)"),
            ("Research/BatmobileGrab/COLLISION_FRAME.md",
             "the decoded convex union sits on the render mesh through component offsets only: "
             "pursuit hull margin min +0.22 cm, pursuit collision shifted +5.0 cm in X, battle mesh "
             "rotated 4.1199 deg (G3-01d)"),
            ("Research/BatmobileGrab/SM_BOUNDS.md",
             "the collision meshes' own `FBoxSphereBounds` are decoded from the untagged native data "
             "of 175973 / 175974 (native+0): origin (5.8023, 0, 146.4544) / (8.5922, 0, 117.3755), "
             "extent (356.3003, 245.6297, 146.4651) / (352.8289, 175.9482, 116.6620), radius "
             "434.8802 / 382.2412 cm, 37/52 BmGame StaticMesh exports carrying the same block "
             "(chase-G3-01b-boxes-u4)"),
            ("Research/JC3Grab/PHYSICS_LIMITS.md",
             "the donor's limit atoms and their fleet table are decoded with a per-atom audit "
             "(G3-10e)"),
            ("Research/JC3Grab/PHYSICS_ROLES4.md",
             "five candidate rules for the constraint partner are scored over 50 fleet files / 494 "
             "constraint records / 3556 bodies and **none** fits every record; the one positive "
             "structural result is that constraints pair the `.epe` part tree in 439/439 cases "
             "(G3-10d)"),
            ("Research/JC3Grab/CONSTRAINT_CODE.md",
             "`hknpConstraintCinfo` carries one real body (`bodyA`, +0x08) and an invalid-body "
             "marker in `bodyB` (+0x0c = 0x7fffffff in 494/494 shipped records); the engine code "
             "writes that value to detach a body, so the stored partner is *absent*, not body 0 "
             "(G3-10h)"),
            ("Research/JC3Grab/CONSTRAINT_CODE2.md",
             "the runtime loop validates both ids against 0x7fffffff, the body-array capacity and "
             "the body live-flag and **drops** every failing record before `addConstraint`; no fixed "
             "body is substituted, so a second body only ever comes from caller-assembled cinfos "
             "(G3-10i)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "needle": "BatmanCollisionMeshPursuitMode",
             "label": "the mode→mesh table is in the record"},
            {"path": "Research/BatmobileGrab/COLLISION_CONVEX.md", "needle": "56",
             "label": "the 56 decoded elements are in the record"},
            {"path": "Research/BatmobileGrab/COLLISION_BOXES.md", "needle": "131",
             "label": "the 131-box oracle is in the record"},
            {"path": "Research/BatmobileGrab/SM_BOUNDS.md", "needle": "FBoxSphereBounds",
             "label": "the mesh bounds decode is in the record"},
            {"path": "Research/JC3Grab/CONSTRAINT_CODE2.md", "needle": "0x7fffffff",
             "label": "the runtime sentinel decode is in the record"},
            {"path": "Research/JC3Grab/PHYSICS_ROLES4.md", "needle": "494",
             "label": "the partner-candidate fleet score is in the record"},
        ],
        "remaining": [
            "The constraint partner question is answered at the *record* level (absent, not hidden) "
            "but not at the *authoring* level: `G3-10d`/`G3-10h`/`G3-10i` show the stored `bodyB` "
            "is `0x7fffffff`, that the loader drops such a record, and that game code builds cinfos "
            "from two live ids — no decoded cinfo shows *which* two bodies the car's constraints "
            "are meant to join.",
            "The branch polarity of the BmAK selector is still not decoded (`G3-01e`), so \"the body "
            "runs when the comparison is true\" stays unproven; the value→mesh table does not "
            "depend on it.",
            "`G3-01` and `G3-01b` themselves have no report file — their facts live in "
            "`COLLISION.md` / `COLLISION_GEOM.md` and were carried forward by the `G3-01b-*`, "
            "`G3-01c`, `G3-01e` reports. Their STATUS is second-hand here.",
            "`G3-01e` carries a `needs rework` review: the byte decode and the value→mesh table "
            "survive an independent re-read, but one `decoded` claim about the two `DriverLeft` "
            "branches' guard names is contradicted by the script, and the runtime narrative drops "
            "one of the four `0→1` transitions.",
        ],
        "unknowns": [
            "Which live body pair each car constraint joins at simulation time (the stored second "
            "id is the sentinel; the caller that assembles the real cinfo is not identified for the "
            "Batmobile).",
            "Whether the JC3 physics frame equals the BmAK collision frame — the +5.0 cm / 4.1199 "
            "deg link is decoded from packages, never observed.",
        ],
    },
    {
        "id": "R-2",
        "question": "grab `BmInput.ini` and the Batmobile input path; grab JC3's vehicle input "
                    "model (for D-11).",
        "core": ["G3-02", "G3-02b", "G3-02c", "G3-02e", "G3-02i", "G3-08"],
        "supporting": ["G3-02d", "G3-02f", "G3-02g", "G3-02h", "G3-02j", "G3-02k"],
        "newest": "G3-02k",
        "newest_note": "the eject's `TriggerSpecialMove` target and the launch vector, read from "
                       "the move asset and its animation",
        "facts": [
            ("Research/BatmobileGrab/CONFIG.md",
             "`BmGame/Config/BmInput.ini` is read as a whole: 43,825 B, 568 rows, "
             "`Engine.PlayerInput` `Bindings` (G3-03) — the reset's \"never read\" is no longer true"),
            ("Research/BatmobileGrab/BINDINGS_MERGED.md",
             "the ini merge rule is established from the install (plain lines append, `-` removes "
             "the entry whose canonical struct matches, no `+` occurs) and the effective merged "
             "binding array is produced (G3-02g)"),
            ("Research/JC3Grab/INPUT.md",
             "JC3 defines vehicle controls in `settings/keymap_gamepad.bin` and "
             "`settings/keymap_keyboard.bin`, with a per-binding record format decoded and a stated "
             "yes/no/UNKNOWN per BmAK action (G3-08)"),
            ("Research/BatmobileGrab/CONTROLS_NATIVE2.md",
             "native mode flags named from the BmSDK dump: `0x10` = `bWeaponsReady`, `0x8000` = "
             "`bBattleModeLocked`; the two `±0.707` comparisons at 0x140063f04 / 0x140063f22 "
             "(G3-02e)"),
            ("Research/BatmobileGrab/DRIVINGMODE.md",
             "the `DrivingMode` state's exec bodies decode: 16 command bodies, 51 call sites with "
             "arguments; `EjectFromVehicle` → `CantEjectFromBatmobile` / "
             "`CheckSpaceAboveBatmobileCockpit` / `DriverLeave(true)` / `PlayCockpitOpenFast`, and "
             "`ToggleBattleMode` passes the name indices of `BattleMode` (5269) and `PursuitMode` "
             "(61474) to `TryToChangeMode` (G3-02i)"),
            ("Research/BatmobileGrab/EJECT_VELOCITY.md",
             "the `SetRBLinearVelocity` argument in `EjectFromVehicle` is the literal (0, 0, 0) "
             "cm/s with `bAddToCurrent = false`, applied to `Car.Mesh` — a stop, not a launch "
             "(G3-02j)"),
            ("Research/BatmobileGrab/EJECT_MOVE.md",
             "`TriggerSpecialMove` dispatches on `Car.ShortRangeGlideKick`, whose class default is "
             "`GlideKick.GlideKickShort_FromBatmobile`; the launch is the animation's root-motion "
             "translation (G3-02k)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/CONFIG.md", "needle": "BmInput.ini",
             "label": "BmInput.ini is in the config record"},
            {"path": "Research/BatmobileGrab/BINDINGS_MERGED.md", "needle": "Bindings",
             "label": "the merge rule / merged table is in the record"},
            {"path": "Research/JC3Grab/INPUT.md", "needle": None,
             "label": "the JC3 input model document exists"},
            {"path": "Research/BatmobileGrab/CONTROLS_NATIVE2.md", "needle": "bBattleModeLocked",
             "label": "the battle-mode flag is named in the native record"},
            {"path": "Research/BatmobileGrab/DRIVINGMODE.md", "needle": "ToggleBattleMode",
             "label": "the script-side mode switch is decoded"},
            {"path": "Research/BatmobileGrab/EJECT_MOVE.md", "needle": "GlideKick",
             "label": "the eject's move asset is decoded"},
        ],
        "remaining": [
            "`G3-02`, `G3-02b`, `G3-02c`, `G3-02d`, `G3-02f` still have no report files; the "
            "config→script→native chain is evidenced only by its outputs (`CONFIG.md`, "
            "`CONTROLS*.md`, `BINDINGS_MERGED.md`).",
            "`G3-02e` is partial: the float at `[Pawn.Mesh + 0xd8]` compared against `±0.707` has "
            "no decoded field name, and its \"no native route from driving input to the exit/eject "
            "execs\" is a decoded negative — `G3-02i` now supplies the positive route in bytecode, "
            "but which branch runs is control flow and stays UNKNOWN.",
            "The user-stated button meanings (LT hold = battle, B = track/immobilizer, LB = exit, "
            "A = eject) are still not proven end to end: `G3-02i`/`G3-02j`/`G3-02k` decode what the "
            "commands *do*, not which input reaches them at runtime.",
            "`CONFIG.md` is stale: `review-G3-03.md` records that its `--check` fails on the current "
            "install (three ini files rewritten 64 minutes after generation; 41 rows changed "
            "identity). The binding rows are right in method, not guaranteed current in value.",
        ],
        "unknowns": [
            "The name of the float compared against `±0.707`, and which entity state it measures.",
            "Whether JC3 exposes the three actions D-11 needs (battle toggle, immobilizer, eject) "
            "for a car module: `INPUT.md` gives per-action verdicts, not a mapping.",
        ],
    },
    {
        "id": "R-3",
        "question": "build a runtime oracle. Measure in game which resources the drop loaded, and "
                    "where collision and mesh actually sit, before touching physics again.",
        "core": ["G3-07", "G3-07a"],
        "supporting": [],
        "newest": "G3-07a",
        "newest_note": "the read-only runtime layout is still the newest card that touches a runtime "
                       "measurement; no new runtime card landed in this window",
        "facts": [
            ("Research/BatmobileGrab/runtime/",
             "a read-only sampler's logs exist (`globals.json` + `samples-*.jsonl`), and `G3-01e` "
             "reads them: runtime mode values {0: 17, 1: 6} with 7 transitions, inside the callers' "
             "constant range"),
            ("Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "the runtime samples are cross-checked against decoded caller constants — still the "
             "only place in the project where a decoded value and a measured value meet"),
        ],
        "probes": [
            {"glob": "Research/BatmobileGrab/runtime/*.jsonl", "min": 1,
             "label": "runtime sample logs exist"},
            {"path": "Research/BatmobileGrab/COLLISION_SELECTOR.md", "needle": "runtime",
             "label": "the record shows the runtime cross-check"},
        ],
        "remaining": [
            "Neither measurement R-3 names is in any output: no document states which `.physicsc` "
            "the drop loads, and none states where the collision sits relative to the mesh **as "
            "measured in game** (the +5.0 cm and 4.1199 deg are decoded from packages).",
            "`G3-07` still has no report; `G3-07a` (static) is the only runtime-adjacent card and "
            "`Research/JC3Grab/RUNTIME_LAYOUT.md` does not exist, so the sampler's layout has no "
            "oracle-backed document.",
            "The sampler's provenance and scope are undocumented: the logs record the "
            "collision-selector mode field, not loaded resources.",
        ],
        "unknowns": [
            "Whether the game reads the built `.physicsc` at all — RESET_FINDINGS §4 question 1 is "
            "still unanswered; no output distinguishes the built file from the vanilla one.",
            "Whether the physics frame equals the render frame for the spawned entity in game.",
            "What the remaining 41 Serpente part bodies contribute at runtime.",
        ],
    },
    {
        "id": "R-4",
        "question": "decode both renderers' colour pipelines far enough to state whether an exact "
                    "conversion exists (and, if not, what the closest mapping depends on).",
        "core": ["G3-03", "G3-04", "G3-04b", "G3-09", "G3-09b", "G3-09c"],
        "supporting": ["G3-04c", "G3-04d"],
        "newest": "G3-04d",
        "newest_note": "the cooked shader caches, and the proof that no `RDEF` chunk survives — the "
                       "binding from constants to output colour cannot be read from the install",
        "facts": [
            ("Research/BatmobileGrab/COLOUR.md",
             "the BmAK chain is decoded to the master: base colour [0.02579, 0.02579, 0.03, 1.0] "
             "matches T-MA3, 3 objects, 5 slots, 31 config terms (G3-04)"),
            ("Research/BatmobileGrab/COLOUR_FUNCTIONS.md",
             "the colour logic is **not** in the cooked bytes: 944/944 `FunctionExpressions` slots "
             "are zero, so no operator graph and no combine rule is claimed (G3-04b)"),
            ("Research/BatmobileGrab/COLOUR_PARAMS.md",
             "the parameter layer is complete instead: 82/87 vector defaults, 52/52 MIC overrides "
             "paired to their expression by GUID (G3-04c)"),
            ("Research/BatmobileGrab/SHADER_COMBINE.md",
             "both cooked shader caches decode (38,201 + 2,098 DXBC containers) but hold only "
             "`ISGN`/`OSGN`/`SHEX`: **0 `RDEF` chunks**, so no constant→slot naming exists and the "
             "bytecode reads `cb0[..]` by number only (G3-04d, partial)"),
            ("Research/JC3Grab/COLOUR.md",
             "the JC3 side is decoded at the container level: `CarPaintMM` block offsets, 10 palette "
             "tint records, sampler slots corroborated (G3-09)"),
            ("Research/JC3Grab/COLOUR_NATIVE.md",
             "in `JustCause3.exe` the palette schema names sit in exactly the `.vmodc` order and "
             "have 0 code references; 3 functions reference `CarPaintMM` (G3-09b)"),
            ("Research/JC3Grab/COLOUR_NATIVE2.md",
             "the 15 \"all-zero\" parameter constants are **not** zero: as `u32` they are small "
             "integers 0..10 (14 of 15 tuples have a non-zero word), as `f32` denormals, and the "
             "consuming code reads them as integers — the \"all zeros\" conclusion is corrected "
             "(G3-09c)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/COLOUR_FUNCTIONS.md", "needle": "FunctionExpressions",
             "label": "the stripped operator graph is recorded"},
            {"path": "Research/BatmobileGrab/SHADER_COMBINE.md", "needle": "RDEF",
             "label": "the missing-constant-table finding is in the record"},
            {"path": "Research/JC3Grab/COLOUR.md", "needle": "Palette",
             "label": "the JC3 palette decode is recorded"},
            {"path": "Research/JC3Grab/COLOUR_NATIVE2.md", "needle": "denormal",
             "label": "the corrected constant block is in the record"},
        ],
        "remaining": [
            "The question R-4 asks — whether an exact conversion exists — is still not answered, and "
            "`G3-04d` now closes one escape route: the link from named constants to output colour "
            "cannot be read from the cooked shaders because every container lacks `RDEF`.",
            "`G3-09`'s Done (on-screen colour as a function of named terms, calibrated on >=3 "
            "vanilla paints, error stated) needs the fixed frame from R-3 and is not met; no "
            "on-screen value is claimed anywhere.",
            "The JC3 tint write is offset-level and its instruction is unidentified; no exposure or "
            "tonemap constant is attributed.",
            "Four colour cards are under a `needs rework` review (`G3-04b` vector defaults, `G3-09` "
            "palette \"referenced by no file\", `G3-03` stale against the install, `G3-09b`'s zero "
            "constants). `G3-09c` corrects the last of those; the other three stand.",
        ],
        "unknowns": [
            "How the BmAK master combines its decoded parameters (expression bodies stripped, and "
            "the shader constants are unnamed without `RDEF`).",
            "Which instruction fills the `CarPaintMM` dynamic float4s, and which of them is the tint.",
            "JC3's exposure/tonemap values, and what the closest defensible BmAK→JC3 mapping "
            "depends on.",
        ],
    },
    {
        "id": "R-5",
        "question": "reconcile `T_ROWS.jsonl` against the built files: for every row, translated / "
                    "not / guessed, with the evidence.",
        "core": ["G3-11", "G3-11b", "G3-20"],
        "supporting": ["G3-11c", "G3-11d", "G3-20b", "G3-20c", "G3-20d"],
        "newest": "G3-20d",
        "newest_note": "the provenance of the pre-reset source files: which script produced each, "
                       "and the 69/27 split of G3-20b's OPEN rows",
        "facts": [
            ("Working/Translation/LEDGER_AUDIT.md",
             "198/198 rows classified against the built files: 85 TRANSLATED, 7 GUESSED, 106 NOT "
             "TRANSLATED (G3-11) — the 85 is not a translation count, see review below"),
            ("Working/Translation/LEDGER_AUDIT2.md",
             "the 72 in-scope rows re-checked with the right decoders: 19 changed, 53 kept; after: "
             "42 TRANSLATED, 0 GUESSED, 25 NOT TRANSLATED, 5 REFUTED (G3-11b)"),
            ("Working/Translation/LEDGER_G3.md",
             "all 198 rows now list the G3 result that supplies, corrects or refutes them, or the "
             "card that would (G3-20)"),
            ("Working/Translation/LEDGER_G3B.md",
             "105 rows of groups T-1, T-2b and T-13 carry a quoted card line or an OPEN route, with "
             "18 verdicts (G3-20b, partial)"),
            ("Working/Translation/MISSING_ROWS.md",
             "the two gaps the audit could not see — ALB-2 and T-13 — get row proposals, including "
             "`PAINT_ALBEDO_GAIN = 4` as a hand-entered literal over a decoded effective paint "
             "colour (G3-11c)"),
            ("Working/Translation/LEDGER_G3C.md",
             "the remaining groups are sourced the same way, closing the per-row G3 pass (G3-20c)"),
            ("Working/Translation/LEDGER_SOURCES.md",
             "G3-20b's 96 OPEN rows split into 69 that rest on re-derivable evidence and 27 that do "
             "not; all seven pre-reset producers re-run green today (7/7 checks exit 0) (G3-20d)"),
        ],
        "probes": [
            {"path": "Working/Translation/LEDGER_AUDIT.md", "needle": "198",
             "label": "the 198-row audit exists"},
            {"path": "Working/Translation/LEDGER_AUDIT2.md", "needle": "19",
             "label": "the 19 changed rows are recorded"},
            {"path": "Working/Translation/LEDGER_G3.md", "needle": "T-G1",
             "label": "the per-row G3 sourcing exists"},
            {"path": "Working/Translation/LEDGER_SOURCES.md", "needle": "69",
             "label": "the 69/27 provenance split is in the record"},
        ],
        "remaining": [
            "`review-G3-11.md` (needs rework) shows **35 of the 85 TRANSLATED rows are not "
            "supported** by the script's own definition: 34 cite files whose `owner_card` in "
            "`Builds/bm-RC1/receipt.json` is an earlier lineage and `T-DM1` cites a vanilla-owned "
            "`.vmodc`. `G3-20d`'s provenance pass addresses exactly this, but the audit file itself "
            "still carries the unsupported count.",
            "`G3-20b` is partial: 96 rows stayed OPEN at that pass (69 re-derivable, 27 not).",
            "The ledger file itself is untouched by design, so its 13 `blocked` / 40 `next` flags "
            "still disagree with the audits' verdicts until someone applies them.",
        ],
        "unknowns": [
            "None for the classification itself; the open set is the 27 rows whose evidence cannot "
            "be re-derived from the current tree (G3-20d).",
        ],
    },
    {
        "id": "R-6",
        "question": "decode the 925 untagged objects that touch the vehicle (handling, upright, "
                    "visual damage, materials).",
        "core": ["G3-05", "G3-06", "G3-06b", "G3-12", "G3-12b", "G3-12c", "G3-12d"],
        "supporting": ["G3-05b", "G3-12e", "G3-14", "G3-19", "G3-19b"],
        "newest": "G3-19b",
        "newest_note": "the last undecoded donor block (`GeneralMkIII` in the three signature "
                       "`.rbm`s) is now accounted byte-for-byte",
        "facts": [
            ("Research/BatmobileGrab/REMAINDER.md",
             "all 925 untagged objects classified: 768 empty stubs, 152 native records, 5 "
             "closes-from-offset; 17 reachable from the vehicle chain, 3 UNKNOWN; 587 partial "
             "objects accounted (70/23/40/454) (G3-06)"),
            ("Research/BatmobileGrab/CLASS_DEFAULTS.md",
             "the vehicle's class defaults are now **values, not descriptors**: "
             "`Default__RVehicleBatmobile` is read tag by tag (274 tag rows), which is where "
             "`REMAINDER.md` left the 97 property values UNKNOWN (G3-06b)"),
            ("Research/BatmobileGrab/PACKAGES_G305.md",
             "20 packages / 320,415 exports censused, including `Startup`/`StartupPatch` (G3-05)"),
            ("Research/BatmobileGrab/AUDIO_BANKS.md",
             "the `AkBank` carriers and the 29 referenced banks are indexed per package, with the "
             "absent banks named (G3-14)"),
            ("Research/JC3Grab/DECODE_DEPTH.md",
             "566/566 donor files classified with a per-family oracle (G3-12)"),
            ("Research/JC3Grab/DECODE_DEPTH2.md",
             "the containers at G3-12b: 71 of 116 `.ddsc` FULL / 45 PARTIAL, 4 `.pfxc` PARTIAL"),
            ("Research/JC3Grab/DECODE_DEPTH3.md",
             "the PARTIAL families ranked and the largest decoded: the 116 `.ddsc` carry 99.3 % of "
             "the graded PARTIAL bytes (G3-12c), and G3-19 finishes the four files"),
            ("Research/JC3Grab/DECODE_DEPTH2.md",
             "**corrected by G3-12d**: `.ddsc` 116/116 FULL (the 84-byte tail is one record per "
             "absent mip of the full chain, 78 records, tag `0x01000010`) and `.pfxc` 4/4 FULL "
             "(there is no trailing blob — the 1920 read as an offset is a section length)"),
            ("Research/JC3Grab/DECODE_DEPTH7.md",
             "`v0300_car_kensington_sportsmuscle_civilian_01.epe` round-trips to 2,293 differing "
             "bytes (2.09 %), every one attributed (G3-12e)"),
            ("Research/JC3Grab/DECODE_DEPTH4.md",
             "the three signature `.rbm`s' block-1 `GeneralMkIII` payloads account byte-for-byte "
             "(7126 / 2592 / 1214 B), with positions re-checked against the block AABB (G3-19b)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/REMAINDER.md", "needle": "925",
             "label": "the 925-object record exists"},
            {"path": "Research/BatmobileGrab/CLASS_DEFAULTS.md", "needle": "Default__RVehicleBatmobile",
             "label": "the class-default values are decoded"},
            {"path": "Research/BatmobileGrab/AUDIO_BANKS.md", "needle": "AkBank",
             "label": "the bank index exists"},
            {"path": "Research/JC3Grab/DECODE_DEPTH.md", "needle": "566",
             "label": "the 566-file census exists"},
            {"path": "Research/JC3Grab/DECODE_DEPTH2.md", "needle": "116",
             "label": "the container decode exists"},
            {"path": "Research/JC3Grab/DECODE_DEPTH4.md", "needle": "GeneralMkIII",
             "label": "the last donor block is decoded"},
        ],
        "remaining": [
            "`review-G3-06.md` (needs rework) is now partly answered: `G3-06b` reads "
            "`Default__RVehicleBatmobile` itself, so the class-default VALUES are no longer "
            "UNKNOWN. What remains is the vehicle's *handling* defaults: `G3-06b` decodes the tags, "
            "and which of them feed suspension/steering is G3-10's JC3-side pairing, not decoded "
            "here.",
            "`G3-06b` is a follow-up of a card under a `needs rework` review, so this item's core "
            "set still carries `G3-06` as reviewed.",
            "45 `.ddsc` tails and the 4 `.pfxc` blobs were **closed** by `G3-12d` (116/116 and 4/4 "
            "FULL); the earlier \"stays UNKNOWN\" text in `RESET_STATUS.md` is superseded.",
            "`G3-19b` leaves one sub-field of the 20-byte vertex record (the two floats at +8/+12) "
            "measured but UNDECODED — every candidate layout tested fails its oracle.",
        ],
        "unknowns": [
            "The meaning of the two floats at +8/+12 of the `GeneralMkIII` vertex record.",
            "The 6 CDO component payloads past the 512 MiB decode budget (unchanged).",
            "Which decoded class-default field values the vehicle sim actually consumes.",
        ],
    },
]


def build():
    available = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPORTS, "G3-*.md"))
                       if os.path.basename(p) not in SELF)
    cards = backlog_cards()
    by_id = {c["id"]: c for c in cards}
    for c in cards:
        c.update({k: v for k, v in card_info(c["id"], available, by_id).items() if k != "id"})

    items = []
    for spec in ITEMS:
        core = [card_info(cid, available, by_id) for cid in spec["core"]]
        sup = [card_info(cid, available, by_id) for cid in spec["supporting"]]
        probes = [run_probe(p) for p in spec["probes"]]
        cited = core + sup
        with_reports = [c for c in cited if c["newest_mtime"]]
        newest = max(with_reports, key=lambda c: c["newest_mtime"]) if with_reports else None
        all_core_done = bool(core) and all(c["status"] == "done" for c in core)
        blocked = any("needs rework" in r.lower() for c in core for r in c["reviews"])
        any_probe = any(p["ok"] for p in probes)
        any_card = any(c["status"] in ("done", "partial", "stated") for c in core)
        if all_core_done and not blocked and all(p["ok"] for p in probes):
            verdict = "RESOLVED"
        elif any_probe or any_card:
            verdict = "PARTIAL"
        else:
            verdict = "OPEN"
        items.append({**spec, "core": core, "supporting": sup, "probe_results": probes,
                      "verdict": verdict, "newest_actual": newest["id"] if newest else None,
                      "newest_mtime": newest["newest_mtime"] if newest else None,
                      "newest_report": newest["newest_report"] if newest else None})

    extra = sorted({p[:-3] for p in available}
                   - {c["id"] for c in cards})
    prev_mtime = os.path.getmtime(PREV) if os.path.exists(PREV) else 0.0
    newer_reports = []
    for c in items:
        for card in c["core"] + c["supporting"]:
            for r in card["reports"]:
                p = os.path.join(REPORTS, r)
                if os.path.getmtime(p) > prev_mtime:
                    newer_reports.append((r, mtime(p), c["id"]))
    newer_reports = sorted(set(newer_reports), key=lambda t: (t[1], t[0]), reverse=True)
    return {"cards": cards, "items": items, "extra_reports": extra,
            "report_count": len(available), "prev_mtime": mtime(PREV) if prev_mtime else None,
            "newer_reports": newer_reports}


def render(doc):
    L = []
    a = L.append
    counts = {"RESOLVED": 0, "PARTIAL": 0, "OPEN": 0}
    for it in doc["items"]:
        counts[it["verdict"]] += 1
    a("# RESET_FINDINGS status (refreshed) — R-1 to R-6 against the G3 outputs")
    a("")
    a("Generated by `Tools/scripts/reset_status2.py --write` (G3-21b). This is the refresh of")
    a("`Research/RESET_STATUS.md` (G3-21, 12:26 UTC): same rule, but every `G3-*.md` in")
    a("`tmp/freebuff/reports` is scanned — including the follow-up cards with no `GRAB_BACKLOG.md`")
    a("row — and each item now names the **newest card it cites**. `--check` recomputes that card")
    a("from the reports' mtimes and fails if an item cites anything older.")
    a("")
    a("| item | verdict | newest cited card | core cards | question |")
    a("|---|---|---|---|---|")
    for it in doc["items"]:
        a("| **%s** | **%s** | `%s` (%s) | %s | %s |" % (
            it["id"], it["verdict"], it["newest_actual"], it["newest_mtime"],
            ", ".join("`%s`" % c["id"] for c in it["core"]), it["question"]))
    a("")
    a("Totals: **%d RESOLVED, %d PARTIAL, %d OPEN** of %d items." % (
        counts["RESOLVED"], counts["PARTIAL"], counts["OPEN"], len(doc["items"])))
    a("")
    a("## What changed since `RESET_STATUS.md`")
    a("")
    a("`RESET_STATUS.md` was written at %s. These cited reports are newer than it and are the"
      % (doc["prev_mtime"] or "an unknown time"))
    a("reason each item's *What remains* differs from the earlier document:")
    a("")
    a("| report | mtime | cited by |")
    a("|---|---|---|")
    for r, t, item in doc["newer_reports"]:
        a("| `%s` | %s | %s |" % (r, t, item))
    a("")
    a("The substantive corrections, in one line each: the JC3 constraint partner is a stored")
    a("**sentinel**, not body 0, and such records are dropped at load (R-1); the eject is a script")
    a("path in `DrivingMode` with a decoded move asset (R-2); the \"15 zero constants\" become small")
    a("integers and the shader caches have no `RDEF` chunk at all (R-4); every ledger row now has")
    a("a G3 source and the 96 OPEN rows split 69/27 by provenance (R-5); the vehicle's class")
    a("defaults are decoded as values, and the last `.ddsc`/`.pfxc`/`.rbm` gaps are closed (R-6).")
    a("")
    a("### Cards under a `needs rework` review")
    a("")
    rework = [c for c in doc["cards"] if any("needs rework" in r.lower() for r in c["reviews"])]
    a("%d cards that carry a STATUS line are under `needs rework`. Their headline numbers are not"
      % len(rework))
    a("used as evidence above; where a review changes what an item can claim, that item's *What")
    a("remains* says so.")
    a("")
    a("| card | its STATUS | review |")
    a("|---|---|---|")
    for c in rework:
        a("| `%s` | %s | %s |" % (c["id"], c["status"], ", ".join(c["reviews"])))
    a("")
    a("## How a verdict is reached")
    a("")
    a("* **RESOLVED** — every core card's report says `done`, no core card is under a `needs")
    a("  rework` review, and every evidence probe holds.")
    a("* **PARTIAL** — at least one evidence probe holds, or at least one core card is")
    a("  done/partial.")
    a("* **OPEN** — neither.")
    a("")
    a("Labels: **decoded** = a value read from a named file at a named offset/export by the cited")
    a("card; **derived** = a rule over decoded values; **UNKNOWN** = not decoded, with what was")
    a("tried.")
    a("")

    for it in doc["items"]:
        a("## %s — %s" % (it["id"], it["verdict"]))
        a("")
        a("> %s" % it["question"])
        a("")
        a("**Newest cited card:** `%s` — report `%s`, mtime %s. %s."
          % (it["newest_actual"], it["newest_report"], it["newest_mtime"], it["newest_note"]))
        a("")
        a("| card | report STATUS | question |")
        a("|---|---|---|")
        for c in it["core"]:
            shown = "_no report_" if c["status"] is None else c["status"]
            if c["reviews"]:
                shown += " (review: %s)" % ", ".join(c["reviews"])
            a("| `%s` | %s | %s |" % (c["id"], shown, c["title"]))
        for c in it["supporting"]:
            shown = "_no report_" if c["status"] is None else c["status"]
            if c["reviews"]:
                shown += " (review: %s)" % ", ".join(c["reviews"])
            a("| `%s` (supporting) | %s | %s |" % (c["id"], shown, c["title"]))
        a("")
        a("### What the G3 outputs establish (decoded)")
        a("")
        for path, fact in it["facts"]:
            a("* `%s` — %s" % (path, fact))
        a("")
        a("### Evidence probes (re-run by `--check`)")
        a("")
        a("| file | fact that must still be there | result |")
        a("|---|---|---|")
        for p in it["probe_results"]:
            a("| `%s` | %s | %s %s |" % (
                p["path"], p["label"], "PASS" if p["ok"] else "**FAIL**",
                "- " + p["seen"] if p["ok"] else "- saw %s, wanted %s" % (p["seen"], p["want"])))
        a("")
        a("### What remains (does not affect the verdict)" if it["verdict"] == "RESOLVED"
          else "### What remains")
        a("")
        for r in it["remaining"]:
            a("* %s" % r)
        a("")
        a("### UNKNOWNs")
        a("")
        for u in it["unknowns"]:
            a("* %s" % u)
        a("")

    a("## Card census — the Phase G3 table, with what exists now")
    a("")
    a("| card | size | serves | report | STATUS | review | newest report |")
    a("|---|---|---|---|---|---|---|")
    for c in doc["cards"]:
        a("| `%s` | %s | %s | %s | %s | %s | %s |" % (
            c["id"], c["size"], c["serves"] or "—",
            ", ".join("`%s`" % r for r in c["reports"]) or "—",
            "_no report_" if c["status"] is None else c["status"],
            ", ".join(c["reviews"]) or "—",
            "%s (%s)" % (c["newest_report"], c["newest_mtime"]) if c["newest_report"] else "—"))
    a("")
    a("Follow-up cards with no `GRAB_BACKLOG.md` row, cited above where they matter: %s."
      % ", ".join("`%s`" % r for r in doc["extra_reports"]))
    a("")
    a("## UNKNOWNs of this document")
    a("")
    a("* **Cards without a report** — their status here is inferred from the outputs they name,")
    a("  not from a declared `STATUS:` line; the census shows `_no report_` for each.")
    a("* **The runtime sample logs' provenance** — `Research/BatmobileGrab/runtime/*.jsonl` exist")
    a("  and are consumed by `G3-01e`, but no G3 document describes how the sampler was built or")
    a("  what else it records.")
    a("* **Card STATUS vs review verdict** — reviews are quoted, not re-run;")
    a("  `tmp/freebuff/reports/review-G3-*.md` is the authority.")
    a("* **`RESET_FINDINGS.md` §2/§3/§4/§5** are not R-items and are not re-checked here.")
    a("* **Newest-card rule** — \"newest\" is the newest report *mtime* among the cards an item")
    a("  cites. It proves the item is not citing older work; it does not prove the newest card is")
    a("  the most relevant one. The relevance judgement is the `newest_note` line per item.")
    a("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)

    if a.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        counts = {}
        for it in doc["items"]:
            counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
        print("wrote Research/RESET_STATUS2.md")
        print("  items: %s" % ", ".join("%s %s" % (it["id"], it["verdict"])
                                        for it in doc["items"]))
        print("  newest cited card: %s" % ", ".join("%s %s" % (it["id"], it["newest_actual"])
                                                    for it in doc["items"]))
        print("  reports scanned: %d (G3-*.md, excluding this card's own)" % doc["report_count"])
        print("  bytes covered: %d, newer than RESET_STATUS.md: %d"
              % (len(md), len(doc["newer_reports"])))
        print("  verdicts: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())))
        stale = [it["id"] for it in doc["items"] if it["newest"] != it["newest_actual"]]
        if stale:
            print("  NEWEST MISMATCH: %s" % ", ".join(stale))
            return 1
        return 0

    fails = []
    if not os.path.exists(OUT):
        fails.append("Research/RESET_STATUS2.md missing - run --write first")
    elif read(OUT) != md:
        fails.append("Research/RESET_STATUS2.md is stale")
    for it in doc["items"]:
        if it["newest"] != it["newest_actual"]:
            fails.append("%s declares newest %s but actually cites %s"
                         % (it["id"], it["newest"], it["newest_actual"]))
        for p in it["probe_results"]:
            if not p["ok"]:
                fails.append("%s probe FAILED: %s (%s)" % (it["id"], p["path"], p["seen"]))
    counts = {}
    for it in doc["items"]:
        counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d items (%s), newest cards %s, %d reports scanned, md byte-identical" % (
        len(doc["items"]), ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
        "/".join(it["newest_actual"] for it in doc["items"]), doc["report_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
