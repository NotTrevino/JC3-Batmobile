"""parts_anim_coverage.py - T-8's moving parts against ANIMATIONS.md and BONES.md.

For every T-12 row in `Working/Translation/T8_PARTS.md` this card asks three decoded questions:

  1. does each cited **animation sequence** exist in `Research/BatmobileGrab/ANIMATIONS.json`,
     and with which `package` / export index?
  2. does the row's **joint bone** appear in that sequence's `moved_bones` (the per-bone range:
     `drot_deg` / `dpos_cm`), and in `BONES.json`'s 180-bone list?
  3. is a **range** recorded for that bone in the sequence (a non-zero rotation or translation)?

Then the inverse direction: every one of the 253 sequences no T-8 row cites, grouped by its
mechanism class, with package and export index.

Read-only.  Writes `Working/Translation/PARTS_ANIM_COVERAGE.{md,json}`.

    python Tools/scripts/parts_anim_coverage.py --write
    python Tools/scripts/parts_anim_coverage.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

T8 = os.path.join(ROOT, "Working", "Translation", "T8_PARTS.json")
ANIM = os.path.join(ROOT, "Research", "BatmobileGrab", "ANIMATIONS.json")
BONES = os.path.join(ROOT, "Research", "BatmobileGrab", "BONES.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "PARTS_ANIM_COVERAGE.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "PARTS_ANIM_COVERAGE.json")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]


def seq_names(row: dict) -> list[str]:
    """The row's cited sequence names, whatever shape T8 stores them in."""
    a = row.get("animation_sequences")
    if a is None:
        return []
    if isinstance(a, dict):
        return list(a)
    out = []
    for x in a:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            out.append(x.get("name") or x.get("sequence") or "")
    return [x for x in out if x]


def build() -> dict:
    t8 = json.load(open(T8, encoding="utf-8"))
    anim = json.load(open(ANIM, encoding="utf-8"))
    bones = json.load(open(BONES, encoding="utf-8"))

    seqs = {}
    for s in anim["sequences"]:
        seqs.setdefault(s["name"], []).append(s)
    bone_names = {b["name"] for b in bones["bones"]}
    bone_index = {b["name"]: b["index"] for b in bones["bones"]}

    rows = []
    cited = set()
    for r in t8["rows"]:
        names = seq_names(r)
        cited.update(names)
        joint = r.get("joint") if isinstance(r.get("joint"), str) else None
        if joint is None and isinstance(r.get("joint"), dict):
            joint = r["joint"].get("bone")
        found, missing, ranges, in_bones = [], [], [], []
        for n in names:
            cands = seqs.get(n) or []
            if not cands:
                missing.append(n)
                continue
            s = cands[0]
            found.append({"name": n, "package": s["package"], "export_index": s["export_index"],
                          "export_name": s["export_name"], "set": s["set"],
                          "outer": s.get("outer"), "mechanism": s.get("mechanism"),
                          "max_rotation_deg": s.get("max_rotation_deg"),
                          "max_translation_cm": s.get("max_translation_cm"),
                          "duplicates": [c["package"] for c in cands]})
            mv = next((m for m in s.get("moved_bones") or [] if m.get("bone") == joint), None)
            if mv:
                ranges.append({"seq": n, "drot_deg": mv.get("drot_deg"),
                               "dpos_cm": mv.get("dpos_cm"), "category": mv.get("category")})
            if joint:
                in_bones.append({"seq": n, "in_moved": bool(mv),
                                 "in_active": joint in (s.get("active_bones") or [])})
        moved_ranges = [x for x in ranges
                        if abs(float(x.get("drot_deg") or 0)) > 1e-9
                        or abs(float(x.get("dpos_cm") or 0)) > 1e-9]
        rows.append({
            "id": r["id"], "part": r.get("part") or "—",
            "mechanism": r.get("mechanism"), "joint": joint,
            "static_reason": r.get("static_reason"),
            "sequences": names, "found": found, "missing": missing,
            "bone_in_bones": bool(joint and joint in bone_names),
            "bone_index": bone_index.get(joint),
            "bone_in_seq": in_bones,
            "ranges": ranges, "has_moved_range": bool(moved_ranges),
            "verdict": ("no-sequence" if not names else
                        "missing-sequence" if missing else
                        "no-bone" if (joint and not (joint in bone_names)) else
                        "no-range" if not moved_ranges else "covered"),
        })

    unrowed = [s for s in anim["sequences"] if s["name"] not in cited]
    by_mech = {}
    for s in unrowed:
        by_mech.setdefault(s.get("mechanism") or "(none)", []).append({
            "name": s["name"], "package": s["package"], "export_index": s["export_index"],
            "set": s["set"], "max_rotation_deg": s.get("max_rotation_deg"),
            "max_translation_cm": s.get("max_translation_cm"),
            "moved_bones": s.get("moved_bone_count"),
        })

    n_cited_exports = sum(1 for s in anim["sequences"] if s["name"] in cited)
    return {
        "rows": rows, "n_rows": len(rows),
        "n_seq": len(anim["sequences"]), "n_cited": n_cited_exports,
        "n_cited_names": len(cited & set(seqs)),
        "n_unrowed": len(unrowed), "unrowed_by_mech": by_mech,
        "unrowed": [{"name": s["name"], "package": s["package"],
                     "export_index": s["export_index"], "set": s["set"],
                     "mechanism": s.get("mechanism")} for s in unrowed],
        "bones_total": len(bones["bones"]),
        "bones_pkg": bones.get("package"), "bones_export": bones.get("export_index"),
        "bones_mesh": bones.get("mesh"),
        "sha": {"T8_PARTS.json": sha16(T8), "ANIMATIONS.json": sha16(ANIM),
                "BONES.json": sha16(BONES)},
        "no_seq_rows": [r["id"] for r in rows if not r["sequences"]],
        "counts": {k: sum(1 for r in rows if r["verdict"] == k) for k in
                   ("covered", "no-range", "no-bone", "missing-sequence", "no-sequence")},
    }


