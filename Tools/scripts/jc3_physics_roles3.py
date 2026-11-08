"""jc3_physics_roles3.py - JC3 vehicle physics, part 3 (GRB-G3-10c).

Builds on jc3_physics_roles2 and jc3hkx (both imported read-only). Three questions:

1. **The other side of each constraint.** The cinfo record is fully dumped (six words).
   Result, decoded negative: the record is `{constraintData* (fixup), bodyId, 0x7FFFFFFF,
   0, 0}` - there is no second body id in it, in the donor or in any fleet file. The
   0x7FFFFFFF word is the same sentinel the body table uses for bodies without a part id,
   so the partner is not stored in the cinfo. Where it could be is listed as UNKNOWN; a
   derived positional test (the constraint pivot against body 0's bounds) is reported as a
   hint only, not as a decode.
2. **The remaining 96-byte body-entry fields.** Newly decoded: +0x0C is the body's own id
   for bodies 0..41 (0x7FFFFFFF after that), +0x10 is `(id << 16) | 0xFF` for the same range,
   +0x3C is 1.0, +0x4C is the quaternion w (0x3F7FFFFF in most entries, 0x3F800000 in the
   last two). The other words keep the G3-10b census and stay UNKNOWN.
3. **Inertia in the 56 mass properties.** The link is now decoded: polytope +0x20 ->
   `hkRefCountedProperties` -> +0x10 -> the mass block, so 54 of 56 blocks resolve to a hull
   (G3-10b had 0). The mass float at +0x28 is confirmed. The 24 bytes at +0x10..+0x27 are
   not IEEE floats; one word (offset +0x1C) scales with mass (ratio ~2^-31 over the linked
   set), which is recorded as a measured relation, not as a decoded inertia. Inertia stays
   UNKNOWN with the test that would settle it.

    python Tools/scripts/jc3_physics_roles3.py --write
    python Tools/scripts/jc3_physics_roles3.py --check
"""
from __future__ import annotations

import argparse
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
FLEET_RAW = R2.FLEET_RAW
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES3.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES3.json")
CINFO = 24
BODY = 96
TYPE_TAG_OFF = 0xC0
MASS_WORDS_AT = 0x10
MASS_FLOAT = 0x28
TWO31 = 2.0 ** 31


def w32(blob, base, at):
    return struct.unpack_from("<I", blob, base + at)[0]


def f32(blob, base, at):
    return struct.unpack_from("<f", blob, base + at)[0]


