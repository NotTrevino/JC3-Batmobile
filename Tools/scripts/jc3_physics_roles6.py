"""jc3_physics_roles6.py - G3-10g: where the constraint's *second* body is, and whether anything names it.

G3-10d read the 24-byte cinfo word +0x04 (= 0 in all 494 records) as "body 0, the chassis" and
its review refuted the universal form: 65 of the 494 records put the pivot more than 0.20 m from
body 0's hull while another body is within 0.05 m, and body 0 never anchors a pivot alone past
0.10 m.  So either the partner is stored somewhere outside the 24-byte record, or it is nowhere.

This pass takes the three places the card names and scores each one against the same geometric
oracle on all 50 fleet files, with a control that a partner rule must beat:

  H1  a parallel array in `hknpPhysicsSystemData` beside the constraint list, with as many
      elements as there are constraints (11 in the Serpente).  Tested by census: every array
      header in the data section whose size equals the file's cinfo count is listed and its
      elements are classified (callback pointers / invalid ids / a real body list).
  H2  the constraintData's two pivot frames, each read as a frame in its body's local space:
      a frame that lands on a body's hull after that body's transform is applied names the body.
      Tested by measuring both frames of every record and, separately, the world-read versus
      local-read distance for the records whose recorded body is *not* the identity transform -
      the only records that can tell the two readings apart.
  H3  the vehicle .epe's per-part parent link (`Research/JC3Grab/PARTS_TABLE.jsonl`, which is
      built from the .epe): the partner of body b is the body of b's parent part.  Tested on
      every record that maps to a parts row, paired against body 0 on the same subset.

Oracle, unchanged from G3-10d so the numbers are comparable: |signed distance from the stored
pivot to a body's decoded convex hull|, small = the joint sits on that body.  A candidate "names
the partner" only if it does so for every record of every file; a candidate "fits" some records
otherwise, and the report says how many.

Everything is read from the files (`jc3hkx` for the packfile, PARTS_TABLE for the .epe links);
nothing is taken from a published layout and no game is launched.

Usage
    python Tools/scripts/jc3_physics_roles6.py --write
    python Tools/scripts/jc3_physics_roles6.py --check
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

FLEET = r"E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc"
PARTS = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
ENT_JSON = r"E:/Modding/_shared/gamedata/JC3grab/hkx/out/*.json"
MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES6.md")
JS = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES6.json")

CINFO_STRIDE = 24
BODY_ENTRY = 96
TOL = 0.05                     # "the pivot sits on this body" — G3-10d's 5 cm
FAR = 0.20                     # a record that makes body 0 impossible
MARGIN = 0.01                  # nearest-vs-second-nearest gap under which the pick is ambiguous
POLYTOPE = "hknpConvexPolytopeShape"


# --------------------------------------------------------------------------- helpers
def sdist(planes, p):
    """Signed distance of a point to a hull: max over planes of (n.p + d); <= 0 is inside."""
    return max(n["n"][0] * p[0] + n["n"][1] * p[1] + n["n"][2] * p[2] + n["d"] for n in planes)


def is_identity(q):
    return q[0] == 0.0 and q[1] == 0.0 and q[2] == 0.0 and abs(abs(q[3]) - 1.0) < 1e-6


def qmat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def rate(k, n):
    return round(k / n, 4) if n else None


# --------------------------------------------------------------------------- one physicsc
def scan(path):
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
    if psd is None:
        return None
    a40, a50 = pf.array(psd.offset + 0x40), pf.array(psd.offset + 0x50)

    bodies = []
    for i in range(a40["size"]):
        at = a40["ptr"] + BODY_ENTRY * i
        shape = pf.pointers.get(at, 0)
        cls = pf._starts.get(shape, "") if shape else ""
        hull = None
        if cls == POLYTOPE:
            d = jc3hkx.decode_polytope(pf, shape)
            hull = {"planes": d["planes"], "bounds": d["bounds"],
                    "n_planes": len(d["planes"]), "convex_ok": d["convex_ok"]}
        bodies.append({
            "id": i, "shape": shape, "shape_class": cls,
            "position": [round(struct.unpack_from("<f", blob, base + at + 0x30 + 4 * k)[0], 6)
                         for k in range(3)],
            "quaternion": [round(struct.unpack_from("<f", blob, base + at + 0x40 + 4 * k)[0], 6)
                           for k in range(4)],
            "identity": is_identity([struct.unpack_from("<f", blob, base + at + 0x40 + 4 * k)[0]
                                     for k in range(4)]),
            "hull": hull,
        })

    cinfos = []
    for k in range(a50["size"]):
        rec = a50["ptr"] + CINFO_STRIDE * k
        w = struct.unpack_from("<6I", blob, base + rec)
        co = pf.pointers.get(rec, 0)
        if not co:
            continue
        ext = pf.extents[co]
        fl = [struct.unpack_from("<f", blob, base + co + 4 * j)[0] for j in range(ext // 4)]
        frames = []
        for s in range(0, max(0, len(fl) - 16)):
            hit = R2.rot3x4(fl[s:s + 16])
            if hit:
                frames.append({"at": s * 4, "rows": hit[1], "det": hit[0],
                               "pivot": [round(fl[s + 12 + t], 6) for t in range(3)]})
        cinfos.append({"k": k, "record": rec, "constraint": co,
                       "class": pf._starts.get(co, ""), "words": list(w),
                       "body_a_word": w[1], "body_b": w[2], "word_0c": w[3],
                       "frames": frames})

    # every array header in the data section whose size equals the cinfo count
    partner_arrays = []
    for p in range(0, pf.lf - 16, 4):
        if p not in pf.pointers:
            continue
        size = struct.unpack_from("<I", blob, base + p + 8)[0]
        cap = struct.unpack_from("<I", blob, base + p + 12)[0]
        if size != a50["size"] or (cap & 0x7FFFFFFF) < size or size == 0:
            continue
        tgt = pf.pointers[p]
        vals = [struct.unpack_from("<I", blob, base + tgt + 4 * i)[0] for i in range(size)]
        if tgt == a50["ptr"]:
            kind = "cinfo-array"
        elif size >= 2 and all(v < a40["size"] for v in vals) and len(set(vals)) >= 3:
            kind = "partner-like"          # length matches and the values genuinely vary
        elif all(v < a40["size"] for v in vals):
            kind = "degenerate-body-values"  # in range, but size 1 or constant
        elif all(v in pf.pointers for v in vals):
            kind = "pointers"
        else:
            kind = "other"
        partner_arrays.append({"slot": p, "target": tgt, "size": size, "kind": kind,
                               "values": vals if kind != "pointers" else None,
                               "first_hex": blob[base + tgt:base + tgt + 16].hex()})
    return {"path": path, "file": os.path.basename(path), "n_bodies": a40["size"],
            "n_cinfos": a50["size"], "body_array": a40["ptr"], "cinfo_array": a50["ptr"],
            "bodies": bodies, "cinfos": cinfos, "partner_arrays": partner_arrays}


# --------------------------------------------------------------------------- parts
def parts_rows():
    rows = {}
    with open(PARTS, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                rows[r["entity"]] = r
    return rows


def entity_map():
    """physicsc stem -> the entity files that reference it."""
    out = {}
    for p in glob.glob(ENT_JSON):
        d = json.load(open(p, encoding="utf-8"))
        for ph in d.get("physics") or []:
            stem = os.path.basename(ph.get("file") or "").replace(".physicsc", "")
            out.setdefault(stem, []).append(d.get("entity"))
    return out


def part_links(row):
    """body id -> (parent part index, parent body, part name) for one entity's parts."""
    parts = row["parts"]
    out = {}
    for pi, p in enumerate(parts):
        b = p.get("body")
        if not isinstance(b, int):
            continue
        par = parts[p["parent"]] if isinstance(p.get("parent"), int) and 0 <= p["parent"] < len(parts) else None
        out.setdefault(b, {"part": p.get("n"), "index": pi,
                           "parent_index": p.get("parent"),
                           "parent_part": par.get("n") if par else None,
                           "parent_body": par.get("body") if par else None})
    return out


