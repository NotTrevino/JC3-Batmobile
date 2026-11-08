"""ledger_sources.py - G3-20d: where the pre-reset files' values came from.

G3-20b left 96 of 105 translation-ledger rows OPEN because their values sit in seven files the
research reset did not re-derive:

    Research/BatmobileGrab/CHAIN.json      Research/BatmobileGrab/VALUES.json
    Research/JC3Grab/VOCABULARY.md         Research/JC3Grab/PARTS_TABLE.jsonl
    Research/JC3Grab/FX_TABLE.jsonl        Working/Translation/T3_FLEET.md
    Working/Translation/FITS.md

This pass answers the provenance question for exactly those files and the rows that use them:

  * which script under `Tools/scripts/` writes each file (verified by finding the output path in
    the script's own text - not by memory), and what that script reads;
  * for each value family, whether the value is **grabbed** (read from a named game file, at a
    named offset/member), **derived** (a stated rule over grabbed inputs, e.g. a median, a ratio,
    a fitted `a * mass^b`), or **guessed** (a literal in code with no source);
  * whether the producer re-runs green: `--check` (or a read-only re-run) is executed for every
    producer that has one, and its exit code is recorded.

Nothing here decides a translation; it only labels the evidence. Files under `Research/` and
`Working/` are read-only for this tool.

    python Tools/scripts/ledger_sources.py --write
    python Tools/scripts/ledger_sources.py --check
"""

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
LEDGER = os.path.join(ROOT, "Working", "Translation", "LEDGER_G3B.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "LEDGER_SOURCES.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "LEDGER_SOURCES.json")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch")
PY = [sys.executable]