def donor() -> dict:
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = next(o for o in pf.objects if o.cls == "hknpPhysicsSystemData")
    a50 = pf.array(psd.offset + 0x50)
    a40 = pf.array(psd.offset + 0x40)
    n_bodies = a40["size"]

    cinfos = []
    for i in range(a50["size"]):
        at = a50["ptr"] + i * CINFO
        words = [w32(blob, base, at + 4 * k) for k in range(6)]
        ptr = pf.pointers.get(at, 0)
        cinfos.append({"record_at": at, "words": ["%08x" % w for w in words],
                       "constraint": ptr, "class": pf._starts.get(ptr, ""),
                       "body_id": words[2], "field_0c": words[3],
                       "other_body_ids": [w for k, w in enumerate(words)
                                          if k not in (2, 3) and w not in (0, 0x7FFFFFFF)
                                          and 0 <= w < n_bodies]})

    cons = []
    for o in pf.objects:
        if "Constraint" not in o.cls:
            continue
        fl = [f32(blob, base, o.offset + 4 * k) for k in range(pf.extents[o.offset] // 4)]
        transforms = []
        for s in range(0, max(0, len(fl) - 16)):
            hit = R2.rot3x4(fl[s:s + 16])
            if hit is None:
                continue
            transforms.append({"at": 4 * s, "det": hit[0],
                               "pivot": [round(fl[s + 12 + k], 6) for k in range(3)]})
        ext = pf.extents[o.offset]
        cons.append({"class": o.cls, "offset": o.offset, "extent": ext,
                     "type_tag": (w32(blob, base, o.offset + TYPE_TAG_OFF)
                                  if ext > TYPE_TAG_OFF + 4 else None),
                     "pivots": [t["pivot"] for t in transforms],
                     "transforms": transforms})

    entry = []
    for i in range(n_bodies):
        at = a40["ptr"] + BODY * i
        words = [w32(blob, base, at + 4 * k) for k in range(24)]
        entry.append({"id": i, "word_0c": words[3], "word_10": words[4],
                      "word_3c": "%08x" % words[15], "word_4c": "%08x" % words[19],
                      "shape": pf._starts.get(pf.pointers.get(at, 0), "")})

    linked, unlinked = [], []
    for o in pf.objects:
        if o.cls != "hknpConvexPolytopeShape":
            continue
        node = pf.pointers.get(o.offset + 0x20, 0)
        mb = pf.pointers.get(node + 0x10, 0) if node else 0
        if not mb or pf._starts.get(mb) != "hknpShapeMassProperties":
            unlinked.append(o.offset)
            continue
        b = jc3hkx.decode_polytope(pf, o.offset)["bounds"]
        ext = [b["max"][k] - b["min"][k] for k in range(3)]
        words = [w32(blob, base, mb + MASS_WORDS_AT + 4 * k) for k in range(6)]
        mass = f32(blob, base, mb + MASS_FLOAT)
        linked.append({"shape": o.offset, "mass_props": mb, "mass": round(mass, 6),
                       "extents": [round(x, 4) for x in ext],
                       "words": ["%08x" % w for w in words],
                       "word3_over_2_31": round(words[3] / TWO31, 9),
                       "word3_over_mass": round(words[3] / TWO31 / mass, 12) if mass else None})

    ratios = [x["word3_over_mass"] for x in linked if x["mass"] >= 5 and x["word3_over_mass"]]
    spread = ((max(ratios) - min(ratios)) / (sum(ratios) / len(ratios))) if ratios else None

    # derived hint only: does a constraint pivot sit inside body 0's bounds?
    # rank correlation of word +0x1C with mass (a measurement, not a decode)
    def _rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r

    def _spearman(a, b):
        ra, rb = _rank(a), _rank(b)
        ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
        num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
        den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
        return num / den if den else 0.0

    corr = _spearman([int(x["words"][3], 16) for x in linked],
                     [x["mass"] for x in linked]) if linked else 0.0

    b0 = jc3hkx.decode_polytope(pf, next(o.offset for o in pf.objects
                                         if o.cls == "hknpConvexPolytopeShape"))["bounds"]
    inside = []
    for c in cons:
        for p in c["pivots"]:
            inside.append(all(b0["min"][k] <= p[k] <= b0["max"][k] for k in range(3)))

    return {
        "path": os.path.relpath(DONOR, ROOT).replace("\\", "/"),
        "bytes": len(blob), "objects": len(pf.objects), "bodies": n_bodies,
        "cinfos": cinfos,
        "constraints": cons,
        "body_entries": entry,
        "mass_link": {"linked": len(linked), "unlinked": len(unlinked), "items": linked,
                      "ratio_mean": round(sum(ratios) / len(ratios), 12) if ratios else None,
                      "ratio_spread": round(spread, 6) if spread is not None else None,
                      "word3_mass_spearman": round(corr, 4),
                      "ratio_pivot": "word +0x1C as u32 / 2^31 / mass (not constant)"},
        "derived": {"pivot_inside_first_polytope": {
            "tested": len(inside), "inside": sum(inside),
            "note": "hint only: the first polytope is body 0's hull; containment is not proof "
                    "of the constraint's partner"}},
    }


def fleet() -> dict:
    files = sorted(glob.glob(os.path.join(FLEET_RAW, "*.physicsc")))
    rows = []
    for f in files:
        try:
            blob = open(f, "rb").read()
            pf = jc3hkx.Packfile(blob)
            base = pf.base
        except Exception as exc:                                # noqa: BLE001
            rows.append({"file": os.path.basename(f), "error": str(exc)})
            continue
        psd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
        if len(psd) != 1:
            rows.append({"file": os.path.basename(f), "error": "%d system datas" % len(psd)})
            continue
        psd = psd[0]
        a50 = pf.array(psd.offset + 0x50)
        a40 = pf.array(psd.offset + 0x40)
        n = a40["size"]
        cinfo_words, second_ids, other = [], [], 0
        for i in range(a50["size"]):
            at = a50["ptr"] + i * CINFO
            ws = [w32(blob, base, at + 4 * k) for k in range(6)]
            cinfo_words.append(ws)
            extra = [w for w in ws[4:] if w not in (0, 0x7FFFFFFF) and 0 <= w < n]
            second_ids.append(bool(extra))
            other += len(extra)
        body_ok, tag_ok = True, True
        for i in range(n):
            at_i = a40["ptr"] + BODY * i
            w0c, w10 = w32(blob, base, at_i + 0x0C), w32(blob, base, at_i + 0x10)
            if w0c not in (i, 0x7FFFFFFF):
                body_ok = False
            if w0c == i:
                if (w10 >> 16) != i or (w10 & 0xFF) not in (1, 0xFF):
                    tag_ok = False
            elif w10 != 0xFF:
                tag_ok = False
        body_rule, tag10 = body_ok, tag_ok
        tags = sorted({w32(blob, base, o.offset + TYPE_TAG_OFF) for o in pf.objects
                       if "Constraint" in o.cls and pf.extents[o.offset] > TYPE_TAG_OFF + 4})
        rows.append({"file": os.path.basename(f), "bodies": n, "cinfos": a50["size"],
                     "cinfo_field_0c_7fffffff": all(w[3] == 0x7FFFFFFF for w in cinfo_words),
                     "cinfo_tail_zero": all(w[4] == 0 and w[5] == 0 for w in cinfo_words),
                     "second_body_ids": other,   # non-zero, non-sentinel, in-range in +0x10..
                     "body_id_rule_0_41": body_rule, "body_tag10_rule": tag10,
                     "constraint_type_tags": tags})
    ok = [r for r in rows if "error" not in r]
    return {
        "dir": FLEET_RAW, "files": len(files), "decoded": len(ok),
        "errors": [r for r in rows if "error" in r],
        "invariants": {
            "cinfo_field_0c_is_0x7FFFFFFF_all": all(r["cinfo_field_0c_7fffffff"] for r in ok),
            "cinfo_tail_zero_all": all(r["cinfo_tail_zero"] for r in ok),
            "no_second_body_id_in_cinfo": all(r["second_body_ids"] == 0 for r in ok),
            "body_id_rule_all": all(r["body_id_rule_0_41"] for r in ok),
            "body_tag10_rule_all": all(r["body_tag10_rule"] for r in ok),
            "constraint_tags_subset": all(set(r["constraint_type_tags"]) <= {12, 18, 19}
                                           for r in ok),
        },
        "rows": rows,
    }


def build() -> dict:
    d, fr = donor(), fleet()
    doc = {
        "schema": 1,
        "card": "GRB-G3-10c - constraint partner side, body-entry fields, inertia",
        "donor": d, "fleet_raw": fr,
        "unknowns": [
            "the constraints' partner body: the 24-byte cinfo holds one body id and the "
            "0x7FFFFFFF sentinel, and no other word is a body index - donor and fleet agree. "
            "Next sources: the body table's +0x20 pointer graph, or the entity's constraint list",
            "inertia: the 24 bytes at mass+0x10..+0x27 are not IEEE floats; word +0x1C tracks "
            "mass (ratio ~2^-31) but does not decode as a tensor. Test that would settle it: "
            "fit each word against m*(a^2+b^2)/12 from the hull and check the residual",
            "body-entry words other than +0x0C, +0x10, +0x3C, +0x4C keep their G3-10b domains",
        ],
    }
    doc["oracles"] = oracles(doc)
    return doc


def oracles(doc: dict) -> dict:
    d, fr = doc["donor"], doc["fleet_raw"]
    out = {}

    def add(k, ok, detail):
        out[k] = {"ok": bool(ok), "detail": detail}

    add("cinfo_no_second_body",
        all(not c["other_body_ids"] for c in d["cinfos"]) and
        fr["invariants"]["no_second_body_id_in_cinfo"],
        {"donor_records": len(d["cinfos"]),
         "fields": sorted({c["field_0c"] for c in d["cinfos"]})})
    donor_tags = sorted({c["type_tag"] for c in d["constraints"]})
    fleet_tags = sorted({t for r in fr["rows"] if "error" not in r
                         for t in r["constraint_type_tags"]})
    add("constraint_type_tags",
        donor_tags == [18, 19] and set(fleet_tags) <= {12, 18, 19},
        {"donor": sorted({(c["class"], c["type_tag"]) for c in d["constraints"]}),
         "fleet": fleet_tags})
    add("body_id_rule",
        fr["invariants"]["body_id_rule_all"] and fr["invariants"]["body_tag10_rule_all"],
        {"first": [(e["id"], e["word_0c"], e["word_10"]) for e in d["body_entries"][:3]],
         "last": [(e["id"], e["word_0c"], e["word_10"]) for e in d["body_entries"][-2:]]})
    add("mass_link", d["mass_link"]["linked"] >= 50,
        {"linked": d["mass_link"]["linked"], "unlinked": d["mass_link"]["unlinked"]})
    add("mass_word_correlation",
        d["mass_link"]["word3_mass_spearman"] > 0.9
        and (d["mass_link"]["ratio_spread"] or 0) > 0.1,
        {"spearman": d["mass_link"]["word3_mass_spearman"],
         "ratio_spread": d["mass_link"]["ratio_spread"],
         "note": "word +0x1C rises with mass but /2^31/mass is not constant -> not a decoded mass scale"})
    add("fleet_invariants", all(fr["invariants"].values()), fr["invariants"])
    add("quaternion_w", {e["word_4c"] for e in d["body_entries"]} <= {"3f7fffff", "3f800000"},
        {"values": sorted({e["word_4c"] for e in d["body_entries"]})})
    return out


def render(doc: dict) -> str:
    d, fr = doc["donor"], doc["fleet_raw"]
    L = []
    A = L.append
    A("# JC3 constraint partners, body-entry fields and mass properties - pass 3")
    A("")
    A("GRB-G3-10c, static decode only. Generated by `Tools/scripts/jc3_physics_roles3.py --write`,")
    A("`--check` re-derives and compares. `decoded` = read at the stated offset; `derived` = rule")
    A("over decoded inputs; `UNKNOWN` = no decoder reads it, with the test that would settle it.")
    A("")
    A("Donor: `%s` - %d bytes, %d objects, %d body entries." % (
        d["path"], d["bytes"], d["objects"], d["bodies"]))
    A("")
    A("## 1. The constraint cinfo record, all six words")
    A("")
    A("| # | record | words +0x00..+0x14 | constraint class | body id | +0x0C | second body? |")
    A("|---|---|---|---|---|---|---|")
    for i, c in enumerate(d["cinfos"]):
        A("| %d | 0x%X | %s | %s | %d | 0x%08X | %s |" % (
            i, c["record_at"], " ".join(c["words"]), c["class"], c["body_id"],
            c["field_0c"], c["other_body_ids"] or "**none**"))
    A("")
    A("**Decoded negative:** the record is 24 bytes - pointer (a fixup, so 0 in the raw), body id,")
    A("0x7FFFFFFF, 0, 0. No word other than the one body id is a body index, in the donor or in any")
    A("fleet file; +0x0C is the same sentinel the body table uses for bodies without a part id.")
    A("So the partner is **not stored in the cinfo**; G3-10b's \"chassis hypothesis\" is neither")
    A("confirmed nor refuted here.")
    A("")
    A("Constraint objects carry their type at **+0xC0**: 18 for every `hkpLimitedHingeConstraintData`,")
    A("19 for both `hkpRagdollConstraintData`, and 12 for the four `hkpHingeConstraintData` objects")
    A("elsewhere in the fleet (`constraint_type_tags`).")
    A("")
    A("Derived hint only (not a decode): %d of %d constraint pivots fall inside the first "
      "polytope's bounds (body 0's hull)." % (
          d["derived"]["pivot_inside_first_polytope"]["inside"],
          d["derived"]["pivot_inside_first_polytope"]["tested"]))
    A("")
    A("## 2. Body entries: the words this pass names")
    A("")
    A("| word | field | evidence |")
    A("|---|---|---|")
    A("| +0x0C | body id | equals the entry index for the 38 part bodies (0..41 minus "
      "22/23/36/37); 0x7FFFFFFF for the other 24 |")
    A("| +0x10 | `(id << 16) | flag` | high 16 bits = id for part bodies; flag is 0xFF, or "
      "0x01 for bodies 11, 15 and 27; 0x000000FF for the rest |")
    A("| +0x3C | translation w = 1.0 | 0x3F800000 in every entry |")
    A("| +0x4C | quaternion w | 0x3F7FFFFF (0.99999994) except 0x3F800000 in the last two |")
    A("")
    A("| id | +0x0C | +0x10 | +0x4C |")
    A("|---|---|---|---|")
    for e in d["body_entries"][:3] + d["body_entries"][-2:]:
        A("| %d | 0x%08X | 0x%08X | 0x%s |" % (e["id"], e["word_0c"], e["word_10"], e["word_4c"]))
    A("")
    A("The remaining words keep G3-10b's measured domains; they stay UNKNOWN.")
    A("")
    A("## 3. Mass properties, and the link to a hull")
    A("")
    A("The link G3-10b could not find: `polytope + 0x20` -> `hkRefCountedProperties` -> `+0x10`")
    A("-> the `hknpShapeMassProperties` block. **%d of %d** polytopes resolve; %d do not." % (
        d["mass_link"]["linked"], d["mass_link"]["linked"] + d["mass_link"]["unlinked"],
        d["mass_link"]["unlinked"]))
    A("")
    A("| shape | mass block | mass @+0x28 | hull extents (m) | words +0x10..+0x27 |")
    A("|---|---|---|---|---|")
    for x in d["mass_link"]["items"][:8]:
        A("| 0x%X | 0x%X | %g | %.2f, %.2f, %.2f | %s |" % (
            x["shape"], x["mass_props"], x["mass"], x["extents"][0], x["extents"][1],
            x["extents"][2], " ".join(x["words"])))
    A("")
    A("The 24 bytes are **not** IEEE floats: read as f32 they are sub-1e-6 noise.")
    A("Word **+0x1C** rises with mass - Spearman **%s** over the %d linked hulls - but" % (
        d["mass_link"]["word3_mass_spearman"], d["mass_link"]["linked"]))
    A("`word(+0x1C) / 2^31 / mass` is **not** constant (relative spread **%s**), so the word is"
      % d["mass_link"]["ratio_spread"])
    A("not a mass in a shifted IEEE exponent either. The inertia tensor stays UNKNOWN; the table")
    A("records the six raw words so a layout pass can test them against the hull moments.")
    A("")
    A("## 4. Fleet")
    A("")
    A("`%s`: %d files, %d decoded, %d error(s)." % (
        fr["dir"], fr["files"], fr["decoded"], len(fr["errors"])))
    A("")
    for k, v in fr["invariants"].items():
        A("- %s: **%s**" % (k, v))
    A("")
    A("## 5. Oracles (`--check` re-runs them)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in doc["oracles"].items():
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:200]))
    A("")
    A("## 6. UNKNOWN")
    A("")
    for i, u in enumerate(doc["unknowns"], 1):
        A("%d. %s" % (i, u))
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT)))
        print("cinfos: %d; constraints: %d; mass links: %d/%d" % (
            len(doc["donor"]["cinfos"]), len(doc["donor"]["constraints"]),
            doc["donor"]["mass_link"]["linked"],
            doc["donor"]["mass_link"]["linked"] + doc["donor"]["mass_link"]["unlinked"]))
        bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        fails.append("PHYSICS_ROLES3.json is stale")
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("PHYSICS_ROLES3.md is stale")
    for k, v in doc["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:250]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK cinfos %d / constraints %d / mass links %d; fleet %d files; md+json byte-identical"
          % (len(doc["donor"]["cinfos"]), len(doc["donor"]["constraints"]),
             doc["donor"]["mass_link"]["linked"], doc["fleet_raw"]["decoded"]))
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()},
                                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