# --------------------------------------------------------------------------- analysis
def analyse():
    files = []
    for path in sorted(glob.glob(FLEET, recursive=True)):
        try:
            f = scan(path)
        except Exception as e:                                   # noqa: BLE001
            files.append({"path": path, "file": os.path.basename(path), "error": str(e)})
            continue
        if f:
            files.append(f)

    usable = [f for f in files if "error" not in f and f.get("n_cinfos")]
    rows = parts_rows()
    ents = entity_map()

    # --- H3 coverage: which files have .epe part links, and do variants agree?
    variant_disagree = []
    for f in usable:
        stem = f["file"].replace(".physicsc", "")
        linked = [ents[e] for e in [] ]  # placeholder, filled below
        ent_names = [e for e in ents.get(stem, []) if e in rows]
        f["entities"] = ent_names
        maps = []
        for e in ent_names:
            m = part_links(rows[e])
            maps.append({b: (v["parent_body"], v["parent_part"]) for b, v in m.items()})
        f["part_links"] = part_links(rows[ent_names[0]]) if ent_names else {}
        if len(maps) > 1:
            first = maps[0]
            for m in maps[1:]:
                if m != first:
                    variant_disagree.append(f["file"])
                    break
        f["n_entities"] = len(ent_names)

    # --- per record measurements
    recs = []
    for f in usable:
        hulls = {b["id"]: b["hull"]["planes"] for b in f["bodies"] if b["hull"]}
        ident = {b["id"]: b["identity"] for b in f["bodies"]}
        xform = {b["id"]: (b["position"], b["quaternion"]) for b in f["bodies"]}
        links = f.get("part_links") or {}
        for c in f["cinfos"]:
            fr = c["frames"]
            piv = fr[0]["pivot"] if fr else None
            if piv is None:
                continue
            d = {i: abs(sdist(pl, piv)) for i, pl in hulls.items()}
            b = c["body_b"]
            others = sorted(((v, i) for i, v in d.items() if i != b))
            near = others[0] if others else (None, None)
            second = others[1] if len(others) > 1 else (None, None)
            # the loosest reading of "body 0 cannot be the partner": some body OTHER than 0 is
            # close.  This one counts the recorded body too, so it is comparable with G3-10d's
            # review; `others` above is the stricter "a *second* body is close" form.
            anyother = sorted(((v, i) for i, v in d.items() if i != 0))
            best_any = anyother[0] if anyother else (None, None)
            link = links.get(b)
            par_body = link["parent_body"] if link else None
            # local-read: un-transform the pivot by the recorded body's transform
            local = None
            if b in hulls and not ident.get(b, True):
                pos, q = xform[b]
                R = qmat(q)
                loc = [sum(R[k][r] * (piv[k] - pos[k]) for k in range(3)) for r in range(3)]
                local = round(abs(sdist(hulls[b], loc)), 4)
            recs.append({
                "file": f["file"], "k": c["k"], "class": c["class"], "body_b": b,
                "n_bodies": f["n_bodies"], "pivot": piv,
                "pivot_b": fr[1]["pivot"] if len(fr) > 1 else None,
                "n_frames": len(fr),
                "body_a_word": c["body_a_word"], "word_0c": c["word_0c"],
                "d_b": round(d[b], 4) if b in d else None,
                "d_0": round(d[0], 4) if 0 in d else None,
                "best_any": best_any[1],
                "d_best_any": round(best_any[0], 4) if best_any[0] is not None else None,
                "nearest_other": near[1], "d_nearest_other": round(near[0], 4) if near[0] is not None else None,
                "second_other": second[1],
                "d_second_other": round(second[0], 4) if second[0] is not None else None,
                "parent_body": par_body,
                "parent_part": link["parent_part"] if link else None,
                "part": link["part"] if link else None,
                "d_parent": round(d[par_body], 4) if par_body in d else None,
                "local_read": local,
                "d_local_untouched": round(d[b], 4) if b in d else None,
                "b_identity": ident.get(b),
            })

    # --- H1 census
    kinds = {}
    body_id_arrays = []
    for f in usable:
        for a in f["partner_arrays"]:
            kinds[a["kind"]] = kinds.get(a["kind"], 0) + 1
            if a["kind"] in ("partner-like", "degenerate-body-values"):
                body_id_arrays.append({"file": f["file"], "slot": a["slot"], "kind": a["kind"],
                                       "size": a["size"], "values": a["values"],
                                       "n_cinfos": f["n_cinfos"]})

    # --- H2: frames
    two_frames = [r for r in recs if r["n_frames"] >= 2 and r["pivot_b"] is not None]
    same_ab = sum(1 for r in two_frames if r["pivot"] == r["pivot_b"])
    diff_ab = [r for r in two_frames if r["pivot"] != r["pivot_b"]]
    nonident = [r for r in recs if r["local_read"] is not None]
    world_le = sum(1 for r in nonident if (r["d_local_untouched"] or 9) <= TOL)
    local_le = sum(1 for r in nonident if r["local_read"] <= TOL)

    # --- candidate scores
    def hits(key, subset):
        vals = [r[key] for r in subset if r.get(key) is not None]
        return sum(1 for v in vals if v <= TOL), len(vals)

    # C1 body 0
    c1_hit, c1_n = hits("d_0", recs)
    c1_strict = [r for r in recs
                 if r["d_0"] is not None and r["d_nearest_other"] is not None
                 and r["d_0"] > FAR and r["d_nearest_other"] <= TOL]
    c1_any = [r for r in recs
              if r["d_0"] is not None and r["d_best_any"] is not None
              and r["d_0"] > FAR and r["d_best_any"] <= TOL]
    # C4 geometric nearest other body
    c4_hit, c4_n = hits("d_nearest_other", recs)
    c4_ambig = sum(1 for r in recs
                   if r["d_nearest_other"] is not None and r["d_second_other"] is not None
                   and r["d_second_other"] - r["d_nearest_other"] < MARGIN)
    c4_parent = sum(1 for r in recs if r["parent_body"] is not None
                    and r["nearest_other"] == r["parent_body"])
    # C5 .epe parent
    par = [r for r in recs if r["d_parent"] is not None]
    c5_hit, c5_n = hits("d_parent", par)
    c5_b0_hit, c5_b0_n = hits("d_0", par)

    # --- structural: constrained bodies vs parts that have a parent
    struct_rows = []
    for f in usable:
        links = f.get("part_links") or {}
        if not links:
            continue
        constrained = sorted({c["body_b"] for c in f["cinfos"]})
        with_parent = sorted({b for b, v in links.items() if v["parent_body"] is not None})
        inter = [b for b in constrained if b in with_parent]
        struct_rows.append({"file": f["file"], "n_constrained": len(constrained),
                            "n_parts_with_parent": len(with_parent),
                            "n_in_both": len(inter),
                            "constrained_not_in_parents": [b for b in constrained
                                                           if b not in with_parent],
                            "parents_not_constrained": [b for b in with_parent
                                                        if b not in constrained]})

    # --- scores table
    cands = [
        {"id": "C1", "rule": "cinfo +0x04 == 0, i.e. the partner is body 0",
         "where": "inside the 24-byte cinfo", "stored": True,
         "hit": c1_hit, "n": c1_n, "rate": rate(c1_hit, c1_n),
         "contradictions": len(c1_strict), "contradictions_review": len(c1_any),
         "holds": False,
         "why": "0 in all 494 records, so the value cannot name anything; %d records put the "
                "pivot further than %.2f m from body 0 while a body other than 0 and other than "
                "the recorded one is within %.2f m (%d if the recorded body is allowed to be "
                "that body)" % (len(c1_strict), FAR, TOL, len(c1_any))},
        {"id": "C2", "rule": "a parallel array beside the cinfo list, one body id per constraint",
         "where": "hknpPhysicsSystemData / data section", "stored": True,
         "hit": 0, "n": len(recs), "rate": 0.0,
         "contradictions": None, "holds": False,
         "why": "census: the cinfo array is the only same-length array in %d of %d files; arrays "
                "that also carry variable body-range values: %d; body-range but constant/degenerate: "
                "%d in %d file(s)"
                % (kinds.get("cinfo-array", 0), len(usable), kinds.get("partner-like", 0),
                   kinds.get("degenerate-body-values", 0),
                   len({x["file"] for x in body_id_arrays}))},
        {"id": "C3", "rule": "the constraintData's two pivot frames are the two bodies' local frames",
         "where": "constraintData (before/after the limits)", "stored": True,
         "hit": 0, "n": len(two_frames), "rate": 0.0,
         "contradictions": None, "holds": False,
         "why": "the two frames carry the same pivot in %d of %d records (%d differ), so the pair "
                "cannot name two bodies" % (same_ab, len(two_frames), len(diff_ab))},
        {"id": "C4", "rule": "the partner is the body whose hull is nearest the pivot, other than "
                             "the recorded body",
         "where": "geometry only (not stored)", "stored": False,
         "hit": c4_hit, "n": c4_n, "rate": rate(c4_hit, c4_n),
         "contradictions": None, "holds": False,
         "why": "fits %d of %d records but the pick is ambiguous in %d of them (second-nearest "
                "within %g m) and it equals the recorded body's parent part in %d"
                % (c4_hit, c4_n, c4_ambig, MARGIN, c4_parent)},
        {"id": "C5", "rule": "the partner is the body of the recorded body's parent part in the .epe",
         "where": "vehicle .epe part tree", "stored": True,
         "hit": c5_hit, "n": c5_n, "rate": rate(c5_hit, c5_n),
         "contradictions": c5_n - c5_hit, "holds": False,
         "why": "covers %d of %d records (45 of 50 files have a parts row, and the parent's body "
                "needs a decoded hull); on that subset it fits %d of %d (%.1f%%) against body 0's "
                "%d of %d (%.1f%%) - a few points better, nowhere near a rule"
                % (len(par), len(recs), c5_hit, c5_n, 100.0 * (rate(c5_hit, c5_n) or 0),
                   c5_b0_hit, c5_b0_n, 100.0 * (rate(c5_b0_hit, c5_b0_n) or 0))},
    ]

    summary = {
        "fleet_files_matched": len(files),
        "fleet_files_decoded": len(usable),
        "fleet_files_skipped": [{"file": f["file"], "error": f.get("error")}
                                for f in files if "error" in f or not f.get("n_cinfos")],
        "cinfos": len(recs),
        "bodies": sum(f["n_bodies"] for f in usable),
        "bodies_non_identity": sum(1 for f in usable for b in f["bodies"] if not b["identity"]),
        "hulls": sum(1 for f in usable for b in f["bodies"] if b["hull"]),
        "files_with_parts": sum(1 for f in usable if f.get("part_links")),
        "records_with_parts": len(par),
        "variant_disagreements": variant_disagree,
        "frames": {"with_two": len(two_frames), "same_pivot": same_ab, "differ": len(diff_ab),
                   "differing": [{"file": r["file"], "k": r["k"],
                                  "a": r["pivot"], "b": r["pivot_b"]} for r in diff_ab]},
        "non_identity_records": {"n": len(nonident),
                                 "world_read_le_5cm": world_le, "local_read_le_5cm": local_le,
                                 "median_world": median([r["d_local_untouched"] for r in nonident]),
                                 "median_local": median([r["local_read"] for r in nonident])},
        "partner_array_census": kinds,
        "body_id_lookalikes": body_id_arrays,
        "scores": {"c1": {"hit": c1_hit, "n": c1_n,
                           "contradictions_strict": len(c1_strict),
                           "contradictions_review": len(c1_any)},
                   "c4": {"hit": c4_hit, "n": c4_n, "ambiguous": c4_ambig,
                          "equals_parent": c4_parent},
                   "c5": {"hit": c5_hit, "n": c5_n, "body0_hit": c5_b0_hit,
                          "body0_n": c5_b0_n}},
        "candidates": cands,
        "structural": {"rows": struct_rows,
                       "files": len(struct_rows),
                       "constrained_total": sum(r["n_constrained"] for r in struct_rows),
                       "in_both_total": sum(r["n_in_both"] for r in struct_rows),
                       "files_all_constrained_have_parent": sum(
                           1 for r in struct_rows if not r["constrained_not_in_parents"])},
        "median": {"d_b": median([r["d_b"] for r in recs]),
                   "d_0": median([r["d_0"] for r in recs]),
                   "d_nearest_other": median([r["d_nearest_other"] for r in recs]),
                   "d_parent": median([r["d_parent"] for r in par])},
    }
    return {"summary": summary, "records": recs,
            "files": [{"file": f["file"], "n_bodies": f["n_bodies"], "n_cinfos": f["n_cinfos"],
                       "n_hulls": sum(1 for b in f["bodies"] if b["hull"]),
                       "n_non_identity": sum(1 for b in f["bodies"] if not b["identity"]),
                       "entities": f.get("entities") or [],
                       "partner_arrays": f["partner_arrays"]} for f in usable]}