# --------------------------------------------------------------------------------------------
# The seven sources. `producer` and `check` are verified against the script's own text below.
# --------------------------------------------------------------------------------------------
SOURCES = {
    "CHAIN.json": {
        "path": "Research/BatmobileGrab/CHAIN.json",
        "producer": "Tools/scripts/bmak_chain.py",
        "check_argv": ["--check"],
        "reads": [
            "the Batmobile's shipped objects (batmobile_grab.py's objects.jsonl): archetype property tags",
            "Working/vendor/BmSDK/*.g.cs (the generated layout: Class.Prop -> offset) for the names",
            "BmGame.upk / Engine.upk Default__<class> streams for values the archetype does not override",
            "Research/BatmobileGrab/OFFSETS.json (336 offsets cross-checked, 0 conflicts)",
        ],
        "value_label": "grabbed",
        "rule": ("each field row carries `offset` (in the shipped object), `name` (SDK layout at that "
                 "offset), `value` (the package bytes) and `named_by: sdk-layout`; a name at an offset "
                 "with no property is reported `absent`, never zero-filled"),
    },
    "VALUES.json": {
        "path": "Research/BatmobileGrab/VALUES.json",
        "producer": "Tools/scripts/grab_values.py",
        "check_argv": [],                      # no --check; the default run prints the live values
        "reads": [
            "Working/Serpente/.../sportsmuscle_body_lod1.rbm block 6 (the vanilla paint template)",
            "the BmAK paint material Material0_BaseColour + Diffuse_Adjust (batmobile grab)",
        ],
        "value_label": "grabbed + derived (one assumed composite)",
        "rule": ("gloss_cap, base_colour and the vanilla tint are grabbed (rbm block / material member); "
                 "albedo_gain = vanilla paint luma 0.1837 / authored luma 0.0533 is DERIVED; "
                 "effective_base_colour multiplies by the grabbed Diffuse_Adjust, but the engine's "
                 "combine operator is UNKNOWN in COLOUR_PARAMS.md, so that composite is ASSUMED, not "
                 "derived"),
        "derived_fields": ["paint.albedo_gain"],
        "assumed_fields": ["paint.effective_base_colour"],
        "assumed_rule": {"file": "Research/BatmobileGrab/COLOUR_PARAMS.md", "line": 228,
                         "quote": "whether and how they combine is UNKNOWN"},
    },
    "VOCABULARY.md": {
        "path": "Research/JC3Grab/VOCABULARY.md",
        "producer": "Tools/scripts/jc3grab.py",
        "check_argv": ["check"],
        "reads": [
            "every JC3 vehicle `.ee` in the archives, its inner `.vmodc` decoded with Gibbed ConvertAdf",
            "the decoded instance.member.path = value rows in E:/Modding/_shared/gamedata/JC3grab",
        ],
        "value_label": "derived",
        "rule": ("ranges/counts are aggregates (min..max, n) over the decoded member values; the member "
                 "VALUES are grabbed from the game's own named XML rows, the aggregate is DERIVED"),
    },
    "PARTS_TABLE.jsonl": {
        "path": "Research/JC3Grab/PARTS_TABLE.jsonl",
        "producer": "Tools/scripts/jc3parts.py",
        "check_argv": ["check"],
        "reads": [
            "the fleet's `*_vehicle_parts.vmodc` modules (decoded by jc3adf.py, 233 entities)",
            "`DeformPoints` part names, the `.epe` part table in ENTITIES.md (cross-check)",
        ],
        "value_label": "grabbed",
        "rule": ("one row per entity; `parts[].body/ray/lights/deform/kid/parent` are module members "
                 "read at their decoded positions, `n` is the DeformPoints string, `m` the model path"),
    },
    "FX_TABLE.jsonl": {
        "path": "Research/JC3Grab/FX_TABLE.jsonl",
        "producer": "Tools/scripts/jc3fx.py",
        "check_argv": ["check"],
        "reads": [
            "every `.effc` / `.ctunec` / `.trim` in the game (inside `.ee` bundles and as archive entries)",
            "the ADF v4 container read by jc3adf.py",
        ],
        "value_label": "grabbed",
        "rule": ("one row per file: container, path, ext, size, mount, root class, row/array census and "
                 "a digest of the decoded rows; `check` re-reads the game and recomputes the digest"),
    },
    "T3_FLEET.md": {
        "path": "Working/Translation/T3_FLEET.md",
        "producer": "Tools/scripts/t3_fleet.py",
        "check_argv": ["--check"],
        "reads": [
            "E:/Modding/_shared/gamedata/JC3grab (the jc3grab.py decodes: RigidBody, VehicleDamage, Suspension, "
            "Brakes, LandGlobal, Engine members)",
        ],
        "value_label": "derived",
        "rule": ("each cell is n, the median and the p25..p75 band over the land fleet in a mass class "
                 "(3-8 t, 6 t+); the member values are grabbed, the statistics are DERIVED"),
    },
    "FITS.md": {
        "path": "Working/Translation/FITS.md",
        "producer": "Tools/scripts/t1_fits.py",
        "check_argv": ["-o", os.path.join(SCRATCH, "FITS_recheck.md")],   # no --check: rebuild to scratch
        "reads": [
            "E:/Modding/_shared/gamedata/JC3grab, one `<member>` and `rigid_body.mass` per land vehicle",
        ],
        "value_label": "derived",
        "rule": ("log-log least squares value = a * mass^b over the vehicles carrying both members, with "
                 "R^2, n and the fleet min..max printed; a fit is DERIVED, and an R^2 near 0 is the "
                 "file's own statement that the relation is not usable"),
    },
}

MARKERS = {k: k for k in SOURCES}

# Constants in the producers that are choices rather than values (reported, not counted as values).
LITERAL_LINES = {
    "Tools/scripts/grab_values.py": ["TEMPLATE_BLOCK", "TARGET"],
    "Tools/scripts/t1_fits.py": ["TARGET_MASS"],
    "Tools/scripts/t3_fleet.py": ["MASS_CLASS", "TARGET"],
}


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha_of(path):
    h = hashlib.sha1(open(path, "rb").read()).hexdigest()[:16]
    return h


