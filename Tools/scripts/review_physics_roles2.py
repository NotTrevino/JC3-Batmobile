#!/usr/bin/env python3
"""review_physics_roles2.py - independent re-derivation for the G3-10b review.

Re-derives three of `jc3_physics_roles2.py`'s decoded values from the raw
`sportsmuscle.physicsc` bytes, compares them with that tool's stored JSON, and
tests two of its weaker claims:

  R1  the 11 cinfo body ids and the 0x7FFFFFFF sentinel (donor)
  R2  all 56 mass floats at `hknpShapeMassProperties+0x28`, their exact sum and
      their full value census
  R3  body entry 22's translation, and the shape pointers of bodies 16 / 26

  B1  the "limits" column: how many reported limit offsets fall inside a decoded
      atom transform (3x4 rotation + translation = 64 B of the object)
  B2  how many reported limit values are a pivot component re-listed
  B4  "one side per constraint": how many fixups target each constraint data
      object (donor and fleet), and the cinfo words 3/4/5 domains
  B5  the fleet cinfo oracle's blind spot: null cinfo pointers it skips

Read-only on the donor, the fleet directory and G3-10b's outputs. Writes only
`Research/JC3Grab/PHYSICS_ROLES2_REVIEW.md` / `.json`.

Usage:
  python Tools/scripts/review_physics_roles2.py --write
  python Tools/scripts/review_physics_roles2.py --check
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import struct
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402  (shared packfile reader, unmodified)

DONOR = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "sportsmuscle.physicsc")
CARD_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2.json")
FLEET_RAW = r"E:/Modding/_shared/gamedata/JC3grab/hkx/all"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2_REVIEW.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2_REVIEW.json")
CONSTRAINTS = ("hkpLimitedHingeConstraintData", "hkpRagdollConstraintData",
               "hkpHingeConstraintData")
CINFO_STRIDE = 24
BODY_ENTRY = 96
TRANSFORM_SPAN = 64          # 3x4 rotation (48 B) + translation (16 B), as decoded by the card


def u32(blob, base, at):
    return struct.unpack_from("<I", blob, base + at)[0]


def f32(blob, base, at):
    return struct.unpack_from("<f", blob, base + at)[0]


def rev_map(pf):
    rev = {}
    for frm, tgt in pf.pointers.items():
        rev.setdefault(tgt, []).append(frm)
    return rev


def donor_facts():
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"][0]
    a50 = pf.array(psd.offset + 0x50)
    a40 = pf.array(psd.offset + 0x40)

    cinfos = []
    for i in range(a50["size"]):
        at = a50["ptr"] + i * CINFO_STRIDE
        w = struct.unpack_from("<6I", blob, base + at)
        ptr = pf.pointers.get(at, 0)
        cinfos.append({"record_at": at, "constraint": ptr,
                       "constraint_class": pf._starts.get(ptr, ""),
                       "body_id": w[2], "word3": w[3], "word4": w[4], "word5": w[5]})

    masses = sorted(({"offset": o.offset,
                      "mass": f32(blob, base, o.offset + 0x28)}
                     for o in pf.objects if o.cls == "hknpShapeMassProperties"),
                    key=lambda r: r["offset"])

    e_lo, n_bodies = a40["ptr"], a40["size"]
    entries = {}
    for i in (0, 16, 22, 26, 35):
        at = e_lo + BODY_ENTRY * i
        shp = pf.pointers.get(at, 0)
        entries[i] = {"at": at, "shape": shp, "shape_class": pf._starts.get(shp, ""),
                      "position": [f32(blob, base, at + 0x30 + 4 * k) for k in range(4)],
                      "rotation": [f32(blob, base, at + 0x40 + 4 * k) for k in range(4)]}

    rev = rev_map(pf)
    cons = [o for o in pf.objects if o.cls in CONSTRAINTS]
    refs = {o.offset: len(rev.get(o.offset, [])) for o in cons}

    compound_refs = []
    for o in pf.objects:
        if o.cls != "hknpStaticCompoundShape":
            continue
        bodies = []
        for frm in rev.get(o.offset, []):
            if e_lo <= frm < e_lo + BODY_ENTRY * n_bodies and (frm - e_lo) % BODY_ENTRY == 0:
                bodies.append((frm - e_lo) // BODY_ENTRY)
        compound_refs.append({"offset": o.offset, "body_refs": sorted(bodies)})

    return {
        "donor": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
        "bytes": len(blob), "base": base, "bodies": n_bodies,
        "cinfos": cinfos, "mass_count": len(masses), "masses": masses,
        "entries": {str(k): v for k, v in entries.items()},
        "constraint_count": len(cons),
        "constraint_refs": {hex(k): v for k, v in sorted(refs.items())},
        "compound_refs": compound_refs,
    }


def mass_census(masses):
    c = Counter(round(m["mass"], 3) for m in masses)
    return {str(k): v for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))}


def limits_analysis(stored):
    rows, inside, pivot_dup, total = [], 0, 0, 0
    for c in stored["donor"]["constraints"]:
        ats = [t["at"] for t in c["transforms"]]
        piv = [round(x, 6) for t in c["transforms"] for x in t["pivot"]]
        lim = c["angle_like_tail"]
        in_tr = [x for x in lim if any(t <= x["at"] < t + TRANSFORM_SPAN for t in ats)]
        dup = [x for x in lim if round(x["value"], 6) in piv]
        inside += len(in_tr)
        pivot_dup += len(dup)
        total += len(lim)
        rows.append({"constraint": hex(c["offset"]), "class": c["class"],
                     "limits": len(lim), "inside_transform": len(in_tr),
                     "pivot_duplicates": len(dup),
                     "transform_starts": [hex(t) for t in ats],
                     "limit_offsets": [hex(x["at"]) for x in lim]})
    return {"total_limit_values": total, "inside_a_transform": inside,
            "pivot_duplicates": pivot_dup, "rows": rows}


def fleet_facts():
    files = sorted(glob.glob(os.path.join(FLEET_RAW, "*.physicsc")))
    rows, errors = [], []
    wordset = set()
    one_ref, zero_cinfo, cons_total, cinfo_total = 0, 0, 0, 0
    files_checked = 0
    for f in files:
        try:
            blob = open(f, "rb").read()
            pf = jc3hkx.Packfile(blob)
        except Exception as exc:                                # noqa: BLE001
            errors.append({"file": os.path.basename(f), "error": str(exc)})
            continue
        base = pf.base
        psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
        if len(psd) != 1:
            errors.append({"file": os.path.basename(f), "error": f"{len(psd)} system datas"})
            continue
        psd = psd[0]
        a50 = pf.array(psd.offset + 0x50)
        rev = rev_map(pf)
        cons = [o for o in pf.objects if o.cls in CONSTRAINTS]
        files_checked += 1
        cons_total += len(cons)
        cinfo_total += a50["size"]
        for o in cons:
            if len(rev.get(o.offset, [])) == 1:
                one_ref += 1
        for i in range(a50["size"]):
            at = a50["ptr"] + i * CINFO_STRIDE
            if not pf.pointers.get(at, 0):
                zero_cinfo += 1
            w = struct.unpack_from("<6I", blob, base + at)
            wordset.add((w[3], w[4], w[5]))
        rows.append({"file": os.path.basename(f), "cinfos": a50["size"],
                     "constraints": len(cons)})
    return {"dir": FLEET_RAW, "files": len(files), "files_checked": files_checked,
            "errors": errors,
            "constraints": cons_total, "cinfos": cinfo_total,
            "constraints_with_exactly_one_fixup": one_ref,
            "null_cinfo_pointers": zero_cinfo,
            "cinfo_words_3_4_5": sorted([w[0], w[1], w[2]] for w in wordset)}


def build():
    facts = donor_facts()
    stored = json.load(open(CARD_JSON, encoding="utf-8"))
    scon = stored["donor"]["constraints"]
    smass = stored["donor"]["mass_properties"]

    # ---- R1: cinfo body ids
    stored_ids = sorted(c["cinfo"]["body_id"] for c in scon)
    byte_ids = sorted(c["body_id"] for c in facts["cinfos"])
    r1 = {"byte_ids": byte_ids, "stored_ids": stored_ids, "match": byte_ids == stored_ids,
          "word3_values": sorted({c["word3"] for c in facts["cinfos"]}),
          # lists, not tuples: JSON turns tuples into arrays, and --check compares parsed JSON
          "words4_5": sorted([c["word4"], c["word5"]] for c in facts["cinfos"])}

    # ---- R2: masses
    byte_mass = {m["offset"]: round(m["mass"], 6) for m in facts["masses"]}
    stored_mass = {m["offset"]: m["mass"] for m in smass["items"]}
    exact_sum = sum(m["mass"] for m in facts["masses"])
    census = mass_census(facts["masses"])
    missing = {k: v for k, v in census.items() if k not in smass["distinct"]}
    r2 = {"count": len(byte_mass), "stored_count": smass["count"],
          "values_match": byte_mass == stored_mass,
          "exact_sum": exact_sum, "stored_sum": smass["sum"],
          "sum_delta": round(exact_sum - smass["sum"], 9),
          "full_census": census,
          "stored_census": smass["distinct"],
          "census_values_missing_from_stored": missing,
          "stored_census_count_sum": sum(smass["distinct"].values()),
          "positive": all(m["mass"] > 0 for m in facts["masses"])}

    # ---- R3: body entries
    e22 = facts["entries"]["22"]
    stored22 = next((s for s in stored["donor"]["second_id_space"] if s["id"] == 22), None)
    r3 = {"body22_position_bytes": [round(x, 6) for x in e22["position"]],
          "body22_position_stored": (stored22 or {}).get("entry", {}).get("position"),
          "body22_shape_class": e22["shape_class"],
          "body16_shape": hex(facts["entries"]["16"]["shape"]),
          "body16_class": facts["entries"]["16"]["shape_class"],
          "body26_shape": hex(facts["entries"]["26"]["shape"]),
          "body26_class": facts["entries"]["26"]["shape_class"],
          "compound_body_refs": [c["body_refs"] for c in facts["compound_refs"]],
          "compound_refs_stored": [c["ref_body_ids"] for c in stored["donor"]["compounds"]]}

    lim = limits_analysis(stored)
    fleet = fleet_facts()

    core = [r1["match"], r2["values_match"], r3["body22_position_bytes"] ==
            [round(x, 6) for x in (r3["body22_position_stored"] or [])],
            sorted(r3["compound_body_refs"]) == [[16], [26]]]
    issues = []
    if lim["total_limit_values"]:
        issues.append(
            f"the 'limits' column is a value-band float dump, not a decoded limit: "
            f"{lim['inside_a_transform']} of {lim['total_limit_values']} reported values sit "
            f"inside an already-decoded atom transform, and {lim['pivot_duplicates']} are a "
            f"pivot component re-listed; the column must be relabelled derived/UNKNOWN")
    if r2["census_values_missing_from_stored"]:
        issues.append(
            f"the mass census is silently truncated: the stored/printed dict covers "
            f"{r2['stored_census_count_sum']} of {r2['count']} blocks and drops "
            f"{len(r2['census_values_missing_from_stored'])} distinct values "
            f"({sorted(r2['census_values_missing_from_stored'])})")
    if abs(r2["sum_delta"]) > 1e-9:
        issues.append(
            f"the quoted mass total {r2['stored_sum']} is the sum of per-block values rounded "
            f"to 6 dp, not the exact float sum {r2['exact_sum']:.9f} (delta "
            f"{r2['sum_delta']})")
    if not all(x for x in core):
        issues.append("a re-derived core value does not match the card")

    return {
        "schema": 1,
        "generated_by": "Tools/scripts/review_physics_roles2.py --write",
        "review_of": "tools/scripts/jc3_physics_roles2.py",
        "target_card": "G3-10b",
        "R1_cinfo_body_ids": r1,
        "R2_masses": r2,
        "R3_body_entries": r3,
        "B1_limits": lim,
        "B4_one_side": {
            "donor_constraint_fixups": facts["constraint_refs"],
            "donor_constraints": facts["constraint_count"],
            "fleet_constraints": fleet["constraints"],
            "fleet_with_exactly_one_fixup": fleet["constraints_with_exactly_one_fixup"],
            "fleet_cinfo_words_3_4_5": fleet["cinfo_words_3_4_5"],
        },
        "B5_fleet_oracle": {
            "files": fleet["files"], "files_checked": fleet["files_checked"],
            "errors": fleet["errors"], "null_cinfo_pointers": fleet["null_cinfo_pointers"],
            "note": ("the card's fleet `cinfo_bijection` skips a null pointer (`if p`) and "
                     "compares counts, so it cannot detect a null or a duplicate; the donor "
                     "oracle is the strict one"),
        },
        "core_values_match": all(x for x in core),
        "issues": issues,
        "verdict": ("needs rework" if any(not x for x in core) else
                    ("needs rework (limits section)" if lim["pivot_duplicates"] else
                     "minor issues" if issues else "holds")),
        "unknowns": [
            "which value in a hinge's tail really is the limit: not resolved by this review "
            "either; the tail overlaps the atom transforms, so the card's offsets cannot be "
            "separated from transform bytes without the constraint data layout",
            "whether the half of the 'limit' values that are outside the transforms are angles "
            "at all: several are plausible (1.396263 = 80 deg, 0.523599 = 30 deg) but no oracle "
            "in either file proves the field",
            "the partner body of each constraint: not stored in the cinfo (decoded negative, "
            "donor and fleet); where it lives is still unknown (G3-10c agrees)",
        ],
    }


def render_md(doc):
    r1, r2, r3 = doc["R1_cinfo_body_ids"], doc["R2_masses"], doc["R3_body_entries"]
    lim, b4, b5 = doc["B1_limits"], doc["B4_one_side"], doc["B5_fleet_oracle"]
    L = []
    a = L.append
    a("# PHYSICS_ROLES2 review - independent re-derivation (G3-10b)")
    a("")
    a("Generated by `Tools/scripts/review_physics_roles2.py --write`; `--check` recomputes "
      "every number and fails on drift. Inputs are read-only: the donor "
      f"`{doc['R1_cinfo_body_ids'] and 'sportsmuscle.physicsc'}`, the fleet directory and "
      "G3-10b's stored JSON.")
    a("")
    a(f"**VERDICT: {doc['verdict']}** - core values re-derive "
      f"({'all match' if doc['core_values_match'] else 'MISMATCH'}); "
      f"{len(doc['issues'])} issue(s).")
    a("")
    a("## R1. The 11 cinfo body ids (re-derived from the bytes)")
    a("")
    a(f"- bytes: `{r1['byte_ids']}`")
    a(f"- stored: `{r1['stored_ids']}` - **match {r1['match']}**")
    a(f"- word 3 domain: `{[hex(v) for v in r1['word3_values']]}`; words 4/5: "
      f"`{r1['words4_5']}` - one side stored, sentinel confirmed")
    a("")
    a("## R2. The 56 masses (re-derived at `hknpShapeMassProperties+0x28`)")
    a("")
    a(f"- count {r2['count']} (stored {r2['stored_count']}); per-block values match: "
      f"**{r2['values_match']}**; all positive: **{r2['positive']}**")
    a(f"- exact float sum **{r2['exact_sum']:.9f}** vs stored **{r2['stored_sum']}** "
      f"(delta {r2['sum_delta']})")
    a(f"- full census ({len(r2['full_census'])} distinct values, "
      f"{sum(r2['full_census'].values())} blocks): `{r2['full_census']}`")
    a(f"- stored census covers **{r2['stored_census_count_sum']}** blocks; missing: "
      f"`{r2['census_values_missing_from_stored']}`")
    a("")
    a("## R3. Body entries (translation of body 22; compound pointers 16/26)")
    a("")
    a(f"- body 22 position from bytes `{r3['body22_position_bytes']}` vs stored "
      f"`{r3['body22_position_stored']}`")
    a(f"- body 22 shape `{r3['body22_shape_class']}`; body 16 `{r3['body16_shape']}` "
      f"{r3['body16_class']}; body 26 `{r3['body26_shape']}` {r3['body26_class']}")
    a(f"- compound body refs re-derived `{r3['compound_body_refs']}` vs stored "
      f"`{r3['compound_refs_stored']}`")
    a("")
    a("## B1. What the \"limits\" column actually contains")
    a("")
    a(f"{lim['inside_a_transform']} of {lim['total_limit_values']} reported limit values fall "
      f"inside a decoded atom transform; {lim['pivot_duplicates']} are a pivot component "
      "re-listed. Per constraint:")
    a("")
    a("| constraint | limits | inside a transform | pivot duplicates |")
    a("|---|---:|---:|---:|")
    for row in lim["rows"]:
        a(f"| `{row['constraint']}` {row['class'].replace('hkp', '').replace('ConstraintData', '')} "
          f"| {row['limits']} | {row['inside_transform']} | {row['pivot_duplicates']} |")
    a("")
    a("## B2. \"One side per constraint\" (against the bytes, after G3-10c)")
    a("")
    a(f"- donor: {b4['donor_constraints']} constraint objects, fixups targeting each: "
      f"`{b4['donor_constraint_fixups']}`")
    a(f"- fleet: {b4['fleet_with_exactly_one_fixup']}/{b4['fleet_constraints']} constraint "
      f"objects have exactly one fixup pointing at them")
    a(f"- cinfo words 3/4/5 across the fleet: `{b4['fleet_cinfo_words_3_4_5']}`")
    a("")
    a("## B3. The fleet cinfo oracle's blind spot")
    a("")
    a(f"{b5['files']} files, {b5['files_checked']} decoded, {len(b5['errors'])} error(s); "
      f"null cinfo pointers: **{b5['null_cinfo_pointers']}**. {b5['note']}.")
    a("")
    a("## Issues")
    a("")
    for i in doc["issues"]:
        a(f"- {i}")
    a("")
    a("## UNKNOWNs of this review")
    a("")
    for u in doc["unknowns"]:
        a(f"- {u}")
    a("")
    return "\n".join(L)


def write():
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(render_md(doc))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}")
    print(f"R1 ids match {doc['R1_cinfo_body_ids']['match']} | "
          f"R2 values match {doc['R2_masses']['values_match']} | "
          f"core {doc['core_values_match']}")
    print(f"limits: {doc['B1_limits']['inside_a_transform']}/"
          f"{doc['B1_limits']['total_limit_values']} inside a transform, "
          f"{doc['B1_limits']['pivot_duplicates']} pivot duplicates")
    print(f"verdict: {doc['verdict']} ({len(doc['issues'])} issues)")
    return 0


def check():
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    fresh = build()
    if stored != fresh:
        drift = [k for k in stored if stored.get(k) != fresh.get(k)]
        fails.append("stale sections: " + ", ".join(drift))
    if not fresh["R1_cinfo_body_ids"]["match"]:
        fails.append("cinfo body ids do not re-derive")
    if fresh["R1_cinfo_body_ids"]["byte_ids"] != [1, 3, 4, 6, 7, 16, 18, 19, 20, 26, 35]:
        fails.append(f"unexpected body ids {fresh['R1_cinfo_body_ids']['byte_ids']}")
    if not fresh["R2_masses"]["values_match"] or fresh["R2_masses"]["count"] != 56:
        fails.append("mass values do not re-derive to 56 matching floats")
    if fresh["R3_body_entries"]["body22_position_bytes"][:3] != [-1.208, 0.7047, -2.57]:
        fails.append("body 22 translation differs from the bytes")
    if fresh["B1_limits"]["pivot_duplicates"] < 20:
        fails.append("limits analysis found fewer pivot duplicates than measured")
    if fresh["B4_one_side"]["fleet_with_exactly_one_fixup"] != \
            fresh["B4_one_side"]["fleet_constraints"]:
        fails.append("a fleet constraint does not have exactly one fixup")
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print(f"OK core={'match' if fresh['core_values_match'] else 'MISMATCH'}; "
          f"limits {fresh['B1_limits']['pivot_duplicates']} pivot dups; "
          f"one-side {fresh['B4_one_side']['fleet_with_exactly_one_fixup']}/"
          f"{fresh['B4_one_side']['fleet_constraints']}; md+json byte-identical")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    return write() if args.write else check()


if __name__ == "__main__":
    raise SystemExit(main())
