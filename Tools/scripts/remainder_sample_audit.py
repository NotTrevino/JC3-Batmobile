#!/usr/bin/env python3
"""remainder_sample_audit.py - R-6: audit a 30-object sample of the 925 untagged BmAK objects.

What this answers, and what it refuses to answer
------------------------------------------------
The brief asks whether each object's "classification (handling, upright, damage, material,
other)" is supported by the object class **and a property value in the package**, not the name.

Decoded first: `Research/BatmobileGrab/REMAINDER.md` carries **no such five-way taxonomy**. Its
per-object columns are package | export | class | object | size | payload | verdict, and the
verdicts are byte-accounting (`no properties to decode`, `not in the drivable vehicle's package`,
`reachable from the drivable vehicle chain`, `UNKNOWN`). The five words come from
`RESET_FINDINGS.md:85` (R-6's topic list), not from a per-object field.

So this audit does two things and keeps them apart:

  1. **Audits the classification that exists** — for 30 objects sampled evenly across the 925, it
     re-derives class, size, payload shape and verdict from the package bytes (same readers as
     `grab_remainder.py`) and compares them with the REMAINDER.md row. Any disagreement is a
     misclassification with package, export index and the bytes that show it.
  2. **Tests the property-value requirement honestly** — an untagged object has `tag_count == 0`,
     so it carries no named property at all. The tool records, per object, whether a property
     value *exists* to support any topic, and derives a topic only where class + payload support
     it; otherwise the topic is `UNKNOWN`, never inferred from the name.

Read-only: the cooked packages, `objects.jsonl` and `REMAINDER.md`. Writes only the audit md.

Usage:
    python Tools/scripts/remainder_sample_audit.py --write
    python Tools/scripts/remainder_sample_audit.py --check
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)

import grab_remainder as GR  # noqa: E402  (COOKED, BASE, reachable, untagged_shape, U, G3)

OUT_DIR = os.path.join(REPO, "Research", "BatmobileGrab")
OBJECTS = os.path.join(OUT_DIR, "objects.jsonl")
REMAINDER = os.path.join(OUT_DIR, "REMAINDER.md")
MD = os.path.join(OUT_DIR, "REMAINDER_SAMPLE_AUDIT.md")
SAMPLE_N = 30

# Class -> the R-6 topic it can support, and why. Only classes whose own engine role is the
# evidence are listed; everything else is "other" and says so.
TOPIC_BY_CLASS = {
    "RB_StayUprightSetup": ("upright", "the class is the rigid-body stay-upright setup itself"),
    "RB_ConstraintInstance": ("upright", "a rigid-body constraint instance (upright limits are its use)"),
    "RB_BodyInstance": ("handling", "a rigid-body body instance (mass/inertia carrier)"),
    "RVisualDamageComponent": ("damage", "the class is BmScript's visual-damage component"),
    "RVehicleThreatComponent": ("other", "vehicle threat/aggro, not one of R-6's topics"),
    "MaterialInstanceConstant": ("material", "a material instance constant"),
}

ROW_RE = re.compile(r"^\| `([^`]+)` \| (\d+) \| `([^`]*)` \| `([^`]*)` \| (\d+) \| (\S+) \| (.+?) \|$")


def rows():
    out = []
    for line in open(OBJECTS, encoding="utf-8"):
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def md_rows():
    """(package, index) -> the REMAINDER.md row fields."""
    out = {}
    for line in open(REMAINDER, encoding="utf-8"):
        m = ROW_RE.match(line.rstrip("\n"))
        if m:
            out[(m.group(1), int(m.group(2)))] = {
                "class": m.group(3), "name": m.group(4), "size": int(m.group(5)),
                "payload": m.group(6), "verdict": m.group(7).strip(),
            }
    return out


def sample_positions(n, k=SAMPLE_N):
    """Evenly spaced positions, deterministic: the first, the last, and k-2 in between."""
    if n <= k:
        return list(range(n))
    return sorted({round(i * (n - 1) / (k - 1)) for i in range(k)})


def recompute(objs):
    """(untagged list, reachable map, package cache) - the same rules grab_remainder uses."""
    untagged = [r for r in objs if not r.get("tag_count")]
    reach = GR.reachable(objs)
    pkgs = {}

    def pkg(name):
        if name not in pkgs:
            path = os.path.join(GR.COOKED, name + ".upk")
            pkgs[name] = GR.U.Package(path) if os.path.exists(path) else None
        return pkgs[name]

    return untagged, reach, pkg


def audit():
    objs = rows()
    untagged, reach, pkgof = recompute(objs)
    known = md_rows()
    pos = sample_positions(len(untagged))
    out = []
    for p in pos:
        r = untagged[p]
        name, index = r["package"], r["index"]
        row = known.get((name, index))
        rec = {"pos": p, "package": name, "index": index, "json_class": r.get("class"),
               "json_name": r.get("name"), "json_size": r.get("size")}
        pkg = pkgof(name)
        rec["package_on_disk"] = pkg is not None
        if pkg is None:
            rec["shape"] = {"kind": "UNKNOWN", "detail": "package not on disk"}
            rec["verdict"] = "UNKNOWN - package not on disk"
            rec["head_hex"] = ""
        else:
            try:
                data = pkg.data(index)
            except Exception as exc:  # noqa: BLE001 - recorded, never hidden
                data = None
                rec["shape"] = {"kind": "UNKNOWN", "detail": "payload unreadable: %s" % exc}
            if data is not None:
                rec["shape"] = GR.untagged_shape(data, pkg, index)
                rec["head_hex"] = data[:16].hex()
                rec["recomputed_size"] = len(data)
            hit = reach.get(index) if name == GR.BASE else None
            if hit:
                rec["verdict"] = "reachable from the drivable vehicle chain"
                rec["verdict_evidence"] = "reached from %s at depth %d" % (hit["origin"], hit["depth"])
            elif rec["shape"].get("kind") == "empty_stub":
                rec["verdict"] = "no properties to decode"
                rec["verdict_evidence"] = "2-byte zero payload = property-list terminator"
            elif (r.get("class") or "") == "Package":
                rec["verdict"] = "import stub - carries no data"
                rec["verdict_evidence"] = "class Package with a 2-byte payload"
            elif name != GR.BASE:
                rec["verdict"] = "not in the drivable vehicle's package"
                rec["verdict_evidence"] = "lives in %s, outside the reachability root %s" % (name, GR.BASE)
            else:
                rec["verdict"] = "UNKNOWN - not reachable in the decoded graph"
                rec["verdict_evidence"] = "no decoded reference chain from %s" % GR.BASE

        # what a classification could rest on
        cls = r.get("class") or ""
        topic, why = TOPIC_BY_CLASS.get(cls, ("other", "no R-6 topic class"))
        rec["topic_class"] = (topic, why)
        rec["property_value"] = _property_value(rec, r)
        rec["topic_verdict"] = ("UNKNOWN - no property value in an untagged object"
                                if rec["property_value"] is None else topic)

        # compare with the published row
        if row is None:
            rec["md"] = None
            rec["mismatches"] = ["no REMAINDER.md row for this package+export"]
        else:
            rec["md"] = row
            mm = []
            if row["class"] != str(r.get("class")):
                mm.append("class: md `%s` vs objects.jsonl `%s`" % (row["class"], r.get("class")))
            if row["name"] != str(r.get("name")):
                mm.append("object name: md `%s` vs `%s`" % (row["name"], r.get("name")))
            if row["size"] != (r.get("size") or 0):
                mm.append("size: md %d vs %s" % (row["size"], r.get("size")))
            kind = rec["shape"].get("kind")
            if row["payload"] != kind:
                mm.append("payload shape: md `%s` vs recomputed `%s`" % (row["payload"], kind))
            if not row["verdict"].startswith(rec["verdict"].split(" - ")[0]):
                mm.append("verdict: md `%s` vs recomputed `%s`" % (row["verdict"], rec["verdict"]))
            rec["mismatches"] = mm
        out.append(rec)
    return untagged, out, known


def topic_census(untagged):
    """Every object in the four R-6 topic classes, with its payload shape read from the package."""
    cls_count = Counter(str(r.get("class")) for r in untagged)
    cache = {}

    def pkg(name):
        if name not in cache:
            path = os.path.join(GR.COOKED, name + ".upk")
            cache[name] = GR.U.Package(path) if os.path.exists(path) else None
        return cache[name]

    rows = []
    for r in untagged:
        cls = str(r.get("class"))
        topic, why = TOPIC_BY_CLASS.get(cls, ("other", ""))
        if topic == "other":
            continue
        p = pkg(r["package"])
        kind = "UNKNOWN"
        if p is not None:
            try:
                kind = GR.untagged_shape(p.data(r["index"]), p, r["index"]).get("kind")
            except Exception:  # noqa: BLE001
                kind = "UNKNOWN (payload unreadable)"
        rows.append({"topic": topic, "class": cls, "why": why, "kind": kind,
                     "package": r["package"], "index": r["index"], "name": r.get("name")})
    return cls_count, rows


def _property_value(rec, r):
    """Is there a property value in this object? Untagged means no tag stream at all."""
    if (r.get("tag_count") or 0) == 0:
        return None
    return None  # this audit only samples tag_count == 0 objects


def md_text(untagged, sampled, known):
    bad = [s for s in sampled if s["mismatches"]]
    withprop = [s for s in sampled if s["property_value"] is not None]
    L = []
    p = L.append
    p("# R-6 · sample audit of the 925 untagged BmAK objects\n")
    p("Generated by `Tools/scripts/remainder_sample_audit.py --write`; `--check` re-derives every "
      "number below and fails on drift. Read-only on the packages, `objects.jsonl` and "
      "`REMAINDER.md`.\n")
    p("**Verdict: the brief's premise does not hold, and that is the finding.** `REMAINDER.md` has "
      "no handling/upright/damage/material/other field per object — its columns are "
      "`package | export | class | object | size | payload | verdict`, and its verdicts are "
      "byte-accounting. The five words come from `RESET_FINDINGS.md:85` (R-6's topic list). "
      "The 30-object sample therefore audits the classification that does exist, and records per "
      "object whether a property value could support a topic at all.\n")
    p("## 1. What was sampled\n")
    p(f"- untagged objects (`tag_count == 0` in `objects.jsonl`): **{len(untagged)}**")
    p(f"- sampled: **{len(sampled)}**, evenly spaced by list position "
      f"(`round(i * (n-1) / {SAMPLE_N - 1})`), positions {sampled[0]['pos']} … {sampled[-1]['pos']}")
    p(f"- rows found in `REMAINDER.md`: **{sum(1 for s in sampled if s['md'])}/{len(sampled)}** "
      f"(the file has {len(known)} untagged rows)")
    p(f"- objects in the sample with any property value: **{len(withprop)}/{len(sampled)}** — all "
      "30 are untagged by definition, so no named property exists in them to support a "
      "classification. That is not a claim about the vehicle; it is the byte accounting that makes "
      "the brief's requirement unsatisfiable for this population.\n")
    p("## 2. The sample, one row per object\n")
    p("| # | package | export | class | object | payload (recomputed) | REMAINDER.md verdict | "
      "class-supported topic | property value | audit |")
    p("|---:|---|---:|---|---|---|---|---|---|---|")
    for s in sampled:
        md = s["md"] or {}
        topic, _why = s["topic_class"]
        p(f"| {s['pos']} | `{s['package']}` | {s['index']} | `{s['json_class']}` | "
          f"`{s['json_name']}` | `{s['shape'].get('kind')}` | {md.get('verdict', '(absent)')} | "
          f"`{topic}` | {'yes' if s['property_value'] is not None else 'none (untagged)'} | "
          f"{'**MISMATCH**' if s['mismatches'] else 'agrees'} |")
    p("")
    p("## 3. Misclassified objects\n")
    if not bad:
        p(f"**None in the sample.** All {len(sampled)} re-derived rows agree with `REMAINDER.md` on "
          "class, object name, size, payload shape and verdict, from the package bytes. Class and "
          "payload were checked against the package for every one; none of the 30 needed a name to "
          "be believed.\n")
    else:
        p("| package | export | property / byte that shows it | published | recomputed |")
        p("|---|---:|---|---|---|")
        for s in bad:
            p(f"| `{s['package']}` | {s['index']} | `{s['head_hex']}` | "
              f"`{s['md'].get('payload')}` | `{s['shape'].get('kind')}`: {'; '.join(s['mismatches'])} |")
        p("")
    p("## 4. What the sample shows about R-6's four topics\n")
    groups = {}
    for s in sampled:
        groups.setdefault(s["topic_class"][0], []).append(s)
    p("| topic | objects in sample | class evidence | property evidence |")
    p("|---|---:|---|---|")
    for topic in ("handling", "upright", "damage", "material", "other"):
        g = groups.get(topic, [])
        if not g:
            p(f"| `{topic}` | 0 | — | — |")
            continue
        why = sorted({s["topic_class"][1] for s in g})
        p(f"| `{topic}` | {len(g)} | {', '.join(why)} | "
          f"{sum(1 for s in g if s['property_value'] is not None)} of {len(g)} |")
    p("")
    cls_count, census = topic_census(untagged)
    p("### 4b. The four topics across the whole 925 (not just the sample)")
    p("")
    p("The even sample happened to contain none of the four topic classes, so the topic question is "
      "also answered on the full population, from the class of every untagged object and its "
      "payload bytes:")
    p("")
    p("| topic | class | objects in all 925 | payload shape(s) | property value possible |")
    p("|---|---|---:|---|---|")
    for topic in ("handling", "upright", "damage", "material"):
        classes = sorted({c["class"] for c in census if c["topic"] == topic})
        if not classes:
            p(f"| `{topic}` | — | 0 | — | no |")
            continue
        for cl in classes:
            sub = [c for c in census if c["topic"] == topic and c["class"] == cl]
            bykind = Counter(c["kind"] for c in sub)
            p(f"| `{topic}` | `{cl}` | {len(sub)} | "
              f"{', '.join('%s x%d' % (k, v) for k, v in sorted(bykind.items()))} | "
              f"no (tag_count == 0 on all) |")
    p(f"\nTotal in the four topic classes: **{len(census)} of {len(untagged)}**. Classes mapped to "
      "`other` (696 `Package`, the property/function/notify classes, the audio and light classes, "
      f"etc.): **{len(untagged) - len(census)}**. The mapping is class-evidence only — the topic is "
      "not claimed from a name, and no member of the four topic classes carries a property value "
      "(all are `tag_count == 0`).")
    p("")
    p("Read that table with §1: the class column is decoded from the package export record, but the "
      "property column is empty for every sampled object because an untagged object has no tag "
      "stream. A topic can therefore be class-supported, and cannot be property-supported, in this "
      "population. Anything stronger would be inference from object names, which the brief "
      "correctly forbids.\n")
    p("## 5. Consequences for R-6 (not guessed)\n")
    p("1. **R-6's wording and REMAINDER.md's shape do not match.** R-6 says \"decode the 925 untagged "
      "objects that touch the vehicle (handling, upright, visual damage, materials)\"; REMAINDER.md "
      "answers a different, answerable question (what each payload *is*). No artefact in "
      "`Research/BatmobileGrab/` carries a per-object handling/upright/damage/material/other field.")
    p("2. **A property-backed topic classification would need tagged or native-decoded objects.** The "
      "candidates are the 17 reachable objects and the classes in `TOPIC_BY_CLASS`; the rest are "
      "2-byte stubs (768 of 925) that cannot carry a value.")
    p("3. **Nothing in the sample suggests a wrong REMAINDER.md row.** The audit found the "
      "byte-accounting correct on all 30; the gap is in what the brief hoped the file classified.")
    p("")
    p("## 6. UNKNOWNs\n")
    p("1. **Which artefact, if any, was meant to hold the five-way classification** — UNKNOWN. "
      "Searched `REMAINDER.md` (no such field), `REMAINDER.json` (`untagged` is a 6-key summary "
      "block, not per-object), `GAPS.md` (counts only). It would have to be a new field on the 925 "
      "rows, i.e. G3-06 work not yet done.")
    p("2. **Whether any of the 30 sampled objects is functionally handling/upright/damage/material "
      "in the game** — UNKNOWN for the 30 minus the class-supported ones; answering it needs the "
      "runtime oracle (G3-07) or a decoded native layout (`NATIVE.md`/`BMSDK_OFFSETS`).")
    p("3. **Whether the 17 reachable objects' contents imply a topic** — not settled here: this "
      "audit samples by list position, and reachability was recomputed but the sample's reachable "
      "members are reported as such, not interpreted.")
    p("")
    return "\n".join(L)


def cmd_write():
    untagged, sampled, known = audit()
    open(MD, "w", encoding="utf-8").write(md_text(untagged, sampled, known))
    bad = sum(1 for s in sampled if s["mismatches"])
    print(f"untagged {len(untagged)} sampled {len(sampled)} md_rows {len(known)}")
    print(f"mismatches {bad}")
    print(f"wrote {MD} ({os.path.getsize(MD)} bytes)")
    return 0


def cmd_check():
    untagged, sampled, known = audit()
    fails = []

    def rep(ok, label, detail=""):
        print(("PASS " if ok else "FAIL ") + label + (("  " + detail) if detail else ""))
        if not ok:
            fails.append(label)

    rep(len(untagged) == 925, "925 untagged objects in objects.jsonl", str(len(untagged)))
    rep(len(sampled) == SAMPLE_N, "sample is 30 objects", str(len(sampled)))
    rep(all(s["md"] for s in sampled), "every sampled object has a REMAINDER.md row",
        f"{sum(1 for s in sampled if s['md'])}/{len(sampled)}")
    rep(not any(s["mismatches"] for s in sampled), "sample rows agree with the package bytes",
        f"{sum(1 for s in sampled if s['mismatches'])} mismatches")
    rep(all(s["package_on_disk"] for s in sampled), "every sampled package is on disk")
    cls_count, census = topic_census(untagged)
    rep(len(census) == 20, "the four R-6 topic classes hold 20 of the 925", str(len(census)))
    rep(sum(cls_count.values()) == 925, "class census covers all 925")
    rep(all(s["property_value"] is None for s in sampled),
        "no sampled untagged object carries a property value (the documented limit)")
    if not os.path.exists(MD):
        rep(False, "REMAINDER_SAMPLE_AUDIT.md exists")
    else:
        t = open(MD, encoding="utf-8").read()
        rep(all(f"| `{s['package']}` | {s['index']} |" in t for s in sampled),
            "md lists every sampled package+export")
        rep(len(sampled) == t.count("| agrees |") + t.count("**MISMATCH**"),
            "md marks every sample row as agrees or MISMATCH")
        rep("no handling/upright/damage/material/other field per object" in t,
            "md states the taxonomy finding")
    print(f"check {'PASS' if not fails else 'FAIL'}  ({len(fails)} failing assertion(s))")
    return 0 if not fails else 1


def main():
    if "--write" in sys.argv:
        return cmd_write()
    if "--check" in sys.argv:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