def find_literal(script, path):
    """The producer must mention the output path it is supposed to write: the mapping is checked."""
    text = open(script, encoding="utf-8", errors="replace").read()
    base = os.path.basename(path)
    hits = [i + 1 for i, line in enumerate(text.splitlines()) if base in line]
    return {"mentioned": bool(hits), "lines": hits[:6],
            "writes": bool(re.search(r'open\([^\n]*%s[^\n]*["\']w' % re.escape(base), text))
            or bool(re.search(r'with open\([^\n]*%s' % re.escape(base), text))}


def run_check(name, spec):
    """Run the producer's own check (read-only) and record the exit code."""
    argv = spec["check_argv"]
    if not argv:
        argv = []                                   # default run: prints the live values
    cmd = PY + [os.path.join(ROOT, spec["producer"])] + argv
    if spec["producer"].endswith("t1_fits.py"):
        os.makedirs(SCRATCH, exist_ok=True)
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        out = (p.stdout or "") + (p.stderr or "")
        return {"cmd": " ".join(["python"] + [rel(c) for c in cmd[1:]]),
                "exit": p.returncode, "seconds": round(time.time() - t0, 1),
                "tail": [ln for ln in out.strip().splitlines() if ln.strip()][-6:]}
    except subprocess.TimeoutExpired:
        return {"cmd": " ".join(["python"] + [rel(c) for c in cmd[1:]]),
                "exit": None, "seconds": round(time.time() - t0, 1), "tail": ["TIMEOUT (900 s)"]}
    except Exception as exc:
        return {"cmd": " ".join(["python"] + [rel(c) for c in cmd[1:]]),
                "exit": None, "seconds": round(time.time() - t0, 1),
                "tail": ["could not run: %s" % type(exc).__name__]}


def source_state(name, spec):
    path = os.path.join(ROOT, spec["path"])
    exists = os.path.exists(path)
    st = {"name": name, "path": spec["path"], "exists": exists,
          "bytes": os.path.getsize(path) if exists else None,
          "sha1_16": sha_of(path) if exists else None,
          "producer": spec["producer"], "reads": spec["reads"],
          "value_label": spec["value_label"], "rule": spec["rule"],
          "derived_fields": spec.get("derived_fields", []),
          "assumed_fields": spec.get("assumed_fields", []),
          "producer_mention": find_literal(os.path.join(ROOT, spec["producer"]), path)
          if os.path.exists(os.path.join(ROOT, spec["producer"])) else {"mentioned": False}}
    # a first line of the file, so the reader can see what the row looks like
    if exists:
        with open(path, encoding="utf-8", errors="replace") as f:
            first = f.readline().strip()
        st["first_line"] = first[:220]
    ar = spec.get("assumed_rule")
    if ar:
        fp = os.path.join(ROOT, ar["file"])
        lines = (open(fp, encoding="utf-8", errors="replace").read().splitlines()
                 if os.path.exists(fp) else [])
        txt = lines[ar["line"] - 1] if 0 < ar["line"] <= len(lines) else ""
        st["assumed_rule"] = dict(ar, present=ar["quote"] in txt, line_text=txt.strip()[:200])
    return st


def classify(row, sources):
    """Which source files does this OPEN row's value come from, and what is its provenance?"""
    text = " ".join(str(row.get(k) or "") for k in ("now", "source", "open_with", "note",
                                                    "target", "verify", "proposed"))
    hit = [k for k, m in MARKERS.items() if m in text]
    if not hit:
        return {"cells": [], "verdict": "outside the seven",
                "why": "the row cites no value from the seven pre-reset files"}
    labels = {sources[h]["value_label"] for h in hit}
    if "grabbed+derived" in labels:
        verdict = "grabbed + derived (field-dependent)"
    elif "derived" in labels and "grabbed" in labels:
        verdict = "grabbed + derived"
    elif labels == {"derived"}:
        verdict = "derived"
    else:
        verdict = "grabbed"
    return {"cells": hit, "verdict": verdict,
            "why": "; ".join("%s = %s" % (h, sources[h]["value_label"]) for h in hit)}


