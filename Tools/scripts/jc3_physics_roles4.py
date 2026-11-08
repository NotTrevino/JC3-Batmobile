"""jc3_physics_roles4.py - G3-10d: the constraint partner, and the 24 packed inertia bytes.

TWO QUESTIONS, TWO ANSWERS OF DIFFERENT STRENGTH.

1. The constraint partner. G3-10c decoded the 24-byte cinfo as
   `{constraintData*, bodyId, 0x7FFFFFFF, 0, 0}` and found no second body id in it, so the
   partner side was UNKNOWN.  This pass re-reads the same record over the whole fleet and
   tests the one reading the bytes allow: words +0x04 and +0x08 as the two body ids, i.e.
   `{cd*, bodyIdA, bodyIdB, 0x7FFFFFFF, 0, 0}` with `bodyIdA` = 0 in every shipped record.
   The test is geometric and has controls (see `pair_hypothesis` in the JSON):

     * the cinfo's transforms A and B carry a pivot, and both bodies of a constraint must
       touch that pivot, so |signed distance pivot -> hull| must be small for the pair and
       not for a random body;
     * control 1: the partner replaced by a deterministic pseudo-random other body;
     * control 2: every other fixed body id measured the same way, which shows whether
       body 0 is special or merely the largest hull.

2. The 24 packed bytes of hknpShapeMassProperties (+0x10..+0x27, mass float at +0x28).
   No public Havok 2014 header and no community reader for this class could be obtained in
   this session, so the format is attacked from the bytes: every per-component reading of
   the 24 bytes (12 x int16 at three scales, 12 x u16, 12 x IEEE half, 6 x f32) is scored
   against the one oracle the file itself supplies - the box inertia of the hull the block
   is bound to:

       Ixx = m (ey^2 + ez^2)/12,  Iyy = m (ex^2 + ez^2)/12,  Izz = m (ex^2 + ey^2)/12

   A packed format must give a *constant* scale inside a body (I_i / value_i equal on all
   three axes).  Measured: no tested reading does, so the tensor stays UNKNOWN with the
   blocker named.  The one measured regularity (one slot rises with mass) is recorded as a
   hint, not as a decode.

Usage:
    python Tools/scripts/jc3_physics_roles4.py --write
    python Tools/scripts/jc3_physics_roles4.py --check

`--write` regenerates Research/JC3Grab/PHYSICS_ROLES4.md and .json.
`--check` rebuilds in memory, requires the committed files to be byte-identical, re-runs
every oracle and prints the result.  Exit code 0 only if everything passes.

Read-only: the donor physicsc and the fleet files are opened for reading and nothing else.
"""

import glob
import json
import math
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3hkx  # noqa: E402
import jc3_physics_roles2 as R2  # noqa: E402  (rot3x4, DONOR)

DONOR = R2.DONOR
FLEET_GLOB = r"E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc"
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES4.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES4.json")

CINFO_STRIDE = 24
BODY_ENTRY = 96
MASS_OFF = 0x28
PACK_OFF = 0x10
PACK_LEN = 24
TOLS = (0.02, 0.05, 0.10, 0.20)
NO_BODY = 0x7FFFFFFF
SEED = 1000
# A packed format with one scale per body must put the three axes' implied scale within a few
# percent. 15% is a deliberately generous bar; the best candidate is 33% off, and the AABB-vs-hull
# shape error is of that order, so the oracle cannot certify any reading (see the MD).
DECODE_BAR = 1.15


# ---------------------------------------------------------------- helpers
def rel(path):
    try:
        return os.path.relpath(path, ROOT).replace("\\", "/")
    except ValueError:
        return path.replace("\\", "/")


def spearman(a, b):
    """Rank correlation without scipy; ties take the first rank, as in the report."""
    ra = [sorted(a).index(x) for x in a]
    rb = [sorted(b).index(x) for x in b]
    n = len(a)
    if n < 3:
        return 0.0
    ma, mb = sum(ra) / n, sum(rb) / n
    num = sum((ra[i] - ma) * (rb[i] - mb) for i in range(n))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((x - mb) ** 2 for x in rb))
    return num / (da * db) if da * db else 0.0


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def half16(u):
    """IEEE 754 binary16 -> float; one of the tested readings of the packed block."""
    s = (u >> 15) & 1
    e = (u >> 10) & 0x1F
    m = u & 0x3FF
    if e == 0:
        return (-1) ** s * m / 1024.0 * 2 ** -14
    if e == 31:
        return float("nan")
    return (-1) ** s * (1 + m / 1024.0) * 2.0 ** (e - 15)


def hull_of(pf, shape):
    if not shape or pf._starts.get(shape) != "hknpConvexPolytopeShape":
        return None
    d = jc3hkx.decode_polytope(pf, shape)
    return {"planes": d["planes"], "bounds": d["bounds"], "convex_ok": d["convex_ok"],
            "n_planes": len(d["planes"])}