def render(d: dict) -> str:
    p = []
    a = p.append
    a("# PARTS_ANIM_COVERAGE - T-8's moving parts against ANIMATIONS.md and BONES.md")
    a("")
    a("Generated by `Tools/scripts/parts_anim_coverage.py --write`; `--check` re-derives every row "
      "and fails on drift.  Read-only on `Research/` and on T-8's files.")
    a("")
    a(f"**Verdict.** {d['n_rows']} T-8 rows cite {d['n_cited_names']} distinct clip names "
      f"({d['n_cited']} sequence exports) out of {d['n_seq']}; "
      f"**{d['counts']['covered']} rows are fully covered** (sequence found, joint bone "
      f"in `moved_bones` with a non-zero range, bone in `BONES.json`), "
      f"**{d['counts']['no-sequence']} rows have no sequence at all** "
      f"({', '.join(d['no_seq_rows'])}), and **{d['n_unrowed']} sequences are cited by no row**. "
      f"No row cites a sequence that is missing from `ANIMATIONS.md`, and every non-static row's "
      f"joint bone is in `BONES.json`.")
    a("")
    a("## 1. Inputs")
    a("")
    a("| file | sha256 (first 16) |")
    a("|---|---|")
    for k, v in d["sha"].items():
        a(f"| `{k}` | `{v}…` |")
    a("")
    a(f"`BONES.json` is the {d['bones_mesh']} skeleton ({d['bones_total']} bones) out of "
      f"`{d['bones_pkg']}` export {d['bones_export']}; `ANIMATIONS.json` holds {d['n_seq']} "
      f"sequences across 4 packages.")
    a("")
    a("## 2. Every T-8 row: sequence, bone, range")
    a("")
    a("`seq (package/export)` is the `AnimSequence` export each cited clip resolves to; "
      "`joint range` is the per-bone `drot_deg` / `dpos_cm` that sequence records for the joint; "
      "`bone` = the joint is in `BONES.json` (bone index).")
    a("")
    a("| id | part | joint bone | cited sequence(s) | seq (package/export) | joint range in ANIMATIONS | bone in BONES | verdict |")
    a("|---|---|---|---|---|---|---|---|")
    for r in d["rows"]:
        seqs = ", ".join(f"`{s}`" for s in r["sequences"]) or "**none**"
        loc = "; ".join(f"`{f['package']}`/{f['export_index']} ({f['set']})" for f in r["found"]) or "—"
        rng = "; ".join(f"{x['drot_deg']:g}° / {x['dpos_cm']:g} cm" for x in r["ranges"]) or "—"
        bone = (f"`{r['joint']}` (#{r['bone_index']})" if r["bone_in_bones"] else
                (f"**`{r['joint']}` absent**" if r["joint"] else "no joint"))
        a(f"| {r['id']} | `{r['part']}` | `{r['joint'] or '—'}` | {seqs} | {loc} | {rng} | "
          f"{bone} | **{r['verdict']}** |")
    a("")
    a("## 3. Parts with a row but no sequence")
    a("")
    empty = [r for r in d["rows"] if not r["sequences"]]
    if not empty:
        a("none")
    else:
        a("| id | part | behaviour | why no sequence |")
        a("|---|---|---|---|")
        for r in empty:
            a(f"| {r['id']} | `{r['part']}` | {r['mechanism'] or '—'} | "
              f"{r['static_reason'] or 'not recorded in T-8 - UNKNOWN'} |")
    a("")
    a("## 4. Sequences with no T-8 row")
    a("")
    a(f"**{d['n_unrowed']} of {d['n_seq']} sequences** are cited by no row.  The table groups them "
      f"by mechanism class; each entry is `name` (`package`/export index).  The full flat list is in "
      f"`PARTS_ANIM_COVERAGE.json` under `unrowed`.")
    a("")
    a("| mechanism | sequences | names |")
    a("|---|---:|---|")
    for mech, items in sorted(d["unrowed_by_mech"].items(), key=lambda kv: -len(kv[1])):
        names = ", ".join(f"`{x['name']}` ({x['package']}/{x['export_index']})" for x in items)
        a(f"| `{mech}` | {len(items)} | {names} |")
    a("")
    a("## 5. Checks")
    a("")
    a("| # | check | result |")
    a("|---:|---|---|")
    a(f"| 1 | every cited sequence name exists in ANIMATIONS.json | "
      f"{'PASS' if not any(r['missing'] for r in d['rows']) else 'FAIL'} |")
    a(f"| 2 | every cited sequence resolves to a package + export index | "
      f"{'PASS' if all(f['package'] and f['export_index'] is not None for r in d['rows'] for f in r['found']) else 'FAIL'} |")
    a(f"| 3 | every non-static row's joint bone is in BONES.json | "
      f"{'PASS' if all(r['bone_in_bones'] for r in d['rows'] if r['joint']) else 'FAIL'} |")
    a(f"| 4 | every row with a sequence has a non-zero joint range in it | "
      f"{'PASS' if all(r['has_moved_range'] for r in d['rows'] if r['sequences']) else 'FAIL'} "
      f"({sum(1 for r in d['rows'] if r['sequences'] and r['has_moved_range'])}/"
      f"{sum(1 for r in d['rows'] if r['sequences'])}) |")
    a(f"| 5 | the 15 rows are partitioned into covered / no-sequence | "
      f"{'PASS' if d['n_rows']==15 and d['counts']['covered']+d['counts']['no-sequence']==d['n_rows'] else 'FAIL'} "
      f"({d['counts']['covered']} + {d['counts']['no-sequence']} = {d['n_rows']}) |")
    a(f"| 6 | cited + no-row sequence exports add up to the 253 in ANIMATIONS.json | "
      f"{'PASS' if d['n_cited'] + d['n_unrowed'] == d['n_seq'] else 'FAIL'} "
      f"({d['n_cited']} + {d['n_unrowed']} = {d['n_seq']}; {d['n_cited_names']} distinct names) |")
    a("")
    a("## 6. UNKNOWNs")
    a("")
    a("1. **Whether a static row's motion is animatable at all.** P-02/P-05 translate in a sequence "
      "and P-13 has no bone; the rows record why they are static, but no sequence is claimed for "
      "them (B-02 decision).")
    a("2. **Duplicate clip names across packages.** `ANIMATIONS.md` records names repeated across the "
      "four packages; the table cites the first carrier and the JSON keeps the other packages under "
      "`found[].duplicates`. No claim is made about whether the copies differ.")
    a("3. **The JC3-side rate.** T-8 already notes `all_hinged_part_properties` has no rate member; "
      "the ranges here are BmAK animation facts, not JC3 values.")
    a("")
    return "\n".join(p) + "\n"