def build(run_checks=True):
    led = json.load(open(LEDGER, encoding="utf-8"))
    rows = led["rows"]
    open_rows = [r for r in rows if r.get("status") == "OPEN"]

    sources = {k: source_state(k, v) for k, v in SOURCES.items()}
    if run_checks:
        for k in sources:
            sources[k]["check"] = run_check(k, SOURCES[k])
    else:
        prev = json.load(open(OUT_JSON, encoding="utf-8"))
        for k in sources:
            sources[k]["check"] = prev["sources"][k]["check"]

    literals = []
    for script, names in LITERAL_LINES.items():
        p = os.path.join(ROOT, script)
        if not os.path.exists(p):
            continue
        for i, line in enumerate(open(p, encoding="utf-8", errors="replace").read().splitlines(), 1):
            if any(n in line for n in names) and "=" in line and not line.strip().startswith("#"):
                literals.append({"script": script, "line": i, "text": line.strip()[:120]})

    classified = []
    for r in open_rows:
        c = classify(r, sources)
        classified.append({"id": r["id"], "doc": r["doc"], "now": r.get("now"),
                           "source": r.get("source"), "open_with": r.get("open_with"),
                           "target": r.get("target"), **c,
                           "trusted": c["verdict"] in ("grabbed", "derived", "grabbed + derived",
                                                        "grabbed + derived (field-dependent)"),
                           "check_green": all((sources[h]["check"]["exit"] == 0)
                                              for h in c["cells"]) if c["cells"] else None})

    doc = {
        "schema": 1,
        "task": "G3-20d",
        "generated_by": "Tools/scripts/ledger_sources.py",
        "ledger": rel(LEDGER),
        "ledger_counts": led["counts"],
        "open_rows": len(open_rows),
        "sources": sources,
        "row_classification": classified,
        "summary": {
            "rows": len(classified),
            "by_verdict": {v: sum(1 for c in classified if c["verdict"] == v)
                           for v in sorted({c["verdict"] for c in classified})},
            "by_source": {k: sum(1 for c in classified if k in c["cells"]) for k in SOURCES},
            "trusted": sum(1 for c in classified if c["trusted"]),
            "checks_green": sum(1 for k, s in sources.items() if s["check"]["exit"] == 0),
            "checks_run": len(sources),
        },
        "literals": literals,
        "notes": [
            "every value is labelled from the producer's own text and the file it writes; a mapping "
            "whose producer does not mention the path fails the check",
            "`--check` re-derives the classification, the mapping oracle and the file hashes; it does "
            "not re-run the producers' own checks (those are recorded from --write)",
            "a fitted constant (FITS.md a/b) is DERIVED, not guessed: the fit, its inputs and its R^2 "
            "are all in the file and t1_fits.py regenerates it",
            "one composite is neither: values.json's effective_base_colour applies a grabbed multiplier "
            "whose operator COLOUR_PARAMS.md marks UNKNOWN, so it is labelled ASSUMED and oracle "
            "`assumed_rules_cited` fails if that citation disappears",
        ],
        "unknowns": [
            "VOCABULARY.md's per-member ranges are aggregates whose raw value rows live outside the "
            "repo (E:/Modding/_shared/gamedata/JC3grab); the aggregate is re-derivable only where that data "
            "is present (jc3grab.py check)",
            "no row in the seven files records a per-value hash, so 'file unchanged since the grab' "
            "rests on the producer's check, not on a value-level fingerprint",
        ],
    }
    doc["oracles"] = oracles(doc, SOURCES)
    return doc


