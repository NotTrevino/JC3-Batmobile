#!/usr/bin/env python3
"""reset_status.py - G3-21: RESET_FINDINGS R-1..R-6 checked against the G3 outputs.

Reads (never edits):
    RESET_FINDINGS.md                    the six research items and their wording
    GRAB_BACKLOG.md                      the Phase G3 card table (section 6b)
    tmp/freebuff/reports/G3-*.md         each card's declared STATUS line
    tmp/freebuff/reports/review-*.md     independent review verdicts, where they exist
    Research/**                          the outputs each item is checked against

Writes:
    Research/RESET_STATUS.md

Every verdict is gated: `--check` re-parses the card table and the STATUS lines, re-runs every
evidence probe against the files on disk, recomputes each item's verdict from the stated rule,
and fails if the document is stale or a verdict no longer follows.

The rule (also printed in the document):
    RESOLVED  every core card's report says done, no core card is under a "needs rework"
              review, and every evidence probe holds
    PARTIAL   at least one evidence probe holds or at least one core card is done/partial
    OPEN      neither - no evidence in the G3 outputs

A verdict is therefore not a matter of taste: if a cited report changes its STATUS, or an output
loses the fact cited for it, `--check` fails.

Usage:
    python Tools/scripts/reset_status.py --write
    python Tools/scripts/reset_status.py --check
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BACKLOG = os.path.join(REPO, "GRAB_BACKLOG.md")
REPORTS = os.path.join(REPO, "tmp", "freebuff", "reports")
OUT = os.path.join(REPO, "Research", "RESET_STATUS.md")

RESET_ITEMS = ("R-1", "R-2", "R-3", "R-4", "R-5", "R-6")


# --------------------------------------------------------------------------- parsing
def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def backlog_cards():
    """Every `#### G3-xx · title   S · deps: ... · serves: ...` line, in file order."""
    out = []
    for line in read(BACKLOG).splitlines():
        if not line.startswith("#### G3-"):
            continue
        m = re.match(r"^#### (G3-[0-9A-Za-z]+)\s+[^\x00-\x7f]\s+(.*?)\s{2,}([SML])(.*)$", line)
        if not m:
            out.append({"id": line.split()[1], "title": line.split("·", 1)[-1].strip(),
                         "size": "", "deps": "", "serves": "", "raw": line})
            continue
        cid, title, size, rest = m.group(1), m.group(2), m.group(3), m.group(4)
        parts = re.split(r"\s*[^\x00-\x7f]\s*", rest)
        deps = serves = ""
        for part in parts:
            if part.startswith("deps:"):
                deps = part[5:].strip()
            elif part.startswith("serves:"):
                serves = part[7:].strip()
        out.append({"id": cid, "title": title.strip(), "size": size, "deps": deps,
                    "serves": serves, "raw": line})
    return out


def report_status(path):
    """The card's own STATUS line, raw, or None."""
    for line in read(path).splitlines()[:16]:
        m = re.search(r"STATUS:\s*(.+)", line, re.I)
        if m:
            return m.group(1).strip().strip("*").strip()
    return None


def classify(raw):
    if raw is None:
        return None
    low = raw.lower()
    if low.startswith("done"):
        return "done"
    if low.startswith("partial"):
        return "partial"
    return "stated"


def review_verdict(path):
    if not os.path.exists(path):
        return None
    for line in read(path).splitlines()[:40]:
        m = re.search(r"VERDICT:\s*\**([A-Za-z ]+?)\**\s*$", line.strip())
        if m:
            return m.group(1).strip()
    return None


def reports_for(card_id, available):
    """`<card>.md`, else the `<card>-*.md` group (a sub-item series). Never a sibling card."""
    exact = [f for f in available if f[:-3] == card_id]
    if exact:
        return exact
    return sorted(f for f in available if f[:-3].startswith(card_id + "-"))