def check() -> int:
    fails = []
    d = build()
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print(f"FAIL: {rel(OUT_MD)} / {rel(OUT_JSON)} missing (run --write)")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != render(d):
        fails.append("the markdown differs from the re-derived one")
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(json.dumps(d, default=str)):
        fails.append("the json differs from the re-derived one")
    if any(r["missing"] for r in d["rows"]):
        fails.append(f"missing sequences: {[r['missing'] for r in d['rows'] if r['missing']]}")
    if any(not r["bone_in_bones"] for r in d["rows"] if r["joint"]):
        fails.append("a row's joint bone is not in BONES.json")
    if any(not r["has_moved_range"] for r in d["rows"] if r["sequences"]):
        fails.append("a sequenced row has no non-zero joint range")
    if d["n_cited"] + d["n_unrowed"] != d["n_seq"]:
        fails.append("sequence partition does not add up")
    print(f"rows {d['n_rows']} | cited seqs {d['n_cited']}/{d['n_seq']} | unrowed {d['n_unrowed']} | "
          f"covered {d['counts']['covered']} | no-sequence {d['counts']['no-sequence']} "
          f"({', '.join(d['no_seq_rows'])}) | bones {d['bones_total']}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print("PASS: every cited sequence, joint bone and range is recorded; "
          "parts-without-sequence and sequences-without-row are both enumerated")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    x = ap.parse_args()
    if x.write == x.check:
        ap.error("pass exactly one of --write / --check")
    if x.check:
        return check()
    d = build()
    text = render(d)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(json.loads(json.dumps(d, default=str)), f, indent=1)
    print(f"wrote {rel(OUT_MD)} ({len(text)} chars) and {rel(OUT_JSON)}")
    print(f"rows {d['n_rows']} | cited {d['n_cited']} | unrowed {d['n_unrowed']} | "
          f"covered {d['counts']['covered']} | no-sequence {d['no_seq_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