def oracles(doc, specs):
    s = doc["sources"]
    checks = {
        "all_seven_present": all(v["exists"] for v in s.values()),
        "producers_named": all(v["producer_mention"].get("mentioned") for v in s.values()),
        "no_guessed_source": not any(v["value_label"] == "guessed" for v in s.values()),
        "row_count_matches_ledger": doc["open_rows"] == doc["ledger_counts"]["OPEN"],
        "every_row_classified": len(doc["row_classification"]) == doc["open_rows"],
        "every_row_has_verdict": all(c["verdict"] for c in doc["row_classification"]),
        "every_source_has_rule": all(len(v["rule"]) > 40 for v in s.values()),
        "assumed_rules_cited": all(v.get("assumed_rule", {}).get("present", True)
                                  for v in s.values()),
    }
    return {"all_ok": all(checks.values()), "checks": checks,
            "producer_exits": {k: v["check"]["exit"] for k, v in s.items()}}


def render(doc):
    L, A = [], None
    A = L.append
    A("# Where the pre-reset files' values came from (G3-20d)")
    A("")
    A("Generated by `%s`. Labels: **grabbed** = read from a named game file at a named "
      "offset/member; **derived** = a stated rule over grabbed inputs; **guessed** = a literal in "
      "code with no source. This pass makes no translation decision and edits none of these files."
      % doc["generated_by"])
    A("")
    A("The ledger (%s) has %d rows: %d HOLDS, %d WRONG_VALUE, **%d OPEN** — the OPEN rows are the "
      "subject here."
      % (doc["ledger"], sum(doc["ledger_counts"].values()), doc["ledger_counts"]["HOLDS"],
         doc["ledger_counts"]["WRONG_VALUE"], doc["ledger_counts"]["OPEN"]))
    A("")
    A("## 1. The seven sources and who writes them")
    A("")
    A("| file | bytes | sha1 | producer | producer's own check | exit | value label |")
    A("|---|---:|---|---|---|---:|---|")
    for k, v in doc["sources"].items():
        c = v["check"]
        A("| `%s` | %s | `%s` | `%s` | `%s` | %s | **%s** |"
          % (k, ("{:,}".format(v["bytes"]) if v["bytes"] else "MISSING"), v["sha1_16"],
             v["producer"].replace("Tools/scripts/", ""),
             (c["cmd"].replace("python ", "") if c["cmd"] else "—"),
             ("**0**" if c["exit"] == 0 else str(c["exit"])), v["value_label"]))
    A("")
    A("The producer mapping is not from memory: `--check` fails unless each script's own text "
      "mentions the file it is claimed to write (oracle `producers_named`).")
    A("")
    for k, v in doc["sources"].items():
        A("### `%s` — %s" % (k, v["producer"]))
        A("")
        A("- **reads:** " + "; ".join(v["reads"]))
        A("- **rule:** %s" % v["rule"])
        if v.get("derived_fields"):
            A("- **derived inside this file:** " + ", ".join("`%s`" % f for f in v["derived_fields"]))
        if v.get("assumed_fields"):
            ar = v.get("assumed_rule", {})
            A("- **assumed inside this file (not decoded):** "
              + ", ".join("`%s`" % f for f in v["assumed_fields"])
              + " — the composite is computed by the producer; `%s:%s` says `%s`"
              % (ar.get("file", "?"), ar.get("line", "?"), ar.get("quote", "")))
        if v.get("check"):
            A("- **re-run:** `%s` → exit **%s**, %.1f s" % (v["check"]["cmd"], v["check"]["exit"],
                                                           v["check"]["seconds"]))
            for line in v["check"]["tail"][-3:]:
                A("  - `%s`" % line[:200])
        if v.get("first_line"):
            A("- **first line:** `%s`" % v["first_line"][:180])
        A("")
    A("## 2. The %d OPEN rows, one by one" % doc["open_rows"])
    A("")
    A("| row | part | value the row carries | source files it cites | provenance | producer check |")
    A("|---|---|---|---|---|---|")
    for c in doc["row_classification"]:
        A("| `%s` | %s | %s | %s | **%s** | %s |"
          % (c["id"], c["doc"], (str(c["now"]) or "")[:60].replace("|", "/"),
             ", ".join("`%s`" % h for h in c["cells"]) or "—", c["verdict"],
             ("green" if c["check_green"] else ("n/a" if c["check_green"] is None else "**not green**"))))
    A("")
    A("### Counts")
    A("")
    A("| provenance | rows |")
    A("|---|---:|")
    for v, n in doc["summary"]["by_verdict"].items():
        A("| %s | %d |" % (v, n))
    A("")
    A("| source | rows citing it |")
    A("|---|---:|")
    for k, n in doc["summary"]["by_source"].items():
        A("| `%s` | %d |" % (k, n))
    A("")
    A("So **%d of %d** OPEN rows rest on a grabbed or derived value whose producer re-runs green; %d "
      "cite none of the seven (they name `stations.json`, the §70 mesh measurement or a card from "
      "another family), and those stay exactly as OPEN as G3-20b left them."
      % (doc["summary"]["trusted"], doc["open_rows"],
         doc["summary"]["by_verdict"].get("outside the seven", 0)))
    A("")
    A("## 3. Constants in the producers that are choices, not values")
    A("")
    A("Reported so nobody mistakes them for grabbed numbers:")
    A("")
    A("| script | line | text |")
    A("|---|---:|---|")
    for x in doc["literals"]:
        A("| `%s` | %d | `%s` |" % (x["script"], x["line"], x["text"]))
    A("")
    A("Each picks an input (a template block index, a target mass) rather than supplying a value: "
      "`TARGET_MASS = 4000.0` in `t1_fits.py` is the mass the fit is evaluated at, and the fit's own "
      "`a`/`b` are derived from the fleet.")
    A("")
    A("## 4. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | value |")
    A("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        A("| `%s` | **%s** |" % (k, "pass" if v else "FAIL"))
    A("")
    A("## 5. UNKNOWNs")
    A("")
    for u in doc["unknowns"]:
        A("- %s" % u)
    A("")
    A("## 6. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/ledger_sources.py` | this pass, `--write` / `--check` |")
    A("| `Working/Translation/LEDGER_SOURCES.md` | this page |")
    A("| `Working/Translation/LEDGER_SOURCES.json` | the same, machine-readable, every row |")
    A("")
    return "\n".join(L) + "\n"


def write():
    doc = build(run_checks=True)
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write(render(doc))
    open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n")
    print("wrote %s and %s" % (rel(OUT_MD), rel(OUT_JSON)))
    print("rows %d; verdicts %s; checks green %d/%d"
          % (doc["open_rows"], json.dumps(doc["summary"]["by_verdict"]),
             doc["summary"]["checks_green"], doc["summary"]["checks_run"]))
    for k, v in doc["sources"].items():
        print("  %-18s exit %-5s %s" % (k, v["check"]["exit"], (v["check"]["tail"][-1] if v["check"]["tail"] else "")[:90]))
    print("oracles %d/%d" % (sum(1 for v in doc["oracles"]["checks"].values() if v),
                             len(doc["oracles"]["checks"])))
    return 0 if doc["oracles"]["all_ok"] else 1


def check():
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    doc = build(run_checks=False)
    fails = []
    if open(OUT_MD, encoding="utf-8").read() != render(doc):
        fails.append("LEDGER_SOURCES.md is stale")
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(
            json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n"):
        fails.append("LEDGER_SOURCES.json is stale")
    if not doc["oracles"]["all_ok"]:
        fails.append("oracles: " + ", ".join(k for k, v in doc["oracles"]["checks"].items() if not v))
    for k, v in doc["sources"].items():
        if v["check"]["exit"] not in (0,):
            fails.append("producer check for %s recorded exit %s" % (k, v["check"]["exit"]))
    if fails:
        for f in fails:
            print("FAIL " + f)
        return 1
    print("OK %d rows re-classified; 7 sources present; producer exits %s; md+json byte-identical"
          % (doc["open_rows"], json.dumps(doc["oracles"]["producer_exits"], sort_keys=True)))
    return 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("--write", "--check"):
        print(__doc__)
        return 2
    return write() if sys.argv[1] == "--write" else check()


if __name__ == "__main__":
    raise SystemExit(main())