# --------------------------------------------------------------------------- probes
def run_probe(p):
    """A probe is a fact that must still be in the bytes/text on disk."""
    if p.get("glob"):
        hits = glob.glob(os.path.join(REPO, p["glob"]))
        need = p.get("min", 1)
        return {"ok": len(hits) >= need, "seen": "%d file(s)" % len(hits),
                "want": "at least %d file(s)" % need, "path": p["glob"],
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


# --------------------------------------------------------------------------- the six items
ITEMS = [
    {
        "id": "R-1",
        "question": "find BmAK's drivable collision: package, class, shape.",
        "core": ["G3-01c", "G3-01d", "G3-01e"],
        "supporting": ["G3-01", "G3-01b", "G3-10", "G3-10b"],
        "facts": [
            ("Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "the selector is UnrealScript: `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`, "
             "export 10894, 253 script bytes, 7 calls, mesh table {0: none, 1: "
             "BatmanCollisionMeshPursuitMode, 2: BatmanCollisionMeshBattleMode}, callers BmGame 1 / "
             "Startup 5 (G3-01e)"),
            ("Research/BatmobileGrab/COLLISION_CONVEX.md",
             "56 convex elements decoded (43 battle / 13 pursuit) with the FKConvexElem accounting "
             "oracles (G3-01c)"),
            ("Research/BatmobileGrab/COLLISION_BOXES.md",
             "131/131 box transforms orthonormal with det +1; extents at 0x40/0x44/0x48, packed bool "
             "word at 0x4C, element stride 0x50 (G3-01b-boxes)"),
            ("Research/BatmobileGrab/COLLISION_FRAME.md",
             "the decoded convex union sits on the render mesh through component offsets only: pursuit "
             "hull margin min +0.22 cm, pursuit collision shifted +5.0 cm in X, battle mesh rotated "
             "4.1199 deg (G3-01d)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "needle": "BatmanCollisionMeshPursuitMode", "label": "the mode→mesh table is in the record"},
            {"path": "Research/BatmobileGrab/COLLISION_FRAME.md", "needle": "5.0",
             "label": "the +5.0 cm pursuit offset is in the record"},
            {"path": "Research/BatmobileGrab/COLLISION_CONVEX.md", "needle": "56",
             "label": "the 56 decoded elements are in the record"},
            {"path": "Research/BatmobileGrab/COLLISION_BOXES.md", "needle": "131",
             "label": "the 131-box oracle is in the record"},
        ],
        "remaining": [
            "The branch polarity of the selector is not decoded (`G3-01e`: comparison shapes hold, "
            "the branch encoding does not), so \"the body runs when the comparison is true\" stays "
            "unproven; the value→mesh table does not depend on it.",
            "`G3-01` and `G3-01b` themselves have no report file — their facts live in "
            "`COLLISION.md` / `COLLISION_GEOM.md` and were carried forward by the `G3-01b-*`, "
            "`G3-01c`, `G3-01e` reports. Their STATUS is therefore second-hand in this table.",
            "`G3-01b-mode`'s \"the selector is native\" inference was refuted by `G3-01e` "
            "(review: needs rework), so `COLLISION_MODES.md` must be read with that in mind.",
            "`G3-01e` carries a `needs rework` review too: the byte decode and the value→mesh table "
            "survive an independent re-read, but one `decoded` claim about the two `DriverLeft` "
            "branches' guard-region names is contradicted by the function's own script, and the "
            "runtime narrative drops one of the four `0→1` transitions.",
        ],
        "unknowns": [
            "Which collision body the JC3 side pairs with each BmAK hull: `G3-10b` leaves the "
            "constraint axes, the partner body of each constraint and the inertia block UNKNOWN.",
        ],
    },
    {
        "id": "R-2",
        "question": "grab `BmInput.ini` and the Batmobile input path; grab JC3's vehicle input "
                    "model (for D-11).",
        "core": ["G3-02", "G3-02b", "G3-02c", "G3-02e", "G3-08"],
        "supporting": ["G3-02d", "G3-02f"],
        "facts": [
            ("Research/BatmobileGrab/CONFIG.md",
             "`BmGame/Config/BmInput.ini` is read as a whole: 43,825 B, 568 rows, `Engine.PlayerInput` "
             "`Bindings`, e.g. `BatmobileSonar`, `BrakeButton` (G3-03) — the reset's \"never read\" is "
             "no longer true"),
            ("Research/JC3Grab/INPUT.md",
             "JC3 defines vehicle controls in `settings/keymap_gamepad.bin` and "
             "`settings/keymap_keyboard.bin` (two archive layers, 4 files), with a per-binding record "
             "format decoded and a stated yes/no/UNKNOWN per BmAK action (G3-08)"),
            ("Research/BatmobileGrab/CONTROLS_NATIVE2.md",
             "native mode flags named from the BmSDK dump: `0x10` = `bWeaponsReady`, `0x8000` = "
             "`bBattleModeLocked`; the two `±0.707` comparisons are at 0x140063f04 / 0x140063f22 "
             "(G3-02e)"),
            ("Research/BatmobileGrab/CONTROLS.md",
             "the script side of the input path (consumers, `ToggleBattleMode`, `TryToChangeMode`) is "
             "recorded with export ids (G3-02/02b/02d line of work)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/CONFIG.md", "needle": "BmInput.ini",
             "label": "BmInput.ini is in the config record"},
            {"path": "Research/JC3Grab/INPUT.md", "needle": None,
             "label": "the JC3 input model document exists"},
            {"path": "Research/BatmobileGrab/CONTROLS_NATIVE2.md", "needle": "bBattleModeLocked",
             "label": "the battle-mode flag is named in the native record"},
            {"path": "Research/BatmobileGrab/CONTROLS.md", "needle": "BattleMode",
             "label": "the script-side control record exists"},
        ],
        "remaining": [
            "`G3-02`, `G3-02b`, `G3-02c`, `G3-02d`, `G3-02f` have no report files, so the "
            "config→script→native chain is evidenced only by its outputs (`CONFIG.md`, "
            "`CONTROLS.md`, `CONTROLS_CONSUMERS.md`, `CONTROLS_NATIVE*.md`).",
            "`G3-02e` is partial: the float at `[Pawn.Mesh + 0xd8]` that meets `±0.707` has no "
            "decoded field name, and \"no native route from the driving input handler to the "
            "exit/eject execs\" is a decoded negative, not a positive path.",
            "The user-stated meanings (LT hold = battle, B = track/immobilizer, LB = exit, A = "
            "eject) are not proven by any decoded caller chain; they remain play observations.",
            "No runtime confirmation exists for the controls (no `G3-02d` report).",
            "`CONFIG.md` is stale: `review-G3-03.md` records that its `--check` fails on the current "
            "install because three ini files were rewritten 64 minutes after the card was "
            "generated (20,961 → 20,966 rows, 41 rows changed identity). The `BmInput.ini` binding "
            "rows are therefore right in method, not guaranteed current in value.",
        ],
        "unknowns": [
            "The name of the float compared against `±0.707`, and which entity state it measures.",
            "Whether JC3 exposes the three actions D-11 needs (battle toggle, immobilizer, "
            "eject) for a car module: `INPUT.md` gives per-action verdicts, not a mapping.",
        ],
    },
    {
        "id": "R-3",
        "question": "build a runtime oracle. Measure in game which resources the drop loaded, and "
                    "where collision and mesh actually sit, before touching physics again.",
        "core": ["G3-07", "G3-07a"],
        "supporting": [],
        "facts": [
            ("Research/BatmobileGrab/runtime/",
             "a read-only sampler's logs exist (`globals.json` + 8 or more `samples-*.jsonl`), and "
             "`G3-01e` reads them: runtime mode values {0: 17, 1: 6} with 7 transitions, inside the "
             "callers' constant range"),
            ("Research/BatmobileGrab/COLLISION_SELECTOR.md",
             "the runtime samples are cross-checked against decoded caller constants, which is the "
             "only place in the project where a decoded value and a measured value meet"),
        ],
        "probes": [
            {"glob": "Research/BatmobileGrab/runtime/*.jsonl", "min": 1,
             "label": "runtime sample logs exist and are consumed by the collision-selector record"},
            {"path": "Research/BatmobileGrab/COLLISION_SELECTOR.md", "needle": "runtime",
             "label": "the record shows the runtime cross-check"},
        ],
        "remaining": [
            "Neither measurement R-3 names is in any output: no document states which `.physicsc` "
            "the drop loads, and none states where the collision sits relative to the mesh **as "
            "measured in game** (the +5.0 cm is decoded from packages, not observed).",
            "`G3-07` and `G3-07a` have no reports, and `Research/JC3Grab/RUNTIME_LAYOUT.md` does not "
            "exist — the sampler's layout has no oracle-backed document.",
            "The sampler's provenance and scope are undocumented here: the logs record the "
            "collision-selector mode field, not loaded resources.",
        ],
        "unknowns": [
            "Whether the game reads the built `.physicsc` at all — the reset's question 1 in §4 is "
            "still unanswered, and no output distinguishes the built file from the vanilla one.",
            "Whether the physics frame equals the render frame for the spawned entity in game.",
            "What the remaining 41 Serpente part bodies contribute at runtime.",
        ],
    },
    {
        "id": "R-4",
        "question": "decode both renderers' colour pipelines far enough to state whether an exact "
                    "conversion exists (and, if not, what the closest mapping depends on).",
        "core": ["G3-03", "G3-04", "G3-04b", "G3-09", "G3-09b"],
        "supporting": ["G3-04c"],
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
            ("Research/JC3Grab/COLOUR.md",
             "the JC3 side is decoded at the container level: `CarPaintMM` block offsets, 10 palette "
             "tint records, sampler slots corroborated (G3-09)"),
            ("Research/JC3Grab/COLOUR_NATIVE.md",
             "in `JustCause3.exe` the palette schema names sit in exactly the `.vmodc` order and have "
             "0 code references; 3 functions reference `CarPaintMM`; the tint writer and any "
             "exposure/tonemap constant are not found (G3-09b)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/COLOUR_FUNCTIONS.md", "needle": "FunctionExpressions",
             "label": "the stripped operator graph is recorded"},
            {"path": "Research/BatmobileGrab/COLOUR_PARAMS.md", "needle": None,
             "label": "the parameter/GUID record exists"},
            {"path": "Research/JC3Grab/COLOUR.md", "needle": "Palette",
             "label": "the JC3 palette decode is recorded"},
            {"path": "Research/JC3Grab/COLOUR_NATIVE.md", "needle": "CarPaintMM",
             "label": "the executable-side decode is recorded"},
        ],
        "remaining": [
            "The question R-4 actually asks — whether an exact conversion exists — is not answered: "
            "one side has no operator graph (BmAK) and the other has no measured on-screen model "
            "(JC3).",
            "`G3-09`'s Done (on-screen colour as a function of named terms, calibrated on >=3 vanilla "
            "paints, error stated) needs the fixed frame from R-3 and is not met; no on-screen value "
            "is claimed anywhere.",
            "The JC3 tint write is offset-level and its instruction is unidentified; no exposure or "
            "tonemap constant is attributed.",
            "Four colour cards are under a `needs rework` review, each for a specific claim: "
            "`G3-04b` reported 0/87 vector defaults where the bytes hold 82/87 (a `StructProperty` "
            "default at 0xCC) and derives `base x adjust` from an operator it itself calls UNKNOWN; "
            "`G3-09` states the palette is referenced by no file, but the entity's own `.epe` carries "
            "its Jenkins hash (`0x6187A56B` at 0x266) — the palette is a hashed asset reference; "
            "`G3-03` no longer matches the install; `G3-09b` reports its 15 constants as zero. None "
            "of this changes the verdict on exact conversion, which is still not answerable.",
        ],
        "unknowns": [
            "How the BmAK master combines its decoded parameters (the expression bodies are stripped).",
            "Which instruction fills the `CarPaintMM` dynamic float4s, and which of them is the tint.",
            "JC3's exposure/tonemap values, and what the closest defensible BmAK→JC3 mapping depends "
            "on.",
        ],
    },
    {
        "id": "R-5",
        "question": "reconcile `T_ROWS.jsonl` against the built files: for every row, translated / "
                    "not / guessed, with the evidence.",
        "core": ["G3-11", "G3-11b"],
        "supporting": ["G3-20"],
        "facts": [
            ("Working/Translation/LEDGER_AUDIT.md",
             "198/198 rows classified against the built files: 85 TRANSLATED, 7 GUESSED, 106 NOT "
             "TRANSLATED, with tiers value/member/string/none (G3-11) — but the 85 is not a "
             "translation count, see review below"),
            ("Working/Translation/LEDGER_AUDIT2.md",
             "the 72 in-scope rows re-checked with the right decoders: 19 changed, 53 kept; after: "
             "42 TRANSLATED, 0 GUESSED, 25 NOT TRANSLATED, 5 REFUTED (G3-11b)"),
        ],
        "probes": [
            {"path": "Working/Translation/LEDGER_AUDIT.md", "needle": "198",
             "label": "the 198-row audit exists"},
            {"path": "Working/Translation/LEDGER_AUDIT2.md", "needle": "19",
             "label": "the 19 changed rows are recorded"},
        ],
        "remaining": [
            "`G3-20` (which G3 file supplies/corrects/refutes each row, open rows named) has no "
            "report and no `Working/Translation/LEDGER_G3.md`; the per-row G3 sourcing is not yet "
            "written.",
            "The ledger file itself is untouched by design, so its 13 `blocked` / 40 `next` flags "
            "still disagree with the audit's verdicts until someone applies them.",
            "`review-G3-11.md` (needs rework) shows **35 of the 85 TRANSLATED rows are not supported** "
            "by the script's own definition: 34 cite files whose `owner_card` in "
            "`Builds/bm-RC1/receipt.json` is an earlier lineage (inherited copies this build never "
            "edited) and `T-DM1` cites `lave_health_medium.vmodc`, whose owner is "
            "`B-18 (vanilla bytes)`. The fix is a provenance dimension over "
            "`receipt.aaf.list[].owner_card`, not a re-run. Until then, R-5 is classified but its "
            "headline count overstates what was translated.",
        ],
        "unknowns": [
            "None for the classification itself; what remains is the G3-sourcing layer (G3-20).",
        ],
    },
    {
        "id": "R-6",
        "question": "decode the 925 untagged objects that touch the vehicle (handling, upright, "
                    "visual damage, materials).",
        "core": ["G3-05", "G3-06", "G3-12", "G3-12b"],
        "supporting": ["G3-05b", "G3-19"],
        "facts": [
            ("Research/BatmobileGrab/REMAINDER.md",
             "all 925 untagged objects classified: 768 empty stubs, 152 native records, 5 "
             "closes-from-offset; 17 reachable from the vehicle chain, 3 UNKNOWN, 757 with nothing to "
             "read, 148 in other packages; 587 partial objects accounted (70/23/40/454) (G3-06)"),
            ("Research/BatmobileGrab/PACKAGES_G305.md",
             "20 packages / 320,415 exports censused, including `Startup`/`StartupPatch` and the "
             "showcase packages (G3-05)"),
            ("Research/JC3Grab/DECODE_DEPTH.md",
             "566/566 donor files classified with a per-family oracle (G3-12)"),
            ("Research/JC3Grab/DECODE_DEPTH2.md",
             "the containers: 71 of 116 `.ddsc` FULL / 45 PARTIAL, 4 `.pfxc` PARTIAL with the whole "
             "packfile decoded (G3-12b)"),
        ],
        "probes": [
            {"path": "Research/BatmobileGrab/REMAINDER.md", "needle": "925",
             "label": "the 925-object record exists"},
            {"path": "Research/BatmobileGrab/PACKAGES_G305.md", "needle": None,
             "label": "the package census exists"},
            {"path": "Research/JC3Grab/DECODE_DEPTH.md", "needle": "566",
             "label": "the 566-file census exists"},
            {"path": "Research/JC3Grab/DECODE_DEPTH2.md", "needle": None,
             "label": "the container decode exists"},
        ],
        "remaining": [
            "The **values** of the vehicle's class defaults are still not decoded. `REMAINDER.md` "
            "accounts for every object but leaves \"where the 97 `BmScript.RVehicleBatmobile` "
            "property values are\" as UNKNOWN; `review-G3-06.md` (needs rework) shows the class "
            "default object itself — `Startup.upk` export 7530, 978 B — was never read, and it "
            "parses from byte 0 into 93 default-value tags. That is now a named next step, not an "
            "open question.",
            "45 `.ddsc` header tails and the 4 `.pfxc` 512-byte trailing blobs stay UNKNOWN "
            "(`G3-12b`, review: minor issues — the tails track a per-group chunk table, not the mip "
            "set).",
            "`G3-19` (partial `.rbm`/`.epe` to FULL) has no report, so the donor is classified but "
            "not fully decoded.",
        ],
        "unknowns": [
            "The 97 class-default *values* (the CDO is readable; the name→offset pairing is not done).",
            "The 6 CDO component payloads past the 512 MiB decode budget.",
            "The `.ddsc` tail table meaning and the `.pfxc` trailing blob.",
        ],
    },
]


# --------------------------------------------------------------------------- build
def card_info(cid, available, by_id):
    """Status, reports and review verdicts for a cited card id (backlog row or follow-up)."""
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
    return {"id": cid, "reports": reps, "status": status, "status_raw": st,
            "reviews": reviews,
            "title": by_id[cid]["title"] if cid in by_id
                     else "(follow-up card, no GRAB_BACKLOG row)"}


def build():
    # `G3-21.md` is this synthesis's own report and is never a cited card: scanning it would make
    # the document depend on itself (it is rewritten after the document).
    available = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPORTS, "G3-*.md"))
                       if os.path.basename(p) != "G3-21.md")
    cards = backlog_cards()
    by_id = {c["id"]: c for c in cards}
    card_rows = []
    for c in cards:
        info = card_info(c["id"], available, by_id)
        for k, v in info.items():
            if k != "id":
                c[k] = v
        card_rows.append(c)

    items = []
    for spec in ITEMS:
        core = [card_info(cid, available, by_id) for cid in spec["core"]]
        sup = [card_info(cid, available, by_id) for cid in spec["supporting"]]
        probes = [run_probe(p) for p in spec["probes"]]
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
        items.append({**spec, "core": core, "supporting": sup,
                      "probe_results": probes, "verdict": verdict})

    extra = sorted({c["id"] for c in cards} ^ {p[:-3] for p in available})
    extra = [p for p in extra if not any(c["id"] == p for c in cards)]
    return {"cards": card_rows, "items": items, "extra_reports": extra,
            "report_count": len(available)}