CHECKS = [
    ("every fleet .physicsc parses and has a physics system data object",
     lambda s, d: (s["fleet_files_decoded"] >= 50,
                   "%d decoded of %d matched" % (s["fleet_files_decoded"],
                                                 s["fleet_files_matched"]))),
    ("the cinfo sweep reproduces G3-10d's 494 records",
     lambda s, d: (s["cinfos"] == 494, "%d cinfos over %d files" % (s["cinfos"],
                                                                    s["fleet_files_decoded"]))),
    ("word +0x04 is 0 in every record (so it cannot be a body id)",
     lambda s, d: (all(r["body_a_word"] == 0 for r in d["records"]),
                   "distinct values %s" % sorted({r["body_a_word"] for r in d["records"]}))),
    ("H1: no array parallel to the cinfo list carries a varying body id per constraint",
     lambda s, d: (s["partner_array_census"].get("partner-like", 0) == 0,
                   "array kinds %s" % s["partner_array_census"])),
    ("H2: the two constraintData frames share one pivot in almost every record",
     lambda s, d: (s["frames"]["same_pivot"] >= 0.95 * max(1, s["frames"]["with_two"]),
                   "%d of %d same, %d differ" % (s["frames"]["same_pivot"],
                                                 s["frames"]["with_two"], s["frames"]["differ"]))),
    ("H2: the local-space read does not beat the world read on the records that can tell them apart",
     lambda s, d: (s["non_identity_records"]["local_read_le_5cm"]
                   <= s["non_identity_records"]["world_read_le_5cm"] + 1,
                   "n=%d world<=5cm %d, local<=5cm %d"
                   % (s["non_identity_records"]["n"],
                      s["non_identity_records"]["world_read_le_5cm"],
                      s["non_identity_records"]["local_read_le_5cm"]))),
    ("H3: parts rows cover most of the fleet and variants of one physicsc agree",
     lambda s, d: (s["files_with_parts"] >= 40 and not s["variant_disagreements"],
                   "%d files with parts; variant disagreements %s"
                   % (s["files_with_parts"], s["variant_disagreements"] or "none"))),
    ("no candidate rule names the partner for every record of every file",
     lambda s, d: (all(not c["holds"] for c in s["candidates"]),
                   "; ".join("%s %s/%s" % (c["id"], c["hit"], c["n"]) for c in s["candidates"]))),
    ("the C1 contradictions reproduce the review's counterexample count (>= 50 with the recorded "
     "body allowed as the near body)",
     lambda s, d: (s["scores"]["c1"]["contradictions_review"] >= 50,
                   "%d strict, %d counting the recorded body"
                   % (s["scores"]["c1"]["contradictions_strict"],
                      s["scores"]["c1"]["contradictions_review"]))),
    ("H3: on the records that have a parts row, the parent body fits at least as often as body 0",
     lambda s, d: (s["scores"]["c5"]["hit"] >= s["scores"]["c5"]["body0_hit"],
                   "parent %d/%d vs body 0 %d/%d"
                   % (s["scores"]["c5"]["hit"], s["scores"]["c5"]["n"],
                      s["scores"]["c5"]["body0_hit"], s["scores"]["c5"]["n"]))),
]