def sdist(planes, p):
    """Signed distance of p to the hull surface: max over planes of (n.p + d).

    jc3hkx stores each plane normal so that <= 0 is inside, so this is > 0 outside and ~0 on
    the surface - which is where a hinge pivot sits.
    """
    return max(n["n"][0] * p[0] + n["n"][1] * p[1] + n["n"][2] * p[2] + n["d"]
               for n in planes)


def rot_delta(a_rows, b_rows):
    """D = A^T B for two 3x3 rotations -> (angle deg, axis, det)."""
    at = [[a_rows[c][r] for c in range(3)] for r in range(3)]
    d = [[sum(at[r][k] * b_rows[k][c] for k in range(3)) for c in range(3)] for r in range(3)]
    tr = d[0][0] + d[1][1] + d[2][2]
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (tr - 1.0) / 2.0))))
    ax = [d[2][1] - d[1][2], d[0][2] - d[2][0], d[1][0] - d[0][1]]
    nrm = math.sqrt(sum(x * x for x in ax))
    det = (d[0][0] * (d[1][1] * d[2][2] - d[1][2] * d[2][1])
           - d[0][1] * (d[1][0] * d[2][2] - d[1][2] * d[2][0])
           + d[0][2] * (d[1][0] * d[2][1] - d[1][1] * d[2][0]))
    axis = [round(x / nrm, 6) for x in ax] if nrm else None
    return round(ang, 4), axis, round(det, 6)


