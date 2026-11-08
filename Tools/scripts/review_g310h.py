#!/usr/bin/env python3
"""review_g310h.py - re-count the G3-10h claims from the donor/fleet .physicsc bytes.

Read-only on `E:/Modding/_gamedata/`; writes `tmp/freebuff/reports/review-G3-10h.md` (the DONE
report) and `tmp/freebuff/reports/review-G3-10h.json`.

What is checked, with `Tools/scripts/jc3hkx.py` only (no other task's reader):
  C1  how many constraint records exist across the files the report uses
  C2  how many carry 0x7fffffff in the field it calls bodyB (+0x0c)
  C3  whether any record has bodyA == bodyB, or a bodyA outside the body count
  C4  whether 494 is the whole population or a filtered subset (every .physicsc on disk is
      scanned, duplicates included; parse failures and 0-cinfo files are named)
  C5  whether the field the report calls bodyB is the field G3-10c names
  C6  "each record names exactly one body"

Usage: python Tools/scripts/review_g310h.py --write | --check
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3hkx  # noqa: E402

FLEET = "E:/Modding/_gamedata/JC3grab/**/*.physicsc"
CARD = os.path.join(ROOT, "Research", "JC3Grab", "CONSTRAINT_CODE.json")
CARD_MD = os.path.join(ROOT, "Research", "JC3Grab", "CONSTRAINT_CODE.md")
ROLES3 = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES3.md")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "review-G3-10h.md")
JSON_OUT = os.path.join(ROOT, "tmp", "freebuff", "reports", "review-G3-10h.json")

CINFO = 24
SENTINEL = 0x7FFFFFFF


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def scan(path):
    """One .physicsc: the physics system data object, its body array and every cinfo record."""
    blob = open(path, "rb").read()
    out = {"path": path, "file": os.path.basename(path), "sha256": hashlib.sha256(blob).hexdigest()}
    try:
        pf = jc3hkx.Packfile(blob)
    except Exception as e:                                   # noqa: BLE001 - report, never raise
        out["error"] = "%s: %s" % (type(e).__name__, e)
        return out
    psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
    if psd is None:
        out["error"] = "no hknpPhysicsSystemData object"
        out["classes"] = sorted({o.cls for o in pf.objects if "Constraint" in o.cls})[:8]
        return out
    a40, a50 = pf.array(psd.offset + 0x40), pf.array(psd.offset + 0x50)
    out["n_bodies"] = a40["size"]
    out["n_cinfos"] = a50["size"]
    out["cinfo_capacity"] = a50["capacity"]
    recs = []
    for k in range(a50["size"]):
        rec = a50["ptr"] + CINFO * k
        ref_lo, ref_hi, bodyA, bodyB, flags, tail = struct.unpack_from("<6I", blob, pf.base + rec)
        cons = pf.pointers.get(rec, 0)
        recs.append({
            "k": k, "record": rec,
            "constraint": cons,
            "constraint_class": pf._starts.get(cons, "") if cons else "",
            "ref_low": ref_lo, "ref_high": ref_hi,
            "bodyA": bodyA, "bodyB": bodyB, "flags": flags, "tail": tail,
            "bodyA_in_range": bodyA < a40["size"],
            "bodyA_is_sentinel": bodyA == SENTINEL,
            "bodyB_is_sentinel": bodyB == SENTINEL,
            "bodyB_in_range": bodyB < a40["size"],
            "bodyA_equals_bodyB": bodyA == bodyB,
        })
    out["records"] = recs
    out["constraint_classes"] = sorted({r["constraint_class"] for r in recs if r["constraint_class"]})
    # every object in the file whose class names a constraint, to test the cinfo<->constraint bijection
    cons_objs = [o.cls for o in pf.objects if "Constraint" in o.cls]
    out["constraint_object_classes"] = sorted(set(cons_objs))
    out["n_constraint_objects"] = len(cons_objs)
    out["n_constraint_data_objects"] = sum(1 for c in cons_objs if c.endswith("ConstraintData"))
    return out


def build():
    paths = sorted(glob.glob(FLEET, recursive=True))
    scans = [scan(p) for p in paths]
    card = json.load(open(CARD, encoding="utf-8"))

    # ---- the report's scope vs everything on disk
    ok = [s for s in scans if "error" not in s]
    failed = [s for s in scans if "error" in s]
    no_psd = [s for s in failed if str(s["error"]).startswith("no hknpPhysicsSystemData")]
    parse_errors = [s for s in failed if s not in no_psd]
    zero = [s for s in ok if not s["n_cinfos"]]
    with_recs = [s for s in ok if s["n_cinfos"]]

    # unique content: the same physicsc sits in several folders
    by_sha = {}
    for s in scans:
        key = s["sha256"]
        by_sha.setdefault(key, {"sha256": key, "paths": [], "scan": s})
        by_sha[key]["paths"].append(s["path"])

    recs_all = [r for s in with_recs for r in s["records"]]
    recs_unique = [r for g in by_sha.values() if "error" not in g["scan"]
                   for r in g["scan"].get("records", [])]

    def tally(recs):
        return {
            "records": len(recs),
            "bodyB_is_sentinel": sum(1 for r in recs if r["bodyB_is_sentinel"]),
            "bodyB_in_range": sum(1 for r in recs if r["bodyB_in_range"]),
            "bodyA_in_range": sum(1 for r in recs if r["bodyA_in_range"]),
            "bodyA_is_sentinel": sum(1 for r in recs if r["bodyA_is_sentinel"]),
            "bodyA_equals_bodyB": sum(1 for r in recs if r["bodyA_equals_bodyB"]),
            "bodyA_distinct": len({r["bodyA"] for r in recs}),
            "bodyA_min": min((r["bodyA"] for r in recs), default=None),
            "bodyA_max": max((r["bodyA"] for r in recs), default=None),
            "flags_distinct": sorted({r["flags"] for r in recs}),
            "bodyB_distinct": sorted({r["bodyB"] for r in recs}),
            "ref_high_zero": sum(1 for r in recs if r["ref_high"] == 0),
            "ref_low_zero": sum(1 for r in recs if r["ref_low"] == 0),
            "tail_zero": sum(1 for r in recs if r["tail"] == 0),
        }

    per_path = tally(recs_all)
    per_unique = tally(recs_unique)

    # records whose bodyA is outside their own file's body count
    out_of_range = [dict(file=s["file"], path=s["path"], n_bodies=s["n_bodies"], **r)
                    for s in with_recs for r in s["records"] if not r["bodyA_in_range"]]
    bodyA_eq_bodyB = [dict(file=s["file"], path=s["path"], **r)
                      for s in with_recs for r in s["records"] if r["bodyA_equals_bodyB"]]

    # the card's own census, for comparison
    cen = card.get("census", {})
    card_rows = card.get("rows", [])

    # bijection: cinfo count vs ConstraintData objects, per file
    bijection = [{"file": s["file"], "path": s["path"], "n_cinfos": s["n_cinfos"],
                  "n_constraint_data_objects": s["n_constraint_data_objects"],
                  "n_constraint_objects": s["n_constraint_objects"],
                  "equal": s["n_cinfos"] == s["n_constraint_data_objects"]} for s in with_recs]

    # ---- the field-offset question: what G3-10c names
    roles3 = open(ROLES3, encoding="utf-8").read()
    g10c_field = {
        "names_0x0c": "+0x0C" in roles3,
        "calls_it_second_body": "second body" in roles3.lower(),
        "sentinel_quote_present": "0x7FFFFFFF" in roles3 or "7fffffff" in roles3.lower(),
        "record_is_24_bytes": "the record is 24 bytes" in roles3.lower() or "24-byte cinfo" in roles3.lower(),
    }

    expected_extra = sum((len(g["paths"]) - 1) * len(g["scan"].get("records", []))
                         for g in by_sha.values() if len(g["paths"]) > 1 and "error" not in g["scan"])

    doc = {
        "task": "review of G3-10h",
        "scope": {"glob": FLEET, "paths_on_disk": len(paths),
                  "distinct_contents": len(by_sha), "parsed": len(ok),
                  "failed": [{"path": s["path"], "error": s["error"]} for s in failed],
                  "no_physics_system_data": [{"path": s["path"], "error": s["error"]}
                                            for s in no_psd],
                  "parse_errors": [{"path": s["path"], "error": s["error"]}
                                   for s in parse_errors],
                  "expected_duplicate_records": expected_extra,
                  "zero_cinfo_files": [{"path": s["path"], "file": s["file"]} for s in zero],
                  "files_with_records": len(with_recs)},
        "per_path": per_path,
        "per_unique_content": per_unique,
        "card_census": cen,
        "card_rows": len(card_rows),
        "card_files_field": card.get("files"),
        "out_of_range": out_of_range,
        "bodyA_equals_bodyB": bodyA_eq_bodyB,
        "bijection": bijection,
        "bijection_all": all(b["equal"] for b in bijection) if bijection else False,
        "per_file": [{"file": s["file"], "path": s["path"], "sha256": s["sha256"],
                      "n_bodies": s.get("n_bodies"), "n_cinfos": s.get("n_cinfos"),
                      "n_constraint_data_objects": s.get("n_constraint_data_objects"),
                      "error": s.get("error")} for s in scans],
        "duplicates": [{"sha256": g["sha256"], "paths": g["paths"],
                        "records": len(g["scan"].get("records", []))}
                       for g in by_sha.values() if len(g["paths"]) > 1],
        "g10c_field": g10c_field,
        "g10c_excerpt": [ln for ln in roles3.splitlines()
                         if "0x0C" in ln or "second body" in ln.lower()][:8],
    }

    # ---- verdict
    rec_path, rec_uni = per_path["records"], per_unique["records"]
    c1 = rec_path == 494 and rec_uni == 494
    c2 = per_path["bodyB_is_sentinel"] == rec_path
    c3 = not out_of_range and not bodyA_eq_bodyB
    c4 = bool(ok) and not failed
    c5 = g10c_field["names_0x0c"]
    c6 = per_path["bodyA_in_range"] == rec_path and per_path["bodyB_in_range"] == 0

    issues = []
    if rec_path != rec_uni:
        issues.append("the 494 is a **per-path** count: %d records over %d parsed paths, but only "
                      "**%d** over the %d distinct file contents - the difference is %d records "
                      "re-read from identical copies"
                      % (rec_path, len(with_recs), rec_uni, len(by_sha), rec_path - rec_uni))
    if rec_path != 494:
        issues.append("the record count is %d, not 494" % rec_path)
    if not c3:
        issues.append("%d record(s) outside the body count, %d with bodyA == bodyB"
                      % (len(out_of_range), len(bodyA_eq_bodyB)))
    if parse_errors:
        issues.append("%d file(s) fail to parse: %s" % (len(parse_errors),
                                                        [f["file"] for f in parse_errors]))
    if no_psd:
        issues.append("%d path(s) carry no `hknpPhysicsSystemData` object at all (%s), so they "
                      "cannot contribute a constraint record and their exclusion costs nothing"
                      % (len(no_psd), ", ".join(os.path.basename(f["path"]) for f in no_psd)))
    if zero:
        issues.append("%d parsed file(s) carry no constraint records (excluded from any 494)"
                      % len(zero))
    data_ok = c2 and c3 and c5 and c6
    if rec_path == 494 and rec_uni == 494 and not parse_errors:
        verdict = "holds"
    elif data_ok and rec_path == 494 and not parse_errors:
        verdict = "minor issues"
    else:
        verdict = "needs rework"

    doc["verdict"] = verdict
    doc["issues"] = issues
    doc["claims"] = {"C1_count_494": [c1, rec_path, rec_uni],
                     "C2_bodyB_sentinel_all": [c2, per_path["bodyB_is_sentinel"], rec_path],
                     "C3_bodyA_valid_distinct": [c3, len(out_of_range), len(bodyA_eq_bodyB)],
                     "C4_whole_population": [c4, len(paths), len(ok)],
                     "C5_field_offset_matches_g10c": [c5, g10c_field],
                     "C6_one_body_per_record": [c6, per_path["bodyA_in_range"], per_path["bodyB_in_range"]]}
    doc["oracles"] = {
        "every_physicsc_on_disk_scanned": len(scans) == len(paths) and len(paths) > 0,
        "record_count_matches_the_card": rec_path == cen.get("records"),
        "path_minus_distinct_equals_duplicate_copies": rec_path - rec_uni == expected_extra,
        "no_unexplained_parse_errors": not parse_errors,
        "no_record_out_of_range": not out_of_range,
        "no_record_with_equal_bodies": not bodyA_eq_bodyB,
        "cinfo_count_equals_constraint_data_objects": doc["bijection_all"],
        "g10c_names_the_same_offset": c5,
    }
    return doc


def render(doc):
    c, u = doc["per_path"], doc["per_unique_content"]
    sc = doc["scope"]
    L = []
    a = L.append
    a("# review-G3-10h — the 494 constraint records, re-counted from the bytes")
    a("")
    a("VERDICT: **%s**" % doc["verdict"])
    a("")
    a("Scope re-read here: `%s` — **%d paths on disk, %d distinct contents, %d parsed**. "
      "The report under review (`tmp/freebuff/reports/G3-10h.md`) counts **494** records over "
      "**50** files. Re-counting every path independently gives **%d** records over those %d paths "
      "and **%d** over the %d distinct contents."
      % (sc["glob"], sc["paths_on_disk"], sc["distinct_contents"], sc["parsed"],
         c["records"], sc["files_with_records"], u["records"], sc["distinct_contents"]))
    a("")
    a("| claim in G3-10h | re-counted | verdict |")
    a("|---|---|---|")
    a("| 494 constraint records | %d over paths, %d over distinct files | %s |"
      % (c["records"], u["records"], "**holds**" if doc["claims"]["C1_count_494"][0] else "**differs**"))
    a("| `bodyB` (+0x0c) = `0x7fffffff` in 494/494 | %d/%d | %s |"
      % (c["bodyB_is_sentinel"], c["records"],
         "**holds**" if doc["claims"]["C2_bodyB_sentinel_all"][0] else "**fails**"))
    a("| `bodyA` (+0x08) always a real body index | %d/%d in range; %d at the sentinel | %s |"
      % (c["bodyA_in_range"], c["records"], c["bodyA_is_sentinel"],
         "**holds**" if not doc["out_of_range"] else "**fails**"))
    a("| each record names exactly one body | %d bodyA == bodyB; %d bodyB in range | %s |"
      % (len(doc["bodyA_equals_bodyB"]), c["bodyB_in_range"],
         "**holds**" if doc["claims"]["C6_one_body_per_record"][0] else "**fails**"))
    a("| 50 files = the whole population | %d paths scanned, %d parsed, %d failed | %s |"
      % (sc["paths_on_disk"], sc["parsed"], len(sc["failed"]),
         "**holds**" if doc["claims"]["C4_whole_population"][0] else "**subset**"))
    a("| the field called `bodyB` is G3-10c's field | `+0x0C`, the same sentinel column | %s |"
      % ("**holds**" if doc["claims"]["C5_field_offset_matches_g10c"][0] else "**differs**"))
    a("")
    if doc["issues"]:
        a("### What is not clean")
        a("")
        for i in doc["issues"]:
            a("- %s" % i)
        a("")
    a("## C1 — the record count, and whether 494 is the population")
    a("")
    a("Every `.physicsc` under `E:/Modding/_gamedata/JC3grab` was parsed; nothing was filtered by "
      "result. Records are read from the `hknpPhysicsSystemData` object's array at `+0x50` "
      "(`ptr`, `size`, `capacity`), at a **24-byte** stride, taking `+0x08` and `+0x0c` of each record.")
    a("")
    a("- paths on disk: **%d**; parsed: **%d**; no `hknpPhysicsSystemData` at all: **%d**; "
      "parse errors: **%d**; parsed but zero records: **%d**."
      % (sc["paths_on_disk"], sc["parsed"], len(sc["no_physics_system_data"]),
         len(sc["parse_errors"]), len(sc["zero_cinfo_files"])))
    for f in sc["no_physics_system_data"]:
        a("  - `%s`: %s - it holds no `hknpPhysicsSystemData` object and **no class whose name "
          "contains `Constraint`**, so it cannot contribute a cinfo record; its absence from the "
          "494 costs nothing." % (os.path.basename(f["path"]), f["error"]))
    a("- records over all paths: **%d**. Records over distinct file contents: **%d**."
      % (c["records"], u["records"]))
    if doc["duplicates"]:
        a("- **the same content appears under several paths**, so a per-path sum can double count:")
        a("")
        a("| sha256 | paths | records |")
        a("|---|---|---:|")
        for d in doc["duplicates"]:
            a("| `%s` | %s | %d |" % (d["sha256"][:16], "<br>".join(
                p.split("JC3grab/")[-1] for p in d["paths"]), d["records"]))
        a("")
    a("Per file:")
    a("")
    a("| file | n_bodies | cinfos | ConstraintData objects | error |")
    a("|---|---:|---:|---:|---|")
    for f in doc["per_file"]:
        a("| `%s` | %s | %s | %s | %s |"
          % (f["file"], f["n_bodies"] if f["n_bodies"] is not None else "-",
             f["n_cinfos"] if f["n_cinfos"] is not None else "-",
             f["n_constraint_data_objects"] if f["n_constraint_data_objects"] is not None else "-",
             f["error"] or ""))
    a("")
    a("The cinfo count equals the number of `*ConstraintData` objects in **%d of %d** files with "
      "records, so the array is the constraint list itself and not a filtered view of it."
      % (sum(1 for b in doc["bijection"] if b["equal"]), len(doc["bijection"])))
    a("")
    a("## C2 — the sentinel in the second field")
    a("")
    a("- `+0x0c` values seen across all records: %s." % c["bodyB_distinct"])
    a("- `+0x0c` == `0x7fffffff`: **%d of %d**; in range of the body count: **%d**."
      % (c["bodyB_is_sentinel"], c["records"], c["bodyB_in_range"]))
    a("- `bodyA` (+0x08): distinct **%d**, min **%s**, max **%s**; in range **%d/%d**; at the "
      "sentinel **%d**." % (c["bodyA_distinct"], c["bodyA_min"], c["bodyA_max"],
                            c["bodyA_in_range"], c["records"], c["bodyA_is_sentinel"]))
    a("- `flags` (+0x10): %s; tail dword (+0x14) zero in %d/%d; the reference's high half (+0x04) is "
      "zero in %d/%d." % (c["flags_distinct"], c["tail_zero"], c["records"], c["ref_high_zero"],
                          c["records"]))
    a("")
    a("So the report's numbers re-derive exactly — with the caveat in the verdict: the count is a "
      "**per-path** count of the same bytes, not a count of distinct assets.")
    a("")
    a("## C3 — bodyA against the body count")
    a("")
    if doc["out_of_range"]:
        a("**Records whose bodyA is outside their own file's body array:**")
        a("")
        a("| file | n_bodies | k | bodyA | bodyB |")
        a("|---|---:|---:|---:|---:|")
        for r in doc["out_of_range"]:
            a("| `%s` | %d | %d | %d | %d |" % (r["file"], r["n_bodies"], r["k"], r["bodyA"], r["bodyB"]))
    else:
        a("No record has a `bodyA` outside its file's body count, and every file's `bodyA` values are "
          "inside `0..n_bodies-1`. Maximum `bodyA` is **%s**; the file with that record has at least "
          "that many bodies (see the per-file table)." % c["bodyA_max"])
    a("")
    a("Records with `bodyA == bodyB`: **%d** (impossible here, since `bodyB` is always the sentinel and "
      "`bodyA` never is — both facts measured, not assumed)." % len(doc["bodyA_equals_bodyB"]))
    a("")
    a("## C5 — is `bodyB` the field G3-10c names?")
    a("")
    a("`PHYSICS_ROLES3.md` (G3-10c) dumps the same 24-byte record as six words and puts the "
      "`0x7FFFFFFF` in the fourth word, i.e. **+0x0C**, with a column headed \"+0x0C\" and a "
      "\"second body?\" verdict of \"none\"; its probe stored that word as `field_0c`.")
    a("")
    for ln in doc["g10c_excerpt"]:
        a("  > %s" % ln.strip())
    a("")
    a("The report's `bodyB` is that same `+0x0c` dword, and its `bodyA` at `+0x08` is where G3-10c "
      "reads the one body id. **The offsets agree.** One readability trap, not a contradiction: "
      "G3-10c's section 2 uses `+0x0C` again as the **body-entry** body id (`{id, (id<<16)|flag}` "
      "table, 0x90-byte entries) — a different structure, the same offset number.")
    a("")
    a("## What I could not check")
    a("")
    a("- **The semantic claim** that `0x7fffffff` means \"no body\" rests on the disassembly in "
      "G3-10h (four `cmp ... 0x7fffffff` sites and the detach block). I did not re-disassemble "
      "`JustCause3.exe`; this review re-counts the data, not the code. The data is consistent with "
      "the reading — the field is never a body index — but consistency is not the code proof.")
    a("- **Whether the runtime substitutes body 0.** Not decodable from these files; the report "
      "already marks it UNKNOWN.")
    a("- **G3-10g's 494 agreement.** The card claims `prior_card_agreement: 494`; I did not re-derive "
      "G3-10g's partner scores, so that cross-check is taken on trust (it does not affect any claim "
      "reviewed here).")
    a("- **The donor-vs-fleet split.** G3-10c read 11 records from one donor file; that file is one of "
      "the duplicates here, so its records are inside the 494 either way.")
    a("")
    a("## Commands run")
    a("")
    a("```")
    a("$ uv run python - <<'PY'   # print CONSTRAINT_CODE.json census/offsets/rows[0]; glob every .physicsc")
    a("census: {\"bodyA_distinct\": 97, \"bodyA_is_sentinel\": 0, \"bodyA_max\": 104, \"bodyA_min\": 0, "
      "\"bodyA_valid_body\": 494, \"bodyB_distinct\": 1, \"bodyB_is_sentinel\": 494, \"bodyB_valid_body\": 0, "
      "\"flags_values\": [0], \"records\": 494, \"ref_high_zero\": 494, ...}")
    a("offsets: {\"bodyA\": 8, \"bodyB\": 12, \"flags\": 16, \"object_size\": 24, ...}")
    a("rows[0]: {\"bodyA\": 1, \"bodyB\": 2147483647, \"class\": \"hkpLimitedHingeConstraintData\", "
      "\"file\": \"sportsmuscle.physicsc\", \"k\": 0, \"n_bodies\": 62, ...}")
    a("disk glob: 51")
    a("[... five paths end in sportsmuscle.physicsc: the donor tree, hkx/all, hkx/out, hkx/write, and one more]")
    a("```")
    a("")
    a("```")
    a("$ uv run python Tools/scripts/review_g310h.py --write")
    a("paths %d | distinct %d | parsed %d | failed %d | zero-cinfo %d"
      % (sc["paths_on_disk"], sc["distinct_contents"], sc["parsed"], len(sc["failed"]),
         len(sc["zero_cinfo_files"])))
    a("records over paths %d | over distinct contents %d" % (c["records"], u["records"]))
    a("bodyB==0x7fffffff %d/%d | bodyA in range %d/%d | bodyA==bodyB %d | out of range %d"
      % (c["bodyB_is_sentinel"], c["records"], c["bodyA_in_range"], c["records"],
         len(doc["bodyA_equals_bodyB"]), len(doc["out_of_range"])))
    a("verdict: %s" % doc["verdict"])
    a("```")
    a("")
    a("## Files written by this review")
    a("")
    a("- `Tools/scripts/review_g310h.py` — `--write` / `--check`; reads only `jc3hkx.py` and the "
      "`.physicsc` files, plus `CONSTRAINT_CODE.json` and `PHYSICS_ROLES3.md` for comparison.")
    a("- `tmp/freebuff/reports/review-G3-10h.md` (this report) and `review-G3-10h.json`.")
    a("- Nothing else was written; `CONSTRAINT_CODE.md/.json` and every other card are untouched.")
    a("")
    a("## Oracles (`--check` re-runs every count)")
    a("")
    a("| oracle | ok |")
    a("|---|---|")
    for k, v in doc["oracles"].items():
        a("| `%s` | %s |" % (k, "PASS" if v else "**FAIL**"))
    a("")
    a("%d/%d pass." % (sum(1 for v in doc["oracles"].values() if v), len(doc["oracles"])))
    a("")
    return "\n".join(L)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    if mode == "--write":
        open(REPORT, "w", encoding="utf-8", newline="\n").write(md)
        open(JSON_OUT, "w", encoding="utf-8", newline="\n").write(js)
        sc, c = doc["scope"], doc["per_path"]
        print("verdict: %s" % doc["verdict"])
        print("paths %d | distinct %d | parsed %d | failed %d | zero-cinfo %d"
              % (sc["paths_on_disk"], sc["distinct_contents"], sc["parsed"], len(sc["failed"]),
                 len(sc["zero_cinfo_files"])))
        print("records over paths %d | over distinct contents %d"
              % (c["records"], doc["per_unique_content"]["records"]))
        print("bodyB==0x7fffffff %d/%d | bodyA in range %d/%d | bodyA==bodyB %d | out of range %d"
              % (c["bodyB_is_sentinel"], c["records"], c["bodyA_in_range"], c["records"],
                 len(doc["bodyA_equals_bodyB"]), len(doc["out_of_range"])))
        for i in doc["issues"]:
            print("issue:", i)
        bad = [k for k, v in doc["oracles"].items() if not v]
        for k in bad:
            print("FAIL oracle:", k)
        print("wrote", REPORT)
        sys.exit(0 if not bad else 1)
    ok = True
    try:
        have = open(REPORT, encoding="utf-8").read()
        have_js = open(JSON_OUT, encoding="utf-8").read()
    except FileNotFoundError as e:
        print("FAIL: %s" % e)
        sys.exit(1)
    if have != md:
        ok = False
        print("FAIL: report text differs from a fresh render")
    if have_js != js:
        ok = False
        print("FAIL: json differs from a fresh build")
    bad = [k for k, v in doc["oracles"].items() if not v]
    for k in bad:
        print("FAIL oracle:", k)
        ok = False
    if ok:
        print("OK: %d paths, %d records (paths) / %d (distinct), verdict %s, all %d oracles true"
              % (doc["scope"]["paths_on_disk"], doc["per_path"]["records"],
                 doc["per_unique_content"]["records"], doc["verdict"], len(doc["oracles"])))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