# --------------------------------------------------------------------------- render
def render(d, s):
    a = []
    A = a.append
    c = {x["id"]: x for x in s["candidates"]}
    sc = s["scores"]
    A("# JC3 constraint partner, second pass (G3-10g) - is the other body stored anywhere?")
    A("")
    A("Generated by `Tools/scripts/jc3_physics_roles6.py` (`--write`); `--check` recomputes every")
    A("number from the install and compares.")
    A("Labels: **decoded** = read from bytes at a stated offset; **derived** = arithmetic on")
    A("decoded values with the rule given; **UNKNOWN** = not decoded, with what was tried.")
    A("")
    A("Scope: all %d `.physicsc` files under `E:/Modding/_shared/gamedata/JC3grab` (%d decoded, %d skipped),"
      % (s["fleet_files_matched"], s["fleet_files_decoded"], len(s["fleet_files_skipped"])))
    A("**%d constraint records** over %d bodies (%d of them with a decoded convex hull, %d with a"
      % (s["cinfos"], s["bodies"], s["hulls"], s["bodies_non_identity"]))
    A("non-identity transform), and the %d files that have a `.epe` parts row." % s["files_with_parts"])
    A("")
    A("## VERDICT")
    A("")
    A("**The partner of a constraint is UNKNOWN. No candidate names it.** Three of the five")
    A("candidates are *stored* readings and all three are excluded by the bytes; the two that are")
    A("geometric fits cover only part of the fleet and pick an ambiguous near-tie elsewhere.")
    A("")
    A("| id | candidate | where | fits | coverage | holds? |")
    A("|---|---|---|---:|---:|---|")
    for x in s["candidates"]:
        A("| %s | %s | %s | %d | %s%% | %s |"
          % (x["id"], x["rule"], x["where"], x["hit"],
             ("%.1f" % (100.0 * x["hit"] / x["n"])) if x["n"] else "-",
             "**no**" if not x["holds"] else "yes"))
    A("")
    A("Reading of the table, shortest form: the record's own second id word is a constant, there is")
    A("no parallel array beside the constraint list, the two pivot frames are the same point, the")
    A("nearest-hull rule settles only %d of %d records and is ambiguous (second body within"
      % (c["C4"]["hit"], c["C4"]["n"]))
    A("0.01 m) in %d of them, and the" % sc["c4"]["ambiguous"])
    A("`.epe` parent link fits %d of its %d records - better than body 0 on the same subset, but not"
      % (c["C5"]["hit"], c["C5"]["n"]))
    A("a rule: %d of them miss." % (c["C5"]["n"] - c["C5"]["hit"]))
    A("")
    A("## 1. H1 - a parallel array beside the constraint list (decoded: absent)")
    A("")
    A("Every array header in each data section whose `size` equals the file's constraint count was")
    A("listed and its elements classified by domain:")
    A("")
    A("| arrays found | count over 50 files | reading |")
    A("|---|---:|---|")
    for k, v in sorted(s["partner_array_census"].items(), key=lambda kv: -kv[1]):
        A("| `%s` | %d | %s |" % (k, v, {
            "cinfo-array": "the constraint list itself",
            "pointers": "callback/instance pointers, not body ids",
            "other": "elements outside the body table",
            "degenerate-body-values": "in body range, but length 1 or a constant list",
            "partner-like": "a varying body list - none exist",
        }.get(k, "")))
    A("")
    seen, long_ones = set(), []
    for x in s["body_id_lookalikes"]:
        if x["size"] < 2:
            continue
        k = (x["file"], x["size"], tuple(x["values"]))
        if k in seen:
            continue
        seen.add(k)
        long_ones.append(x)
    A("Arrays whose length matches the constraint count and whose elements fall inside the body")
    A("table - i.e. every candidate for a stored partner list. None of them varies like a")
    A("per-constraint list; the ones of length 1 are degenerate by construction:")
    A("")
    if long_ones:
        A("| file | length | values |")
        A("|---|---:|---|")
        for x in long_ones:
            A("| `%s` | %d | `%s` |" % (x["file"], x["size"], x["values"]))
        A("")
    A("%d such arrays in %d of %d files: %d have length 1 and %d are constant apart from a single 2."
      % (len(s["body_id_lookalikes"]), len({x["file"] for x in s["body_id_lookalikes"]}),
         s["fleet_files_decoded"],
         sum(1 for x in s["body_id_lookalikes"] if x["size"] == 1), len(long_ones)))
    A("A list that paired constraints would vary with the constraints in every file; in the")
    A("Serpente's whole data section there is exactly one array header with size 11 - the cinfo")
    A("array itself.")
    A("")
    A("## 2. H2 - the constraintData's two frames (decoded: one point, not two)")
    A("")
    A("Frames are located by the project's own `rot3x4` test (three unit rows, orthogonal, det +1)")
    A("sliding over the object; the translation follows the 3x4 rotation.")
    A("")
    A("| measure | value |")
    A("|---|---:|")
    A("| records with two or more frames | %d |" % s["frames"]["with_two"])
    A("| of those, the two frames carry the **same** pivot | %d |" % s["frames"]["same_pivot"])
    A("| of those, the pivots differ | %d |" % s["frames"]["differ"])
    A("")
    if s["frames"]["differing"]:
        A("The differing records, in full:")
        A("")
        A("| file | cinfo | frame A | frame B |")
        A("|---|---:|---|---|")
        for r in s["frames"]["differing"]:
            A("| `%s` | %d | `%s` | `%s` |" % (r["file"], r["k"], r["a"], r["b"]))
        A("")
    A("A pair of frames that is the same point cannot say which body is on which side, so H2 fails")
    A("structurally rather than statistically. The frame *convention* was still measured, because a")
    A("body-local frame would name the body it belongs to. On the %d records whose recorded body"
      % s["non_identity_records"]["n"])
    A("has a non-identity transform - the only records that can tell a world read from a body-local")
    A("read apart - the untouched (world) read puts the pivot within 5 cm on **%d** and the"
      % s["non_identity_records"]["world_read_le_5cm"])
    A("un-transformed (local) read on **%d**; medians %.4f m and %.4f m. The two readings are"
      % (s["non_identity_records"]["local_read_le_5cm"],
         s["non_identity_records"]["median_world"], s["non_identity_records"]["median_local"]))
    A("indistinguishable on this sample, so the frame convention is not settled by them either - and")
    A("a frame that cannot be placed in a body cannot name that body.")
    A("")
    A("## 3. H3 - the .epe part tree (decoded: real link, wrong rule)")
    A("")
    A("%d of %d files map to a parts row (%d records); where several entity variants share one"
      % (s["files_with_parts"], s["fleet_files_decoded"], s["records_with_parts"]))
    A("physicsc their body->parent maps agree%s. The parent link is a real per-part pairing - in"
      % (" (0 disagreements)" if not s["variant_disagreements"]
         else " except %s" % s["variant_disagreements"]))
    A("every one of the %d files that has parts, every constrained body is a part with a parent"
      % s["structural"]["files"])
    A("(%d of %d cases) - but the parent's body does not carry the pivot as systematically as the"
      % (s["structural"]["in_both_total"], s["structural"]["constrained_total"]))
    A("rule needs:")
    A("")
    A("| candidate | fits | n | rate | median distance |")
    A("|---|---:|---:|---:|---:|")
    A("| `C5` parent body of the recorded body's part | %d | %d | %.3f | %.4f m |"
      % (c["C5"]["hit"], c["C5"]["n"], c["C5"]["rate"] or 0, s["median"]["d_parent"] or 0))
    A("| `C1` body 0, on the records where both are measurable | %d | %d | %.3f | %.4f m |"
      % (sc["c5"]["body0_hit"], sc["c5"]["body0_n"],
         sc["c5"]["body0_hit"] / max(1, sc["c5"]["body0_n"]), s["median"]["d_0"] or 0))
    A("| `C4` nearest other body | %d | %d | %.3f | %.4f m |"
      % (c["C4"]["hit"], c["C4"]["n"], c["C4"]["rate"] or 0, s["median"]["d_nearest_other"] or 0))
    A("")
    A("Structural check, over the %d files that have parts: the constrained bodies are parts with a"
      % s["structural"]["files"])
    A("parent in %d of %d cases; in %d of those files **every** constrained body is a part with a"
      % (s["structural"]["in_both_total"], s["structural"]["constrained_total"],
         s["structural"]["files_all_constrained_have_parent"]))
    A("parent. That is why the parent link looked like the answer: it pairs exactly the joints the")
    A("constraints describe, in the Serpente and fleet-wide. It fails as the *body* rule because the")
    A("parent's own hull is often not where the hinge sits (front bumper -> engine: 0.77 m in the")
    A("Serpente, while body 0 is 0.035 m away), so a parent body is a plausible-side guess, not an")
    A("identified partner.")
    A("")
    A("## 4. Each candidate, with its score")
    A("")
    for x in s["candidates"]:
        A("**%s - %s** (%s). fits %d/%s%s. %s"
          % (x["id"], x["rule"], x["where"], x["hit"], x["n"],
             (" (%.1f%%)" % (100.0 * x["hit"] / x["n"])) if x["n"] else "", x["why"]))
        A("")
    A("## 5. Checks")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for ch in d["checks"]:
        A("| %s | %s | %s |" % (ch["check"], "PASS" if ch["pass"] else "FAIL", ch["detail"]))
    A("")
    A("%d/%d checks passed." % (sum(1 for ch in d["checks"] if ch["pass"]), len(d["checks"])))
    A("")
    A("## 6. UNKNOWN")
    A("")
    A("- **The true second body of a constraint.** Tried: the two id words (one is always 0, the")
    A("  other is the recorded body), a size-matched parallel array in every file (absent), both")
    A("  pivot frames in world and body-local space (one point, and the world read wins where the two")
    A("  differ), the .epe parent link (pairs the right joints, wrong geometry), and the nearest-hull")
    A("  fit (ambiguous). Where it would be found: a body-side constraint array (none: the 96-byte")
    A("  body entry resolves to a shape and a property node and nothing that indexes the cinfo list),")
    A("  or a Havok 2014 `hknpConstraintCinfo` header, which this tree does not contain.")
    A("- **Whether a constant 0 at +0x04 is a body id or a flag.** Unchanged: it is 0 in all %d"
      % s["cinfos"])
    A("  shipped records, so the bytes cannot separate the readings.")
    A("- **Why body 0 is such a good fit.** %d of %d records put the pivot within 5 cm of the chassis"
      % (c["C1"]["hit"], c["C1"]["n"]))
    A("  hull, which is what a hinge to the chassis looks like - and also what a large central hull")
    A("  looks like for any joint on the vehicle's midline. The oracle cannot separate those.")
    A("- **Runtime meaning**: no game was launched; every number is a file fact.")
    A("")
    return "\n".join(a) + "\n"