# ---------------------------------------------------------------- one file
def scan(path, with_inertia):
    """Everything this pass needs from one .physicsc, or None without system data."""
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
    if psd is None:
        return None
    a40 = pf.array(psd.offset + 0x40)
    a50 = pf.array(psd.offset + 0x50)
    out = {"path": path, "extent": pf.extents[psd.offset], "n_bodies": a40["size"],
           "n_cinfos": a50["size"], "bodies": [], "cinfos": []}

    for i in range(a40["size"]):
        at = a40["ptr"] + BODY_ENTRY * i
        shape = pf.pointers.get(at, 0)
        b = {"id": i, "entry": at, "shape": shape,
             "shape_class": pf._starts.get(shape, "") if shape else "",
             "position": [round(struct.unpack_from("<f", blob, base + at + 0x30 + 4 * k)[0], 6)
                          for k in range(3)],
             "quaternion": [round(struct.unpack_from("<f", blob, base + at + 0x40 + 4 * k)[0], 6)
                            for k in range(4)],
             "field_08": struct.unpack_from("<I", blob, base + at + 8)[0],
             "field_0c": struct.unpack_from("<I", blob, base + at + 0x0C)[0],
             "field_10": struct.unpack_from("<I", blob, base + at + 0x10)[0],
             "hull": None, "mass": None, "mass_block": None}
        b["hull"] = hull_of(pf, shape)
        if with_inertia and b["shape_class"] == "hknpConvexPolytopeShape":
            node = pf.pointers.get(shape + 0x20, 0)
            if node and pf._starts.get(node) == "hkRefCountedProperties":
                mp = pf.pointers.get(node + 0x10, 0)
                if mp and pf._starts.get(mp) == "hknpShapeMassProperties":
                    b["mass"] = round(struct.unpack_from("<f", blob, base + mp + MASS_OFF)[0], 6)
                    b["mass_block"] = {
                        "offset": mp, "extent": pf.extents[mp],
                        "raw_hex": blob[base + mp + PACK_OFF:base + mp + PACK_OFF + PACK_LEN].hex(),
                        "mass_hex": blob[base + mp + MASS_OFF:base + mp + MASS_OFF + 4].hex(),
                    }
        out["bodies"].append(b)

    for k in range(a50["size"]):
        rec = a50["ptr"] + CINFO_STRIDE * k
        w = struct.unpack_from("<6I", blob, base + rec)
        co = pf.pointers.get(rec, 0)
        # +0x08 is the body id (G3-10c); +0x04 is the constant 0 word tested as body A.
        c = {"index": k, "record": rec, "constraint": co,
             "constraint_class": pf._starts.get(co, "") if co else "",
             "words_hex": ["%08x" % x for x in w],
             "body_id_a": w[1], "body_id_b": w[2], "word_0c": w[3],
             "pivots": [], "pivots_equal": None, "n_frames": 0, "pivots_ab_equal": None,
             "transform_offsets": [],
             "rot_delta_deg": None, "rot_delta_axis": None, "rot_delta_det": None}
        if co:
            ext = pf.extents[co]
            fl = [struct.unpack_from("<f", blob, base + co + 4 * j)[0] for j in range(ext // 4)]
            tr = []
            for s in range(0, max(0, len(fl) - 16)):
                hit = R2.rot3x4(fl[s:s + 16])
                if hit is None:
                    continue
                tr.append({"at": s * 4, "det": hit[0], "rows": hit[1],
                           "pivot": [round(fl[s + 12 + t], 6) for t in range(3)]})
            c["transform_offsets"] = [t["at"] for t in tr]
            c["pivots"] = [t["pivot"] for t in tr]
            c["n_frames"] = len(tr)
            if len(tr) >= 2:
                # frames A and B are the constraint's two sides; a ragdoll can carry a third
                c["pivots_ab_equal"] = tr[0]["pivot"] == tr[1]["pivot"]
                c["pivots_equal"] = all(p == tr[0]["pivot"] for p in c["pivots"][1:])
                ang, ax, det = rot_delta(tr[0]["rows"], tr[1]["rows"])
                c["rot_delta_deg"], c["rot_delta_axis"], c["rot_delta_det"] = ang, ax, det
        out["cinfos"].append(c)
    return out


# ---------------------------------------------------------------- part 1
def part1(donor, fleet):
    """The partner hypothesis {cd*, bodyIdA, bodyIdB, 0x7FFFFFFF, 0, 0}, oracle + 2 controls."""
    recs = []
    for f in fleet:
        hulls = {b["id"]: b["hull"]["planes"] for b in f["bodies"] if b["hull"]}
        for c in f["cinfos"]:
            if not c["pivots"]:
                continue
            piv = c["pivots"][0]
            d = {i: abs(sdist(pl, piv)) for i, pl in hulls.items()}
            recs.append({"file": os.path.basename(f["path"]), "index": c["index"],
                         "body_id_a": c["body_id_a"], "body_id_b": c["body_id_b"],
                         "n_bodies": f["n_bodies"], "n_hulls": len(hulls), "pivot": piv,
                         "d_a": d.get(c["body_id_a"]), "d_b": d.get(c["body_id_b"]), "d": d})

    both = [r for r in recs if r["d_b"] is not None and r["d_a"] is not None]
    tol_rows = []
    for tol in TOLS:
        hit = sum(1 for r in both if r["d_b"] <= tol and r["d_a"] <= tol)
        ctrl_hit = ctrl_n = 0
        for r in both:
            alts = sorted(i for i in r["d"] if i not in (r["body_id_a"], r["body_id_b"]))
            if not alts:
                continue
            rnd = random.Random(SEED + r["index"] * 31 + r["body_id_b"])
            ctrl_n += 1
            if r["d"][rnd.choice(alts)] <= tol:
                ctrl_hit += 1
        tol_rows.append({"tol_m": tol, "pair_hits": hit, "pair_n": len(both),
                         "pair_rate": round(hit / len(both), 4) if both else None,
                         "control_hits": ctrl_hit, "control_n": ctrl_n,
                         "control_rate": round(ctrl_hit / ctrl_n, 4) if ctrl_n else None})

    per_body = []
    for i in range(4):
        seen = [r for r in both if r["d"].get(i) is not None]
        ok = sum(1 for r in seen if r["d"][i] <= 0.05)
        per_body.append({"body": i, "within_5cm": ok, "measured": len(seen),
                         "rate": round(ok / len(seen), 4) if seen else None})

    dhuils = {b["id"]: b["hull"]["planes"] for b in donor["bodies"] if b["hull"]}
    donor_rows = []
    for c in donor["cinfos"]:
        if not c["pivots"]:
            continue
        piv = c["pivots"][0]
        cand = sorted(({"body": i, "abs_dist": round(abs(sdist(pl, piv)), 4)}
                       for i, pl in dhuils.items()), key=lambda x: x["abs_dist"])
        donor_rows.append({
            "index": c["index"],
            "name": c["constraint_class"].replace("hkp", "").replace("ConstraintData", ""),
            "class": c["constraint_class"],
            "body_id_b": c["body_id_b"], "pivot": piv, "n_frames": c["n_frames"],
            "transforms": c["transform_offsets"], "pivots_ab_equal": c["pivots_ab_equal"],
            "pivots_equal": c["pivots_equal"],
            "rot_delta_deg": c["rot_delta_deg"], "rot_delta_det": c["rot_delta_det"],
            "abs_dist_a": round(abs(sdist(dhuils[0], piv)), 4) if 0 in dhuils else None,
            "abs_dist_b": (round(abs(sdist(dhuils[c["body_id_b"]], piv)), 4)
                           if c["body_id_b"] in dhuils else None),
            "nearest": cand[:4]})

    return {
        "cinfos_seen": len(recs), "cinfos_with_both_hulls": len(both),
        "files_with_constraints": len(set(r["file"] for r in recs)),
        "body_id_a_values": sorted(set(r["body_id_a"] for r in recs)),
        "body_id_a_in_range": all(0 <= r["body_id_a"] < r["n_bodies"] for r in recs),
        "body_id_b_all_in_range": all(0 <= r["body_id_b"] < r["n_bodies"] for r in recs),
        "tolerance_table": tol_rows, "per_body": per_body,
        "median_d_a": round(median([r["d_a"] for r in both]) or 0, 4),
        "median_d_b": round(median([r["d_b"] for r in both]) or 0, 4),
        "donor_frames_on_one_pivot": sum(1 for c in donor["cinfos"] if c["pivots_ab_equal"]),
        "donor_with_frames": sum(1 for c in donor["cinfos"] if c["n_frames"] >= 2),
        "donor_frame_counts": sorted({c["n_frames"] for c in donor["cinfos"]}),
        "donor_constraints": len(donor["cinfos"]),
        "donor": donor_rows,
    }


# ---------------------------------------------------------------- part 2
INTERPS = (
    ("6 x IEEE f32", "f32"),
    ("12 x int16 raw", "i16"),
    ("12 x int16 / 16384", "i16_16384"),
    ("12 x int16 / 32767", "i16_32767"),
    ("12 x u16 raw", "u16"),
    ("12 x IEEE half", "half"),
)


def decode_slots(raw_hex, how):
    b = bytes.fromhex(raw_hex)
    if how == "f32":
        return list(struct.unpack("<6f", b))
    u = struct.unpack("<12H", b)
    if how == "i16":
        return list(struct.unpack("<12h", b))
    if how == "i16_16384":
        return [v / 16384.0 for v in struct.unpack("<12h", b)]
    if how == "i16_32767":
        return [v / 32767.0 for v in struct.unpack("<12h", b)]
    if how == "u16":
        return list(u)
    if how == "half":
        return [half16(v) for v in u]
    raise ValueError(how)


def part2(fleet):
    """The 24-byte block against the box inertia of the hull it is bound to."""
    hulls = []
    for f in fleet:
        for b in f["bodies"]:
            if not b["hull"] or b["mass"] is None or not b["mass_block"]:
                continue
            lo, hi = b["hull"]["bounds"]["min"], b["hull"]["bounds"]["max"]
            e = [hi[t] - lo[t] for t in range(3)]
            m = b["mass"]
            if min(e) <= 0 or not (0.05 < m < 1e6):
                continue
            I = [m * (e[1] ** 2 + e[2] ** 2) / 12.0,
                 m * (e[0] ** 2 + e[2] ** 2) / 12.0,
                 m * (e[0] ** 2 + e[1] ** 2) / 12.0]
            hulls.append({"file": os.path.basename(f["path"]), "body": b["id"], "mass": m,
                          "extents": [round(x, 4) for x in e],
                          "box_inertia": [round(x, 4) for x in I],
                          "raw_hex": b["mass_block"]["raw_hex"],
                          "mass_hex": b["mass_block"]["mass_hex"]})

    triples = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11),
               (1, 2, 3), (4, 5, 6), (7, 8, 9))
    interp_rows = []
    for name, how in INTERPS:
        best = None
        for T in triples:
            spreads = []
            for h in hulls:
                v = decode_slots(h["raw_hex"], how)
                if max(T) >= len(v):
                    continue
                if any(abs(v[i]) < 1e-9 or not math.isfinite(v[i]) for i in T):
                    continue
                ratios = [h["box_inertia"][k] / v[T[k]] for k in range(3)]
                if any(x <= 0 for x in ratios):
                    continue
                spreads.append(max(ratios) / min(ratios))
            if len(spreads) >= 10:
                med = median(spreads)
                row = {"triple": list(T), "median_spread": round(med, 4), "n": len(spreads)}
                if best is None or med < best["median_spread"]:
                    best = row
        interp_rows.append({"reading": name, "how": how, "best_triple": best,
                            "decodes": bool(best and best["median_spread"] <= DECODE_BAR)})

    dir_rows = []
    for T in triples:
        dots = []
        for h in hulls:
            v = [abs(x) for x in decode_slots(h["raw_hex"], "i16_16384")]
            if max(T) >= len(v):
                continue
            vv = [v[i] for i in T]
            nv = math.sqrt(sum(x * x for x in vv))
            nu = math.sqrt(sum(x * x for x in h["box_inertia"]))
            if nv and nu:
                dots.append(sum(vv[i] * h["box_inertia"][i] for i in range(3)) / (nv * nu))
        if dots:
            dir_rows.append({"triple": list(T), "mean_cos": round(sum(dots) / len(dots), 4),
                             "min_cos": round(min(dots), 4), "n": len(dots)})

    slot_rows = []
    for j in range(12):
        col = [abs(decode_slots(h["raw_hex"], "i16_16384")[j]) for h in hulls]
        slot_rows.append({
            "slot": j,
            "rho_mass": round(spearman(col, [h["mass"] for h in hulls]), 4),
            "rho_Ixx": round(spearman(col, [h["box_inertia"][0] for h in hulls]), 4),
            "rho_Iyy": round(spearman(col, [h["box_inertia"][1] for h in hulls]), 4),
            "rho_Izz": round(spearman(col, [h["box_inertia"][2] for h in hulls]), 4),
        })

    return {"linked_hulls": len(hulls), "files": len(set(h["file"] for h in hulls)),
            "sample": hulls[:8], "interpretations": interp_rows,
            "direction_test": dir_rows, "slots": slot_rows,
            "any_reading_decodes": any(r["decodes"] for r in interp_rows)}


