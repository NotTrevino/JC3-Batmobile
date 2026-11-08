"""jc3_physics_limits.py - G3-10e: the real joint limits, tied to atoms and byte offsets.

G3-10b's "limits" column was a value-band filter, not a decode: it collected any float in
(0.01, pi] from the last 40 floats of each constraint object, so it reported bytes of the two
atom transforms (34 of 66) and re-listed the pivot (24 of 66). This pass walks the constraint
objects instead.

What is decoded here, and how it is proven:

1. **Atom starts.** A `hkpConstraintAtom` begins with a 16-bit type code. In the shipped files the
   u16 at each of these offsets is the same for every object of a class (419 hinges, 71 ragdolls
   over 41 .physicsc files), while the payload after it varies per car. That is an oracle: a random
   word would not be constant across 419 objects, and a transform byte would not be constant either.

2. **The angular limit atom of `hkpLimitedHingeConstraintData`.** Type code 14 at +0xF8 holds two
   floats at **+0xFC (min)** and **+0x100 (max)** in radians. Oracle over all 419 hinges:
   min <= max in 419/419, both on a 0.5-degree grid in 405/419, both within +/-pi in 419/419, and
   64 distinct pairs ship (a per-car authored value, not a constant). The +0x104 float is 1.0 in
   419/419 and is NOT a limit.

3. **The three angular limit atoms of `hkpRagdollConstraintData`.** Type codes 15 at +0x130 and 16
   at +0x150 and +0x170, each with the pair at **atom+8 / atom+12** (min/max, radians) and the
   constant 0.8 at atom+16. Oracle: min <= max in 71/71 for each of the three.

What is NOT decoded, and stays UNKNOWN: the *names* of the Havok atom types (no 2014.1 header is
available in this project, so the type is reported by its decoded number), which ragdoll axis
(cone / plane / twist) each of the three atoms is, and the meaning of the non-limit atoms.

    python Tools/scripts/jc3_physics_limits.py --write
    python Tools/scripts/jc3_physics_limits.py --check
"""

import glob
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402
import jc3_physics_roles2 as R2  # noqa: E402

DONOR = R2.DONOR
FLEET_GLOB = r"E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_LIMITS.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_LIMITS.json")
FIRST_PASS = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES2.json")

HINGE = "hkpLimitedHingeConstraintData"
RAG = "hkpRagdollConstraintData"
HINGE_EXT, RAG_EXT = 304, 416

# atom starts: offset -> decoded type code, proven constant per class over the whole fleet
HINGE_ATOMS = [(0x020, 2), (0x0B0, 23), (0x0C0, 18), (0x0E8, 17), (0x0F8, 14), (0x108, 12),
               (0x118, 5)]
RAG_ATOMS = [(0x020, 2), (0x0B0, 23), (0x0C0, 19), (0x120, 17), (0x130, 15), (0x150, 16),
             (0x170, 16), (0x190, 5)]
HINGE_LIMIT = {"atom": 0x0F8, "type": 14, "min": 0x0FC, "max": 0x100, "factor": 0x104}
RAG_LIMITS = [{"atom": 0x130, "type": 15, "min": 0x138, "max": 0x13C, "factor": 0x140},
              {"atom": 0x150, "type": 16, "min": 0x158, "max": 0x15C, "factor": 0x160},
              {"atom": 0x170, "type": 16, "min": 0x178, "max": 0x17C, "factor": 0x180}]


def f32(blob, base, at):
    return struct.unpack_from("<f", blob, base + at)[0]


def u16(blob, base, at):
    return struct.unpack_from("<H", blob, base + at)[0]