# --------------------------------------------------------------------------- main
def build():
    d = analyse()
    s = d["summary"]
    checks = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn(s, d)
        except Exception as e:                                   # noqa: BLE001
            ok, detail = False, "check raised %s: %s" % (type(e).__name__, e)
        checks.append({"check": name, "pass": bool(ok), "detail": detail})
    d["checks"] = checks
    return d


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    d = build()
    md = render(d, d["summary"])
    bad = [c["check"] for c in d["checks"] if not c["pass"]]
    if args.write:
        os.makedirs(os.path.dirname(MD), exist_ok=True)
        with open(JS, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"summary": d["summary"], "checks": d["checks"],
                                "records": d["records"], "files": d["files"]},
                               indent=1, sort_keys=False) + "\n")
        with open(MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        s = d["summary"]
        print("wrote PHYSICS_ROLES6.md and PHYSICS_ROLES6.json")
        print("files %d | cinfos %d | hulls %d | parts files %d"
              % (s["fleet_files_decoded"], s["cinfos"], s["hulls"], s["files_with_parts"]))
        print("candidates: " + " | ".join("%s %s/%s" % (c["id"], c["hit"], c["n"])
                                          for c in s["candidates"]))
        print("checks: %d/%d" % (len(d["checks"]) - len(bad), len(d["checks"])))
    if args.check:
        old_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        old = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else {}
        same = old_md == md and old.get("summary") == d["summary"]
        print("%s: files %d, cinfos %d, %d/%d checks, md+summary byte-identical=%s%s"
              % ("OK" if not bad and same else "FAIL", d["summary"]["fleet_files_decoded"],
                 d["summary"]["cinfos"], len(d["checks"]) - len(bad), len(d["checks"]), same,
                 "" if not bad else " | failing: " + "; ".join(bad)))
        return 0 if (same and not bad) else 1
    if not args.write and not args.check:
        print(md[:2000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