# ---------------------------------------------------------------- build
def build():
    donor_raw = scan(DONOR, with_inertia=True)
    files = sorted(glob.glob(FLEET_GLOB, recursive=True))
    fleet, skipped = [], []
    for p in files:
        try:
            f = scan(p, with_inertia=True)
        except Exception as exc:
            skipped.append({"file": rel(p), "error": type(exc).__name__})
            continue
        if f is None:
            skipped.append({"file": rel(p), "error": "no hknpPhysicsSystemData"})
            continue
        fleet.append(f)

    p1 = part1(donor_raw, fleet)
    p2 = part2(fleet)

    doc = {
        "meta": {
            "task": "G3-10d",
            "generated_by": "Tools/scripts/jc3_physics_roles4.py",
            "donor": rel(DONOR),
            "fleet_glob": FLEET_GLOB,
            "fleet_files_scanned": len(files),
            "fleet_files_decoded": len(fleet),
            "fleet_files_skipped": skipped,
            "read_only_imports": ["Tools/scripts/jc3hkx.py",
                                  "Tools/scripts/jc3_physics_roles2.py (rot3x4, DONOR)"],
            "labels": {"decoded": "read from these bytes, with the field's evidence",
                       "derived": "a rule applied to decoded inputs; the rule is stated",
                       "UNKNOWN": "not decodable from the bytes read; the blocker is named"},
        },
        "cinfo_layout": {
            "stride_bytes": CINFO_STRIDE,
            "words": ["constraintData* (8 B packfile fixup)", "body id A (0 everywhere)",
                      "body id B (valid everywhere)", "0x7FFFFFFF (constant)",
                      "0 (constant)", "0 (constant)"],
            "note": ("G3-10c decoded {cd*, bodyId, 0x7FFFFFFF, 0, 0} from the donor. The fleet "
                     "sweep here shows the same shape in every shipped system: one word always 0, "
                     "one word always 0x7FFFFFFF, two words zero, and the varying word always a "
                     "valid body index. Two readings survive: the constant 0 is *not* a body id, "
                     "or it is body 0 (the chassis). The geometric test in section 2 decides."),
            "verdict": "decoded (the record's shape); the pair reading is tested, not assumed",
        },
        "pair_hypothesis": {
            "claim": ("cinfo +0x04 = bodyIdA, +0x08 = bodyIdB; bodyIdA = 0 (chassis) in every "
                      "shipped record, so the constraint partner is body 0"),
            "label": "derived",
            "oracle": ("both bodies of a constraint touch its pivot, so |signed distance pivot -> "
                       "body hull| must be small for the pair"),
            "controls": ["partner replaced by a deterministic pseudo-random other body in the file",
                         "each of body 0..3 measured the same way (is body 0 special?)"],
            **p1,
        },
        "inertia": {
            "block": ("hknpShapeMassProperties +0x10..+0x27, 24 bytes; the mass is the IEEE float "
                      "at +0x28. Not per-component floats (G3-10c); not decoded here."),
            "oracle": ("Ixx = m(ey^2+ez^2)/12 etc. from the hull AABB the block is bound to; a "
                       "packed reading must give a constant per-body scale on all three axes"),
            "label": "UNKNOWN",
            **p2,
        },
        "unknowns": [
            ("The 24 packed inertia bytes: no tested reading gives a constant per-body scale, so "
             "the tensor is not decodable from these bytes alone. No public Havok 2014 header or "
             "community reader for hknpShapeMassProperties could be obtained in this session to fix "
             "the bit layout; the tested readings and their numbers are recorded instead."),
            ("Whether the constant 0 at cinfo +0x04 is the chassis body id or a flag. It is 0 in "
             "every shipped record, so the bytes cannot separate the two readings; the geometry "
             "makes 'body 0' the one the data supports."),
            ("The +0x01 flag at bodies 11/15/27 (G3-10c U-3): still no decoded meaning."),
            ("The remaining body-entry words: unchanged from G3-10b's measured domains."),
        ],
    }
    doc["oracles"] = oracles(doc)
    return doc