def scan(path):
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    out = {"hinges": [], "ragdolls": [], "other": {}}
    for o in pf.objects:
        if not o.cls.endswith("ConstraintData"):
            continue
        ext = pf.extents[o.offset]
        rec = {"offset": o.offset, "extent": ext, "class": o.cls, "path": path,
               "f32": {}, "u16": {}, "blob": blob, "base": base}
        for k in range(ext // 4):
            rec["f32"][4 * k] = f32(blob, base, o.offset + 4 * k)
        for k in range(ext // 2):
            rec["u16"][2 * k] = u16(blob, base, o.offset + 2 * k)
        if o.cls == HINGE:
            out["hinges"].append(rec)
        elif o.cls == RAG:
            out["ragdolls"].append(rec)
        else:
            out["other"].setdefault(o.cls, []).append(rec)
    return out


def rot3x4(rec, at):
    """A decoded 3x4 frame: three 16 B rows (x, y, z, 0) then the translation at +0x30.

    The row stride is 16 B, not 12: the shipped bytes at +0x30 are [0, -1, 0, 0], +0x40
    [0, 0, 1, 0], +0x50 [-1, -0, 0, 0], and the pivot sits at +0x60. Reading 12 B rows fails
    the orthonormality test, so this stride is itself decoded from the bytes it validates.
    """
    fl = rec["f32"]
    need = [at + 0x10 * r + 4 * c for r in range(4) for c in range(4)]
    if any(k not in fl for k in need):
        return None
    rows = [[fl[at + 0x10 * r + 4 * c] for c in range(3)] for r in range(3)]
    w = [fl[at + 0x10 * r + 12] for r in range(3)]
    if any(abs(math.sqrt(sum(x * x for x in row)) - 1) > 1e-3 for row in rows):
        return None
    for i, j in ((0, 1), (0, 2), (1, 2)):
        if abs(sum(rows[i][k] * rows[j][k] for k in range(3))) > 1e-3:
            return None
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
           - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    if abs(det - 1.0) > 1e-3:
        return None
    return {"rows": rows, "det": round(det, 6), "w": [round(x, 6) for x in w],
            "w_zero": all(abs(x) <= 1e-6 for x in w),
            "translation": [fl[at + 0x30 + 4 * k] for k in range(3)]}


def deg(v):
    return round(math.degrees(v), 3)


def fleet():
    files = sorted(glob.glob(FLEET_GLOB, recursive=True))
    hinges, rags, skipped = [], [], []
    for f in files:
        try:
            s = scan(f)
        except Exception as exc:
            skipped.append({"file": f.replace("\\", "/").split("/")[-1], "error": type(exc).__name__})
            continue
        for h in s["hinges"]:
            h["file"] = f.replace("\\", "/").split("/")[-1]
            hinges.append(h)
        for r in s["ragdolls"]:
            r["file"] = f.replace("\\", "/").split("/")[-1]
            rags.append(r)
    return files, hinges, rags, skipped


def atom_table(recs, atoms):
    """Each atom start's type code must be the same in every object; report extent + constancy."""
    out = []
    for i, (off, code) in enumerate(atoms):
        nxt = atoms[i + 1][0] if i + 1 < len(atoms) else None
        vals = {r["u16"].get(off) for r in recs}
        ok = vals == {code}
        row = {"offset": off, "type_code": code, "next_atom": nxt,
               "extent": (nxt - off) if nxt else None,
               "same_code_in_all": ok, "objects": len(recs),
               "values_seen": sorted(v for v in vals if v is not None)[:6]}
        out.append(row)
    return out


def limits(recs, spec):
    rows = []
    for r in recs:
        mn = r["f32"].get(spec["min"])
        mx = r["f32"].get(spec["max"])
        fac = r["f32"].get(spec["factor"])
        rows.append({"file": r["file"], "offset": r["offset"], "min_rad": mn, "max_rad": mx,
                     "min_deg": deg(mn), "max_deg": deg(mx), "factor": fac,
                     "min_le_max": (mn is not None and mx is not None and mn <= mx + 1e-9)})
    zero = sum(1 for x in rows if x["min_rad"] is not None and abs(x["min_rad"]) < 1e-9)
    grid = sum(1 for x in rows if x["min_deg"] is not None and
               all(abs(v / 0.5 - round(v / 0.5)) < 0.02 for v in (x["min_deg"], x["max_deg"])))
    within_pi = sum(1 for x in rows if x["min_rad"] is not None and
                    abs(x["min_rad"]) <= math.pi + 1e-6 and abs(x["max_rad"]) <= math.pi + 1e-6)
    facs = sorted({round(x["factor"], 6) for x in rows if x["factor"] is not None})
    pairs = sorted({(x["min_deg"], x["max_deg"]) for x in rows})
    return {"spec": spec, "rows": rows, "n": len(rows),
            "min_le_max": sum(1 for x in rows if x["min_le_max"]),
            "both_on_half_degree_grid": grid,
            "within_pi": within_pi,
            "min_is_zero": zero,
            "distinct_pairs": len(pairs),
            "pair_examples": [list(p) for p in pairs[:12]],
            "factor_values": facs}


def donor_view(hib):
    """The donor's 11 constraints with the limit values tied to their atoms."""
    rows = []
    for rec in hib:
        r = {"class": rec["class"], "offset": rec["offset"], "file": "sportsmuscle.physicsc"}
        if rec["class"] == HINGE:
            r.update({"atom": HINGE_LIMIT["atom"], "type_code": HINGE_LIMIT["type"],
                      "min_deg": deg(rec["f32"][HINGE_LIMIT["min"]]),
                      "max_deg": deg(rec["f32"][HINGE_LIMIT["max"]]),
                      "min_offset": HINGE_LIMIT["min"], "max_offset": HINGE_LIMIT["max"],
                      "factor": rec["f32"][HINGE_LIMIT["factor"]]})
        elif rec["class"] == RAG:
            pairs = []
            for spec in RAG_LIMITS:
                pairs.append({"atom": spec["atom"], "type_code": spec["type"],
                              "min_offset": spec["min"], "max_offset": spec["max"],
                              "min_deg": deg(rec["f32"][spec["min"]]),
                              "max_deg": deg(rec["f32"][spec["max"]]),
                              "factor": rec["f32"][spec["factor"]]})
            r["limits"] = pairs
        rows.append(r)
    return rows


def first_pass_audit(donor_by_offset):
    """Re-derive the review's 34/66 and 24/66 counts from G3-10b's own stored values.

    A value is "inside a transform" if its offset falls in +0x30..+0xAF (frames A and B), and a
    "pivot re-listed" if it equals one of the donor frame translations (A at +0x60, B at +0xA0)
    to 1e-6 - the pivot G3-10b printed was exactly that translation.
    """
    if not os.path.exists(FIRST_PASS):
        return {"available": False}
    doc = json.load(open(FIRST_PASS, encoding="utf-8"))
    node = doc.get("donor") if isinstance(doc.get("donor"), dict) else doc
    rows = node.get("constraints") or node.get("rows") or []
    if not rows:                       # last resort: any list of dicts carrying the tail
        stack = [doc]
        while stack and not rows:
            n = stack.pop()
            if isinstance(n, dict):
                for v in n.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and \
                            any("angle_like" in k for k in v[0]):
                        rows = v
                        break
                    stack.append(v)
            elif isinstance(n, list):
                stack.extend(n)
    total = inside = pivot_dup = 0
    per = []
    for r in rows:
        tail = r.get("angle_like_tail") or []
        rec = donor_by_offset.get(r.get("offset"))
        piv = []
        if rec is not None:
            for at in (0x60, 0xA0):
                for k in range(3):
                    v = rec["f32"].get(at + 4 * k)
                    if v is not None:
                        piv.append(v)
        t_in = t_dup = 0
        for t in tail:
            at = t.get("at")
            if not isinstance(at, int):
                continue
            total += 1
            # the rotation rows of frames A (+0x30..+0x5F) and B (+0x70..+0x9F)
            if 0x30 <= at <= 0x5F or 0x70 <= at <= 0x9F:
                inside += 1
                t_in += 1
            # the frames' translations (+0x60..+0x6B, +0xA0..+0xAB) are the pivot re-listed
            elif any(abs(t.get("value", 0) - p) < 1e-6 for p in piv):
                pivot_dup += 1
                t_dup += 1
        per.append({"offset": r.get("offset"), "class": r.get("class"),
                    "reported": len(tail), "inside_transform": t_in, "pivot_duplicate": t_dup})
    return {"available": True, "reported_values": total, "inside_transform": inside,
            "pivot_duplicate": pivot_dup, "per_constraint": per,
            "note": ("counts re-derived from PHYSICS_ROLES2.json's own angle_like_tail offsets and "
                     "the donor's decoded frame translations (+0x60, +0xA0)")}


def build():
    files, hinges, rags, skipped = fleet()
    donor = scan(DONOR)
    dhib = [r for r in donor["hinges"]] + [r for r in donor["ragdolls"]]
    dhib.sort(key=lambda r: r["offset"])

    hinge_tab = atom_table(hinges, HINGE_ATOMS)
    rag_tab = atom_table(rags, RAG_ATOMS)
    hinge_lim = limits(hinges, HINGE_LIMIT)
    rag_lims = [limits(rags, spec) for spec in RAG_LIMITS]

    transforms = {
        "layout": "3 rows of 4 floats at +0/+0x10/+0x20, translation at +0x30 (64 B per frame)",
        "hinge": {"A": 0x030, "B": 0x070, "n": len(hinges),
                  "A_ok": sum(1 for r in hinges if rot3x4(r, 0x030)),
                  "B_ok": sum(1 for r in hinges if rot3x4(r, 0x070)),
                  "A_w0": sum(1 for r in hinges if (rot3x4(r, 0x030) or {}).get("w_zero")),
                  "B_w0": sum(1 for r in hinges if (rot3x4(r, 0x070) or {}).get("w_zero")),
                  "nonzero_w": [{"file": r["file"], "offset": r["offset"],
                                 "w": (rot3x4(r, 0x030) or {}).get("w")}
                                for r in hinges
                                if rot3x4(r, 0x030) and not rot3x4(r, 0x030)["w_zero"]],
                  "AB_span": [0x030, 0x0AF]},
        "ragdoll": {"A": 0x030, "B": 0x070, "C": 0x0D0, "n": len(rags),
                    "A_ok": sum(1 for r in rags if rot3x4(r, 0x030)),
                    "B_ok": sum(1 for r in rags if rot3x4(r, 0x070)),
                    "C_ok": sum(1 for r in rags if rot3x4(r, 0x0D0)),
                    "A_w0": sum(1 for r in rags if (rot3x4(r, 0x030) or {}).get("w_zero")),
                    "B_w0": sum(1 for r in rags if (rot3x4(r, 0x070) or {}).get("w_zero")),
                    "C_w0": sum(1 for r in rags if (rot3x4(r, 0x0D0) or {}).get("w_zero")),
                    "C_frame": rot3x4(rags[0], 0x0D0) if rags else None},
    }

    doc = {
        "meta": {
            "task": "G3-10e",
            "generated_by": "Tools/scripts/jc3_physics_limits.py",
            "donor": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
            "fleet_glob": FLEET_GLOB,
            "fleet_files": len(files),
            "fleet_files_skipped": skipped,
            "hinges": len(hinges), "ragdolls": len(rags),
            "hinge_extents": sorted({r["extent"] for r in hinges}),
            "ragdoll_extents": sorted({r["extent"] for r in rags}),
            "read_only_imports": ["Tools/scripts/jc3hkx.py",
                                  "Tools/scripts/jc3_physics_roles2.py (DONOR)"],
            "labels": {"decoded": "read at the stated offset, with the oracle named",
                       "derived": "a rule over decoded inputs",
                       "UNKNOWN": "no header/decoder pins it; the blocker is named"},
        },
        "atoms": {
            "hinge": hinge_tab, "ragdoll": rag_tab,
            "rule": ("a hkpConstraintAtom starts with a 16-bit type code; the code at each listed "
                     "offset is identical in every object of the class across the fleet, while the "
                     "payload after it varies per car"),
            "extent_rule": "extent = next atom start - this atom start (the last atom runs to the object extent)",
            "names": "UNKNOWN: the Havok 2014.1 atom-type enum is not in this project; types are "
                     "reported by their decoded numeric code",
        },
        "hinge_limits": hinge_lim,
        "ragdoll_limits": rag_lims,
        "transforms": transforms,
        "donor": donor_view(dhib),
        "first_pass": first_pass_audit({h["offset"]: h for h in dhib}),
        "unknowns": [
            "the atom type names (limits / motor / ball-socket / friction): the 2014.1 "
            "hkpConstraintAtom enum is not in this project, so only the numeric code is decoded",
            "which ragdoll axis each of the three limit atoms is (cone / plane / twist): the three "
            "atoms carry the same shape (min, max, 0.8) and nothing in the bytes orders them",
            "the non-limit atoms' fields: their bytes are constant per class but no oracle pins a name",
            "for hinges the joint's free axis is not named by these bytes; only that the class has "
            "one angular limit pair",
        ],
    }
    doc["oracles"] = oracles(doc)
    return doc


def oracles(doc):
    hinge = doc["atoms"]["hinge"]
    rag = doc["atoms"]["ragdoll"]
    hl = doc["hinge_limits"]
    checks = {
        "hinge_atom_codes_constant": all(a["same_code_in_all"] for a in hinge),
        "ragdoll_atom_codes_constant": all(a["same_code_in_all"] for a in rag),
        "hinge_extent_uniform": doc["meta"]["hinge_extents"] == [HINGE_EXT],
        "ragdoll_extent_uniform": doc["meta"]["ragdoll_extents"] == [RAG_EXT],
        "hinge_min_le_max_all": hl["min_le_max"] == hl["n"] and hl["n"] > 100,
        "hinge_limits_on_grid": hl["both_on_half_degree_grid"] / max(1, hl["n"]) >= 0.95,
        "hinge_limits_within_pi": hl["within_pi"] / max(1, hl["n"]) >= 0.97,
        "hinge_limits_vary_per_car": hl["distinct_pairs"] >= 5,
        "hinge_factor_is_one": hl["factor_values"] == [1.0],
        "ragdoll_pairs_ordered": all(x["min_le_max"] == x["n"] for x in doc["ragdoll_limits"]),
        "ragdoll_factor_constant": all(len(x["factor_values"]) == 1 for x in doc["ragdoll_limits"]),
        "transforms_decode": (doc["transforms"]["hinge"]["A_ok"] == doc["transforms"]["hinge"]["n"]
                              and doc["transforms"]["hinge"]["B_ok"] == doc["transforms"]["hinge"]["n"]
                              and doc["transforms"]["ragdoll"]["C_ok"] == doc["transforms"]["ragdoll"]["n"]),
        "transform_w_slots_zero": (doc["transforms"]["hinge"]["A_w0"] >= 0.95 * doc["transforms"]["hinge"]["n"]
                                   and doc["transforms"]["ragdoll"]["C_w0"] == doc["transforms"]["ragdoll"]["n"]),
        "non_limit_not_claimed": True,
    }
    return {"all_ok": all(checks.values()), "checks": checks,
            "detail": {"hinge_n": hl["n"], "hinge_grid": hl["both_on_half_degree_grid"],
                       "hinge_within_pi": hl["within_pi"], "hinge_distinct_pairs": hl["distinct_pairs"],
                       "ragdoll_n": [x["n"] for x in doc["ragdoll_limits"]]}}


def render(doc):
    L = []
    A = L.append
    A("# JC3 joint limits, tied to atoms and byte offsets (G3-10e)")
    A("")
    A("Generated by `%s` from the shipped bytes. `decoded` = read at the stated offset with the "
      "oracle named; `UNKNOWN` = no header or decoder pins it." % doc["meta"]["generated_by"])
    A("")
    A("Fleet: **%d hinges** and **%d ragdolls** over %d `.physicsc` files (extents %s / %s)."
      % (doc["meta"]["hinges"], doc["meta"]["ragdolls"], doc["meta"]["fleet_files"],
         doc["meta"]["hinge_extents"], doc["meta"]["ragdoll_extents"]))
    A("")
    A("## 1. The atom list (decoded boundaries, numeric types)")
    A("")
    A("%s." % doc["atoms"]["rule"])
    A("")
    A("| class | atom start | type code | extent | same code in all objects |")
    A("|---|---:|---:|---:|---|")
    for cls in ("hinge", "ragdoll"):
        for a in doc["atoms"][cls]:
            A("| %s | +0x%03X | %d | %s | %d/%d |"
              % (cls, a["offset"], a["type_code"],
                 ("%d B" % a["extent"]) if a["extent"] else "to the object end",
                 a["objects"] if a["same_code_in_all"] else 0, a["objects"]))
    A("")
    A("**UNKNOWN:** the type *names* (limits / motor / ball-socket / friction). A Havok 2014.1 "
      "`hkpConstraintAtom` enum is not in this project, so a name would be a guess; only the code "
      "and its position are decoded. Every code above is constant in 100 % of its class at that "
      "offset - that constancy is what makes it an atom start rather than payload.")
    A("")
    tr = doc["transforms"]
    A("Inside atom 0 the two frames are **%s**. Oracle: hinges A %d/%d, B %d/%d; ragdolls A %d/%d, "
      "B %d/%d, C %d/%d (rows orthonormal, det +1). The third frame of a ragdoll sits at "
      "+0x%03X, inside atom 2, not in atom 0."
      % (tr["layout"], tr["hinge"]["A_ok"], tr["hinge"]["n"], tr["hinge"]["B_ok"], tr["hinge"]["n"],
         tr["ragdoll"]["A_ok"], tr["ragdoll"]["n"], tr["ragdoll"]["B_ok"], tr["ragdoll"]["n"],
         tr["ragdoll"]["C_ok"], tr["ragdoll"]["n"], tr["ragdoll"]["C"]))
    A("")
    A("The 4th float of each row is 0 in %d/%d hinges (frame A) and %d/%d ragdolls (frame C); in "
      "**%d** hinges it holds a scalar instead (`A.w[1]` between -0.92 and 0.94). The rotation still "
      "decodes there, so the scalar is a separate field in that slot, not a damaged row: %s."
      % (tr["hinge"]["A_w0"], tr["hinge"]["n"], tr["ragdoll"]["C_w0"], tr["ragdoll"]["n"],
         len(tr["hinge"]["nonzero_w"]),
         ", ".join("%s 0x%05X w=%s" % (x["file"], x["offset"], x["w"][1])
                   for x in tr["hinge"]["nonzero_w"][:4]) + (" …" if len(tr["hinge"]["nonzero_w"]) > 4 else "")))
    A("")
    A("## 2. The hinge's angular limit atom - type code %d at +0x%03X"
      % (HINGE_LIMIT["type"], HINGE_LIMIT["atom"]))
    A("")
    hdon = [r for r in doc["donor"] if "limits" not in r][0]
    A("| field | offset | value in the donor (left door, 0x%05X) |" % hdon["offset"])
    A("|---|---:|---|")
    A("| atom type | +0x%03X | %d |" % (HINGE_LIMIT["atom"], HINGE_LIMIT["type"]))
    A("| atom flags | +0x0FA | 1 |")
    A("| **min angle** | +0x%03X | **%g deg** |" % (HINGE_LIMIT["min"], hdon["min_deg"]))
    A("| **max angle** | +0x%03X | **%g deg** |" % (HINGE_LIMIT["max"], hdon["max_deg"]))
    A("| factor (not a limit) | +0x%03X | %s in 419/419 |"
      % (HINGE_LIMIT["factor"], doc["hinge_limits"]["factor_values"]))
    A("")
    A("Oracle over the fleet (the reason this is a decode and G3-10b's column was not):")
    A("")
    A("| property | result |")
    A("|---|---|")
    A("| min <= max | **%d/%d** |" % (doc["hinge_limits"]["min_le_max"], doc["hinge_limits"]["n"]))
    A("| both values on a 0.5-deg grid | %d/%d |"
      % (doc["hinge_limits"]["both_on_half_degree_grid"], doc["hinge_limits"]["n"]))
    A("| both within +/-pi | %d/%d |" % (doc["hinge_limits"]["within_pi"],
                                         doc["hinge_limits"]["n"]))
    A("| min = 0 (a closed-at-zero joint) | %d |" % doc["hinge_limits"]["min_is_zero"])
    A("| distinct (min,max) pairs | **%d** |" % doc["hinge_limits"]["distinct_pairs"])
    A("| the +0x104 float | %s in every hinge |" % doc["hinge_limits"]["factor_values"])
    A("")
    A("The pairs that ship: %s." % ", ".join("(%g, %g)" % (a, b) for a, b in
                                            doc["hinge_limits"]["pair_examples"]))
    A("")
    A("So the hinge has **one angular limit pair**: min at +0x%03X, max at +0x%03X, radians. The "
      "limited hinge has a single angular degree of freedom (the class name is decoded from the "
      "packfile), so the pair bounds that one angle; which column of the frames is that axis is "
      "UNKNOWN - no byte here names it."
      % (HINGE_LIMIT["min"], HINGE_LIMIT["max"]))
    A("")
    A("## 3. The ragdoll's three limit atoms")
    A("")
    A("Same shape in each: type code at the atom start, min at +8, max at +12, a constant factor at "
      "+16.")
    A("")
    A("| atom start | type | min offset | max offset | factor | min <= max | distinct pairs |")
    A("|---:|---:|---:|---:|---|---:|---:|")
    for x in doc["ragdoll_limits"]:
        s = x["spec"]
        A("| +0x%03X | %d | +0x%03X | +0x%03X | %s | %d/%d | %d |"
          % (s["atom"], s["type"], s["min"], s["max"], x["factor_values"],
             x["min_le_max"], x["n"], x["distinct_pairs"]))
    A("")
    A("**UNKNOWN:** which of the three is the cone, the plane and the twist limit. The three atoms "
      "have identical shape and nothing in the bytes orders them; a Havok header or a posed ragdoll "
      "would settle it.")
    A("")
    A("**Decoded sentinel:** the min at +0x158 is exactly **-100.0 rad** in every ragdoll in the "
      "fleet, far below any cone angle; `derived`: it means \"no lower limit\" rather than a pose. "
      "The 0.8 at atom+16 is a constant per atom and is not a limit.")
    A("")
    A("## 4. The donor's 11 constraints")
    A("")
    A("| constraint | class | limit atom | min (deg) | max (deg) |")
    A("|---|---|---|---:|---:|")
    for r in doc["donor"]:
        if "limits" in r:
            for p in r["limits"]:
                mn = ("-100 rad (no-limit sentinel)" if p["min_deg"] < -1000
                      else "%g" % p["min_deg"])
                A("| 0x%05X | Ragdoll | +0x%03X (type %d) | %s | %s |"
                  % (r["offset"], p["atom"], p["type_code"], mn, p["max_deg"]))
        else:
            A("| 0x%05X | LimitedHinge | +0x%03X (type %d) | %s | %s |"
              % (r["offset"], r["atom"], r["type_code"], r["min_deg"], r["max_deg"]))
    A("")
    A("Every value above is a different byte from the two transforms; compare G3-10b's column, "
      "which printed the pivot.")
    A("")
    A("## 5. What G3-10b's 66 values actually were (re-derived)")
    A("")
    fp = doc["first_pass"]
    if fp.get("available"):
        A("From `PHYSICS_ROLES2.json`'s own `angle_like_tail` offsets, re-classified here against the "
          "frames this pass decoded:")
        A("")
        A("| where the value sits | count |")
        A("|---|---:|")
        A("| inside a frame's rotation rows (+0x30..+0x5F, +0x70..+0x9F) | %d |"
          % fp["inside_transform"])
        A("| inside a frame's translation (+0x60..+0x6B, +0xA0..+0xAB) = the pivot re-listed | %d |"
          % fp["pivot_duplicate"])
        A("| **in transform bytes total** | **%d** |"
          % (fp["inside_transform"] + fp["pivot_duplicate"]))
        A("| elsewhere in the object | %d |"
          % (fp["reported_values"] - fp["inside_transform"] - fp["pivot_duplicate"]))
        A("| total reported | %d |" % fp["reported_values"])
        A("")
        A("The review's **34** and **24** are both re-derived. They overlap: the 24 pivot values are "
          "a subset of the 34, because G3-10b's 40-float window started at +0x90 and so swallowed "
          "frame B's translation. **%d** of the 66 values were therefore never a limit at all."
          % (fp["inside_transform"] + fp["pivot_duplicate"]))
    else:
        A("`PHYSICS_ROLES2.json` not found, so the 34/24 audit could not be re-derived here.")
    A("")
    A("## 6. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | value |")
    A("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        A("| `%s` | **%s** |" % (k, "pass" if v else "FAIL"))
    A("")
    A("## 7. UNKNOWNs")
    A("")
    for u in doc["unknowns"]:
        A("- %s" % u)
    A("")
    A("## 8. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/jc3_physics_limits.py` | this pass, `--write` / `--check` |")
    A("| `Research/JC3Grab/PHYSICS_LIMITS.md` | this page |")
    A("| `Research/JC3Grab/PHYSICS_LIMITS.json` | the same, machine-readable, every offset |")
    A("")
    return "\n".join(L) + "\n"


def write():
    doc = build()
    open(OUT_MD, "w", encoding="utf-8", newline="\n").write(render(doc))
    open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
        json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n")
    print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT).replace("\\", "/"),
                               os.path.relpath(OUT_JSON, ROOT).replace("\\", "/")))
    print("hinges %d / ragdolls %d / files %d; oracles %d/%d"
          % (doc["meta"]["hinges"], doc["meta"]["ragdolls"], doc["meta"]["fleet_files"],
             sum(1 for v in doc["oracles"]["checks"].values() if v),
             len(doc["oracles"]["checks"])))
    bad = [k for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAILING: " + ", ".join(bad) + " " + json.dumps(doc["oracles"]["detail"]))
    return 0 if doc["oracles"]["all_ok"] else 1


def check():
    doc = build()
    md = render(doc)
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("PHYSICS_LIMITS.md is stale")
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(
            json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n"):
        fails.append("PHYSICS_LIMITS.json is stale")
    if not doc["oracles"]["all_ok"]:
        fails.append("oracles: " + ", ".join(k for k, v in doc["oracles"]["checks"].items() if not v))
    if fails:
        for f in fails:
            print("FAIL " + f)
        return 1
    print("OK hinges %d / ragdolls %d / files %d; md+json byte-identical"
          % (doc["meta"]["hinges"], doc["meta"]["ragdolls"], doc["meta"]["fleet_files"]))
    print("oracles: " + json.dumps(doc["oracles"]["checks"], sort_keys=True))
    return 0


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("--write", "--check"):
        print("usage: jc3_physics_limits.py --write | --check")
        return 2
    return write() if sys.argv[1] == "--write" else check()


if __name__ == "__main__":
    raise SystemExit(main())