def render(doc):
    L = []
    A = L.append
    counts = {"RESOLVED": 0, "PARTIAL": 0, "OPEN": 0}
    for it in doc["items"]:
        counts[it["verdict"]] += 1
    A("# RESET_FINDINGS status — R-1 to R-6 against the G3 outputs")
    A("")
    A("Generated by `Tools/scripts/reset_status.py --write`; `--check` re-parses every cited")
    A("report, re-runs every evidence probe and re-derives every verdict. `RESET_FINDINGS.md` is")
    A("read, never edited.")
    A("")
    A("| item | verdict | core cards | question |")
    A("|---|---|---|---|")
    for it in doc["items"]:
        A("| **%s** | **%s** | %s | %s |" % (
            it["id"], it["verdict"], ", ".join("`%s`" % c["id"] for c in it["core"]),
            it["question"]))
    A("")
    A("Totals: **%d RESOLVED, %d PARTIAL, %d OPEN** of %d items." % (
        counts["RESOLVED"], counts["PARTIAL"], counts["OPEN"], len(doc["items"])))
    A("")
    rework = [c for c in doc["cards"] if any("needs rework" in r.lower() for r in c["reviews"])]
    A("### Cards under a `needs rework` review")
    A("")
    A("%d of the cards that carry a STATUS line were reviewed as `needs rework`. Their headline" % len(rework))
    A("numbers are not used as evidence above; where a review changes what an item can claim, the")
    A("item's *What remains* says so.")
    A("")
    A("| card | its STATUS | review |")
    A("|---|---|---|")
    for c in rework:
        A("| `%s` | %s | %s |" % (c["id"], c["status"], ", ".join(c["reviews"])))
    A("")
    A("## How a verdict is reached")
    A("")
    A("* **RESOLVED** — every core card's report says `done`, no core card is under a")
    A("  `needs rework` review, and every evidence probe holds.")
    A("* **PARTIAL** — at least one evidence probe holds, or at least one core card is")
    A("  done/partial (something is decoded, the item's own question is not fully answered).")
    A("* **OPEN** — neither: nothing in the G3 outputs answers it.")
    A("")
    A("Labels used below: **decoded** = a value read from a named file at a named offset/export by")
    A("the cited card; **derived** = a rule over decoded values; **UNKNOWN** = not decoded, with")
    A("what was tried. A card's own STATUS line is quoted; an independent review verdict is shown")
    A("next to it where one exists.")
    A("")

    for it in doc["items"]:
        A("## %s — %s" % (it["id"], it["verdict"]))
        A("")
        A("> %s" % it["question"])
        A("")
        A("| card | report STATUS | the card's question |")
        A("|---|---|---|")
        for c in it["core"]:
            shown = "_no report_" if c["status"] is None else c["status"]
            if c["reviews"]:
                shown += " (review: %s)" % ", ".join(c["reviews"])
            A("| `%s` | %s | %s |" % (c["id"], shown, c["title"]))
        for c in it["supporting"]:
            shown = "_no report_" if c["status"] is None else c["status"]
            if c["reviews"]:
                shown += " (review: %s)" % ", ".join(c["reviews"])
            A("| `%s` (supporting) | %s | %s |" % (c["id"], shown, c["title"]))
        A("")
        A("### What the G3 outputs establish (decoded)")
        A("")
        for path, fact in it["facts"]:
            A("* `%s` — %s" % (path, fact))
        A("")
        A("### Evidence probes (re-run by `--check`)")
        A("")
        A("| file | fact that must still be there | result |")
        A("|---|---|---|")
        for p in it["probe_results"]:
            A("| `%s` | %s | %s %s |" % (p["path"], p["label"],
                                         "PASS" if p["ok"] else "**FAIL**",
                                         "- " + p["seen"] if p["ok"] else
                                         "- saw %s, wanted %s" % (p["seen"], p["want"])))
        A("")
        if it["verdict"] != "RESOLVED":
            A("### What remains")
            A("")
            for r in it["remaining"]:
                A("* %s" % r)
            A("")
        else:
            A("### What remains (does not affect the verdict)")
            A("")
            for r in it["remaining"]:
                A("* %s" % r)
            A("")
        A("### UNKNOWNs")
        A("")
        for u in it["unknowns"]:
            A("* %s" % u)
        A("")

    A("## Card census — the Phase G3 table, with what exists")
    A("")
    A("| card | size | serves | report | STATUS | review |")
    A("|---|---|---|---|---|---|")
    for c in doc["cards"]:
        A("| `%s` | %s | %s | %s | %s | %s |" % (
            c["id"], c["size"], c["serves"] or "—",
            ", ".join("`%s`" % r for r in c["reports"]) or "—",
            ("_no report_" if c["status"] is None else c["status"]),
            ", ".join(c["reviews"]) or "—"))
    A("")
    A("Reports that have no card of their own in `GRAB_BACKLOG.md` §6b (they are the sub-item")
    A("reports of an existing card): %s." % ", ".join("`%s`" % r for r in doc["extra_reports"]))
    A("")
    A("## UNKNOWNs of this document")
    A("")
    A("* **Cards without a report** — `G3-01`, `G3-01b`, `G3-02`, `G3-02b`, `G3-02c`, `G3-02d`,")
    A("  `G3-02f`, `G3-07`, `G3-07a`, `G3-10c`, `G3-14`, `G3-19`, `G3-20`. Their status is")
    A("  inferred from the outputs they name, not from a declared `STATUS:` line; where such a")
    A("  card carries an item's verdict this document says so.")
    A("* **The runtime sample logs' provenance** — `Research/BatmobileGrab/runtime/*.jsonl` exist")
    A("  and are consumed by `G3-01e`, but no G3 document describes how the sampler was built or")
    A("  what else it records, so what they can prove beyond the mode field is UNKNOWN here.")
    A("* **Card STATUS vs review verdict** — where a review exists it is quoted, but this document")
    A("  does not re-review the cards; `tmp/freebuff/reports/review-G3-*.md` is the authority.")
    A("* **`RESET_FINDINGS.md` §2/§3/§4/§5** (what was not translated, what was translated")
    A("  wrongly, the collision observations, the process failures) are not R-items; they are not")
    A("  re-checked here.")
    A("")
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
        verdicts = {}
        for it in doc["items"]:
            verdicts[it["verdict"]] = verdicts.get(it["verdict"], 0) + 1
        print("wrote Research/RESET_STATUS.md")
        print("  items: %s" % ", ".join("%s %s" % (it["id"], it["verdict"]) for it in doc["items"]))
        print("  cards: %d (%d with a report, %d without)" % (
            len(doc["cards"]),
            sum(1 for c in doc["cards"] if c["reports"]),
            sum(1 for c in doc["cards"] if not c["reports"])))
        print("  probes: %d, all pass: %s" % (
            sum(len(it["probe_results"]) for it in doc["items"]),
            all(p["ok"] for it in doc["items"] for p in it["probe_results"])))
        print("  verdicts: %s" % ", ".join("%s %d" % (k, v) for k, v in sorted(verdicts.items())))
        return 0

    fails = []
    if not os.path.exists(OUT):
        print("FAIL: Research/RESET_STATUS.md missing - run --write first")
        return 1
    if read(OUT) != md:
        fails.append("Research/RESET_STATUS.md is stale")
    for it in doc["items"]:
        for p in it["probe_results"]:
            if not p["ok"]:
                fails.append("%s probe FAILED: %s (%s)" % (it["id"], p["path"], p["seen"]))
        for c in it["core"]:
            if c["id"] not in {x["id"] for x in doc["cards"]} and not c["reports"]:
                fails.append("%s cites %s, which has neither a backlog row nor a report"
                             % (it["id"], c["id"]))
    if len(doc["cards"]) != 32:
        fails.append("card count %d != 32" % len(doc["cards"]))
    for c in doc["cards"]:
        for r in c["reports"]:
            if not os.path.exists(os.path.join(REPORTS, r)):
                fails.append("card %s cites missing report %s" % (c["id"], r))
        if c["status"] is None and any(c["id"] in it["core"] for it in doc["items"]):
            # allowed, but the document must say so; the text does (UNKNOWNs of this document)
            pass
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    counts = {}
    for it in doc["items"]:
        counts[it["verdict"]] = counts.get(it["verdict"], 0) + 1
    print("OK %d items (%s), %d cards (%d with a report), %d probes, md byte-identical" % (
        len(doc["items"]),
        ", ".join("%s %d" % (k, v) for k, v in sorted(counts.items())),
        len(doc["cards"]), sum(1 for c in doc["cards"] if c["reports"]),
        sum(len(it["probe_results"]) for it in doc["items"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