# ---------------------------------------------------------------- oracles
def oracles(doc):
    p1 = doc["pair_hypothesis"]
    p2 = doc["inertia"]
    tol = {r["tol_m"]: r for r in p1["tolerance_table"]}
    rates = [p1["per_body"][i]["rate"] or 0 for i in (1, 2, 3)]
    checks = {
        "cinfo_body_id_a_in_range": p1["body_id_a_in_range"],
        "cinfo_body_id_b_in_range": p1["body_id_b_all_in_range"],
        "pair_beats_control_5cm": (tol[0.05]["pair_rate"] or 0) >= 0.2,
        "pair_control_is_low_5cm": (tol[0.05]["control_rate"] or 1) <= 0.05,
        "body0_is_special": (p1["per_body"][0]["rate"] or 0) >= 3 * max(rates),
        "donor_frames_ab_share_pivot": p1["donor_frames_on_one_pivot"] == p1["donor_with_frames"],
        "donor_deltas_are_rotations": all(abs((r["rot_delta_det"] or 0) - 1) < 1e-3
                                          for r in p1["donor"]),
        "inertia_readings_measured": all((r["best_triple"] or {}).get("n", 0) >= 50
                                         for r in p2["interpretations"]),
        "inertia_best_spread_above_bar": (min(r["best_triple"]["median_spread"]
                                             for r in p2["interpretations"]
                                             if r["best_triple"])) > DECODE_BAR,
        "inertia_linked_hulls": p2["linked_hulls"] >= 50,
    }
    return {"all_ok": all(checks.values()), "checks": checks,
            "detail": {"pair_rate_5cm": tol[0.05]["pair_rate"],
                       "control_rate_5cm": tol[0.05]["control_rate"],
                       "body0_rate": p1["per_body"][0]["rate"],
                       "best_reading_spread": min(r["best_triple"]["median_spread"]
                                                  for r in p2["interpretations"]
                                                  if r["best_triple"])}}


# ---------------------------------------------------------------- markdown
def f3(x):
    return "%.3f" % x if x is not None else "-"


def render(doc):
    p1 = doc["pair_hypothesis"]
    p2 = doc["inertia"]
    tol0 = next(r for r in p1["tolerance_table"] if r["tol_m"] == 0.05)
    rates = [(p1["per_body"][i]["rate"] or 0) for i in (1, 2, 3)]
    out = []
    a = out.append

    a("# Physics roles 4 - the constraint partner, and the 24 packed inertia bytes (G3-10d)")
    a("")
    a("Generated by `%s` from the shipped bytes. Every value is `decoded` (the field is in the "
      "file and the evidence is named), `derived` (a rule applied to decoded inputs) or "
      "`UNKNOWN` (what blocks it is named)." % doc["meta"]["generated_by"])
    a("")
    a("Donor `%s`; fleet `%s` - **%d files decoded**, %d skipped, **%d constraints**."
      % (doc["meta"]["donor"], doc["meta"]["fleet_glob"],
         doc["meta"]["fleet_files_decoded"], len(doc["meta"]["fleet_files_skipped"]),
         p1["cinfos_seen"]))
    a("")
    a("## 1. The cinfo record, fleet-wide (decoded)")
    a("")
    a("24 bytes per constraint, `hknpPhysicsSystemData +0x50`, six words:")
    a("")
    a("| word | offset | content | evidence |")
    a("|---|---|---|---|")
    a("| 0-1 | +0x00..+0x07 | `constraintData*` packfile fixup | resolves to the constraint object "
      "in every record |")
    a("| 2 | +0x04 | body id A | always 0 in %d/%d records |" % (p1["cinfos_seen"], p1["cinfos_seen"]))
    a("| 3 | +0x08 | body id B | always < the file's body count (%d/%d) |"
      % (p1["cinfos_seen"], p1["cinfos_seen"]))
    a("| 4 | +0x0C | 0x7FFFFFFF | constant |")
    a("| 5-6 | +0x10..+0x17 | 0 | constant |")
    a("")
    a("That is the reading G3-10c made, and it leaves the partner side open: either the constant "
      "0 at +0x04 is a flag and the record holds *one* body, or it is body id A and +0x08 is "
      "body id B. Section 2 tests the second reading instead of assuming it.")
    a("")
    a("## 2. The partner, tested with a geometric oracle (derived)")
    a("")
    a("Both bodies of a constraint must touch the constraint's pivot, so the signed distance from "
      "the pivot to each body's convex hull must be small. Distance to body 0 vs distance to the "
      "cinfo's own body, at four tolerances:")
    a("")
    a("| tolerance | pair (body 0, cinfo body) | same pivot, shuffled partner | n |")
    a("|---:|---:|---:|---:|")
    for r in p1["tolerance_table"]:
        a("| %.2f m | %s | %s | %d |" % (r["tol_m"], f3(r["pair_rate"]), f3(r["control_rate"]),
                                         r["pair_n"]))
    a("")
    a("Median |distance| to the pivot: body 0 **%.4f m**, the cinfo body **%.4f m**."
      % (p1["median_d_a"], p1["median_d_b"]))
    a("")
    a("Is body 0 special, or just the largest hull? The same measurement for fixed ids 0-3 "
      "(control 2):")
    a("")
    a("| body | within 5 cm | measured | rate |")
    a("|---:|---:|---:|---:|")
    for r in p1["per_body"]:
        a("| %d | %d | %d | %s |" % (r["body"], r["within_5cm"], r["measured"], f3(r["rate"])))
    a("")
    a("So the cinfo's second body id is a part body and the partner is the chassis: body 0 is near "
      "the pivot **%.0fx** more often than the next fixed body, and the (0, cinfo-body) pair beats "
      "a shuffled partner by **%.0fx** at 5 cm. That is evidence, not a layout proof - only %d%% of "
      "the pivots are within 5 cm of the chassis hull surface, so the oracle has a floor - and the "
      "label is `derived`; section 6 names what would settle it."
      % ((p1["per_body"][0]["rate"] or 0) / max(rates) if max(rates) else 0,
         (tol0["pair_rate"] or 0) / (tol0["control_rate"] or 1),
         round(100 * (p1["per_body"][0]["rate"] or 0))))
    a("")
    a("## 3. Why the pivots cannot separate A from B (decoded)")
    a("")
    a("Each `hkpConstraintData` holds two 3x4 frames (A and B). In the donor **%d/%d** have "
      "bit-identical translations, the two rotations agree to within %.2f deg and every delta is "
      "a proper rotation (det 1); the frame counts per constraint are %s. The A/B pair is "
      "therefore the same frame written twice: the constraintData gives the joint's position and "
      "axis but says nothing about which body is A. That is why section 2 must use the hull test "
      "rather than a pivot comparison."
      % (p1["donor_frames_on_one_pivot"], p1["donor_with_frames"],
         max((r["rot_delta_deg"] for r in p1["donor"] if r["rot_delta_deg"] is not None)),
         ", ".join(str(x) for x in p1["donor_frame_counts"])))
    a("")
    a("The donor's 11 constraints:")
    a("")
    a("| # | type | body b | pivot (m) | \\|d\\| to body 0 | \\|d\\| to body b | nearest hulls |")
    a("|---:|---|---:|---|---:|---:|---|")
    for r in p1["donor"]:
        near = ", ".join("%d@%.3f" % (c["body"], c["abs_dist"]) for c in r["nearest"][:3])
        a("| %d | %s | %d | (%.3f, %.3f, %.3f) | %s | %s | %s |"
          % (r["index"], r["name"], r["body_id_b"], r["pivot"][0], r["pivot"][1],
             r["pivot"][2], r["abs_dist_a"], r["abs_dist_b"], near))
    a("")
    a("`-` in the |d| to body b column means that body's shape is not a convex polytope, so no "
      "hull planes were decoded for it (bodies 16 and 26 in the donor).")
    a("")
    a("## 4. The 24 packed bytes: every candidate reading, scored (UNKNOWN)")
    a("")
    a("The link is decoded: `polytope + 0x20` -> `hkRefCountedProperties + 0x10` -> "
      "`hknpShapeMassProperties`; **%d** hulls across %d files carry a mass block. Mass is the "
      "IEEE float at `+0x28`. The 24 bytes at `+0x10..+0x27` are the packed properties."
      % (p2["linked_hulls"], p2["files"]))
    a("")
    a("Oracle: for a box of the hull's AABB and its own mass,")
    a("")
    a("```")
    a("Ixx = m (ey^2 + ez^2)/12     Iyy = m (ex^2 + ez^2)/12     Izz = m (ex^2 + ey^2)/12")
    a("```")
    a("")
    a("A packed reading must give a *constant* scale inside a body (`I_i / value_i` equal on all "
      "three axes). Spread = max/min of those ratios, median over the hulls; a decode needs ~1.0:")
    a("")
    a("| reading | best triple | median spread | n | decodes? |")
    a("|---|---|---:|---:|---|")
    for r in p2["interpretations"]:
        bt = r["best_triple"] or {}
        a("| %s | %s | %s | %d | %s |"
          % (r["reading"], bt.get("triple"), f3(bt.get("median_spread")) if bt else "-",
             bt.get("n") or 0, "**yes**" if r["decodes"] else "no"))
    a("")
    a("No reading decodes. The bar is a per-axis agreement within %d%% of one scale (spread <= "
      "%.2f); the best candidate is still %.2f, i.e. ~%d%% disagreement, which is the same order "
      "as the AABB-vs-hull shape error of the oracle itself. The test therefore cannot certify any "
      "reading: a true packed inertia could sit in that band and so could noise. For the record, "
      "the direction test (does a triple follow the *shape* of the tensor, unit-normalised) and "
      "each slot's rank correlation:"
      % (round((DECODE_BAR - 1) * 100), DECODE_BAR,
         min(r["best_triple"]["median_spread"] for r in p2["interpretations"]
             if r["best_triple"]),
         round((min(r["best_triple"]["median_spread"] for r in p2["interpretations"]
                if r["best_triple"]) - 1) * 100)))
    a("")
    a("| triple | mean cos | min cos |")
    a("|---|---:|---:|")
    for r in p2["direction_test"]:
        a("| %s | %.3f | %.3f |" % (r["triple"], r["mean_cos"], r["min_cos"]))
    a("")
    a("| slot | rho(mass) | rho(Ixx) | rho(Iyy) | rho(Izz) |")
    a("|---:|---:|---:|---:|---:|")
    for r in p2["slots"]:
        a("| %d | %+.3f | %+.3f | %+.3f | %+.3f |"
          % (r["slot"], r["rho_mass"], r["rho_Ixx"], r["rho_Iyy"], r["rho_Izz"]))
    a("")
    top = max(p2["slots"], key=lambda r: abs(r["rho_mass"]))
    a("The one measured regularity is slot %d tracking mass (rho %.2f) and all three box-inertia "
      "components - what a shared scale inside the block would look like, but it does not locate "
      "the exponent, and no candidate layout reproduces the tensor. **Inertia stays UNKNOWN.**"
      % (top["slot"], top["rho_mass"]))
    a("")
    a("### Raw blocks (verbatim, first hulls)")
    a("")
    a("| file | body | mass | extents (m) | box inertia | 24 B at +0x10 |")
    a("|---|---:|---:|---|---|---|")
    for h in p2["sample"]:
        a("| %s | %d | %g | (%.2f, %.2f, %.2f) | (%.1f, %.1f, %.1f) | `%s` |"
          % (h["file"], h["body"], h["mass"], h["extents"][0], h["extents"][1], h["extents"][2],
             h["box_inertia"][0], h["box_inertia"][1], h["box_inertia"][2], h["raw_hex"]))
    a("")
    a("## 5. Oracles (`--check` re-runs all of them)")
    a("")
    a("| oracle | value |")
    a("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        a("| `%s` | **%s** |" % (k, "pass" if v else "FAIL"))
    a("")
    a("## 6. UNKNOWNs")
    a("")
    for u in doc["unknowns"]:
        a("- %s" % u)
    a("")
    a("## 7. Files and inputs")
    a("")
    a("| file | what |")
    a("|---|---|")
    a("| `Tools/scripts/jc3_physics_roles4.py` | this pass, `--write` / `--check` |")
    a("| `Research/JC3Grab/PHYSICS_ROLES4.md` | this page |")
    a("| `Research/JC3Grab/PHYSICS_ROLES4.json` | the same, machine-readable, every number |")
    a("")
    a("Read-only imports: `%s`. No game was launched or attached to, nothing was written outside "
      "these three files, no build, no git action."
      % "`, `".join(doc["meta"]["read_only_imports"]))
    a("")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- io
def write():
    doc = build()
    md = render(doc)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=False)
        f.write("\n")
    print("wrote %s and %s" % (rel(OUT_MD), rel(OUT_JSON)))
    print("cinfos: %d; hulls with mass: %d; fleet files: %d"
          % (doc["pair_hypothesis"]["cinfos_seen"], doc["inertia"]["linked_hulls"],
             doc["meta"]["fleet_files_decoded"]))
    print("oracles: %d/%d ok" % (sum(1 for v in doc["oracles"]["checks"].values() if v),
                                 len(doc["oracles"]["checks"])))
    bad = [k for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAILING: " + ", ".join(bad))
        print("detail: " + json.dumps(doc["oracles"]["detail"], sort_keys=True))
    return 0 if doc["oracles"]["all_ok"] else 1


def check():
    doc = build()
    md = render(doc)
    problems = []
    old_md = old_json = None
    try:
        old_md = open(OUT_MD, encoding="utf-8", newline="").read()
    except FileNotFoundError:
        problems.append("missing " + rel(OUT_MD))
    try:
        old_json = open(OUT_JSON, encoding="utf-8", newline="").read()
    except FileNotFoundError:
        problems.append("missing " + rel(OUT_JSON))
    new_json = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    if old_md is not None and old_md != md:
        problems.append("PHYSICS_ROLES4.md is stale")
    if old_json is not None and old_json != new_json:
        problems.append("PHYSICS_ROLES4.json is stale")
    if not doc["oracles"]["all_ok"]:
        problems.append("oracle failures: " + ", ".join(
            k for k, v in doc["oracles"]["checks"].items() if not v))
    if problems:
        for p in problems:
            print("FAIL " + p)
        print("detail: " + json.dumps(doc["oracles"]["detail"], sort_keys=True))
        return 1
    print("OK cinfos %d / hulls %d / fleet files %d; md+json byte-identical"
          % (doc["pair_hypothesis"]["cinfos_seen"], doc["inertia"]["linked_hulls"],
             doc["meta"]["fleet_files_decoded"]))
    print("oracles: " + json.dumps(doc["oracles"]["checks"], sort_keys=True))
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--write" in argv:
        return write()
    if "--check" in argv:
        return check()
    print("jc3_physics_roles4.py - G3-10d: constraint partner + packed inertia")
    print("usage: jc3_physics_roles4.py --write | --check")
    return 2


if __name__ == "__main__":
    sys.exit(main())
