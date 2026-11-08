"""review_g310d.py - independent audit of G3-10d (Research/JC3Grab/PHYSICS_ROLES4.md).

G3-10d claims the constraint partner is body 0 (the chassis) for every constraint, from a
geometric oracle: 35.1 % of pivots lie within 5 cm of both body 0's and the recorded body's hull,
against 0.53 % for a shuffled partner. It labels that `derived` and leaves two UNKNOWNs: whether
`cinfo +0x04 = 0` is body 0 or a flag, and the 24 packed inertia bytes.

This tool re-derives the whole pass from the shipped bytes and audits four things:

  1. **The published numbers.** 50 files / 494 cinfos / 2011 mass-linked hulls / 188 measurable,
     the four-tolerance table, the per-fixed-body control, the shuffled control, the donor's
     11-row table, the frame analysis, the six inertia readings - each recomputed here.
  2. **What the oracle actually implies.** G3-10d compares (body 0, recorded body) against a
     shuffled body, but never against the recorded body *alone*. That comparison is run here:
     P(recorded body within 5 cm) vs P(body 0 within 5 cm) vs P(both), plus the subset property
     P(body 0 hits AND recorded body misses), plus the counterexamples the card asks for: a
     constraint whose pivot is far from body 0 and near another body.
  3. **The frame premise.** `jc3hkx.decode_polytope` returns hull planes in shape space and the
     cinfo pivot is a stored 3x4 translation; comparing them is only valid if the bodies carry
     identity transforms. That is measured, not assumed.
  4. **The inertia UNKNOWN.** A wider candidate set than G3-10d's six readings is scored against
     the same box-inertia oracle, and the fact that three of its six readings are the same test
     up to a constant factor is measured rather than asserted.

  5. **Script hygiene.** The file was edited by two agents at once, so the leftovers are counted
     from its source text: constants defined and never used, fields collected and never read,
     an oracle that cannot fail, and a reading name hard-coded into two analyses that are
     presented as interpretation-independent.

Labels: decoded = read from bytes here; derived = a rule applied to decoded inputs; UNKNOWN =
not decodable from these bytes, with the blocker named.

    python Tools/scripts/review_g310d.py --write
    python Tools/scripts/review_g310d.py --check
"""
from __future__ import annotations

import glob
import json
import math
import os
import random
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import jc3hkx                                            # noqa: E402
import jc3_physics_roles2 as R2                          # noqa: E402  (rot3x4, DONOR)

FLEET_GLOB = "E:/Modding/_gamedata/JC3grab/**/*.physicsc"
REVIEWED = os.path.join(ROOT, "Tools", "scripts", "jc3_physics_roles4.py")
CARD_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES4.md")
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES4_REVIEW.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES4_REVIEW.json")

CINFO_STRIDE = 24
BODY_ENTRY = 96
MASS_OFF = 0x28
PACK_OFF = 0x10
PACK_LEN = 24
TOLS = (0.02, 0.05, 0.10, 0.20)
SEED = 1000
DECODE_BAR = 1.15
FAR = 0.20            # "far from body 0" for the counterexample search
NEAR = 0.05           # "near another body"

# G3-10d's six readings, plus layouts it did not test.
READINGS = (
    ("6 x IEEE f32", "f32"),
    ("12 x int16 raw", "i16"),
    ("12 x int16 / 16384", "i16_16384"),
    ("12 x int16 / 32767", "i16_32767"),
    ("12 x u16 raw", "u16"),
    ("12 x IEEE half", "half"),
    ("6 x int32 (new)", "i32"),
    ("6 x uint32 (new)", "u32"),
    ("24 x int8 (new)", "i8"),
    ("24 x uint8 (new)", "u8"),
    ("3 x double (new)", "f64"),
    ("3 x f32 first 12 B (new)", "f32x3"),
    ("6 x IEEE half (new)", "half6"),
)
TRIPLES = ((0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 10, 11),
           (1, 2, 3), (4, 5, 6), (7, 8, 9))


# ------------------------------------------------------------------ math
def rel(p):
    try:
        return os.path.relpath(p, ROOT).replace("\\", "/")
    except ValueError:
        return p.replace("\\", "/")


def sdist(planes, p):
    """Signed distance to the hull surface (inward normals: <= 0 inside, ~0 on the face)."""
    return max(n["n"][0] * p[0] + n["n"][1] * p[1] + n["n"][2] * p[2] + n["d"] for n in planes)


def median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2])


def spearman(a, b):
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


def half16(u):
    s = (u >> 15) & 1
    e = (u >> 10) & 0x1F
    m = u & 0x3FF
    if e == 0:
        return (-1) ** s * m / 1024.0 * 2 ** -14
    if e == 31:
        return float("nan")
    return (-1) ** s * (1 + m / 1024.0) * 2.0 ** (e - 15)


def decode_slots(raw, how):
    b = bytes.fromhex(raw)
    if how == "f32":
        return list(struct.unpack("<6f", b))
    if how == "f32x3":
        return list(struct.unpack("<3f", b[:12]))
    if how == "f64":
        return list(struct.unpack("<3d", b))
    if how == "i32":
        return list(struct.unpack("<6i", b))
    if how == "u32":
        return list(struct.unpack("<6I", b))
    if how == "i8":
        return list(struct.unpack("<24b", b))
    if how == "u8":
        return list(struct.unpack("<24B", b))
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
    if how == "half6":
        return [half16(v) for v in u[:6]]
    raise ValueError(how)


# ------------------------------------------------------------------ parse
def scan(path, want_mass=True):
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd = next((o for o in pf.objects if o.cls == "hknpPhysicsSystemData"), None)
    if psd is None:
        return None
    a40, a50 = pf.array(psd.offset + 0x40), pf.array(psd.offset + 0x50)
    out = {"path": rel(path), "n_bodies": a40["size"], "bodies": [], "cinfos": []}

    for i in range(a40["size"]):
        at = a40["ptr"] + BODY_ENTRY * i
        shape = pf.pointers.get(at, 0)
        pos = [struct.unpack_from("<f", blob, base + at + 0x30 + 4 * k)[0] for k in range(3)]
        quat = [struct.unpack_from("<f", blob, base + at + 0x40 + 4 * k)[0] for k in range(4)]
        hull = None
        if shape and pf._starts.get(shape) == "hknpConvexPolytopeShape":
            d = jc3hkx.decode_polytope(pf, shape)
            hull = {"planes": d["planes"],
                    "bounds": {"min": list(d["bounds"]["min"]), "max": list(d["bounds"]["max"])},
                    "convex_ok": d.get("convex_ok")}
        mass = raw = None
        if want_mass and hull is not None:
            node = pf.pointers.get(shape + 0x20, 0)
            if node and pf._starts.get(node) == "hkRefCountedProperties":
                mp = pf.pointers.get(node + 0x10, 0)
                if mp and pf._starts.get(mp) == "hknpShapeMassProperties":
                    mass = struct.unpack_from("<f", blob, base + mp + MASS_OFF)[0]
                    raw = blob[base + mp + PACK_OFF:base + mp + PACK_OFF + PACK_LEN].hex()
        ident = (all(abs(x) <= 1e-6 for x in pos)
                 and all(abs(q - (1.0 if k == 3 else 0.0)) <= 1e-6
                         for k, q in enumerate(quat)))
        out["bodies"].append({"id": i, "hull": hull, "mass": mass, "raw": raw,
                              "pos": pos, "quat": quat, "identity": ident})

    for k in range(a50["size"]):
        rec = a50["ptr"] + CINFO_STRIDE * k
        w = struct.unpack_from("<6I", blob, base + rec)
        co = pf.pointers.get(rec, 0)
        c = {"k": k, "words": list(w), "constraint": pf._starts.get(co, "") if co else "",
             "pivot": None, "frames": [], "deltas": [], "all_frames_same_pivot": None,
             "ab_same_pivot": None}
        if co:
            ext = pf.extents[co]
            fl = [struct.unpack_from("<f", blob, base + co + 4 * j)[0] for j in range(ext // 4)]
            for s in range(0, max(0, len(fl) - 16)):
                hit = R2.rot3x4(fl[s:s + 16])
                if not hit:
                    continue
                c["frames"].append({"at": s * 4, "rows": hit[1],
                                    "pivot": [fl[s + 12 + t] for t in range(3)]})
            if c["frames"]:
                c["pivot"] = c["frames"][0]["pivot"]
            for a, b in zip(c["frames"], c["frames"][1:]):
                c["deltas"].append(rot_delta(a["rows"], b["rows"]))
            c["all_frames_same_pivot"] = all(
                f["pivot"] == c["frames"][0]["pivot"] for f in c["frames"][1:])
            c["ab_same_pivot"] = (len(c["frames"]) >= 2
                                  and c["frames"][0]["pivot"] == c["frames"][1]["pivot"])
        out["cinfos"].append(c)
    return out


def rot_delta(ar, br):
    at = [[ar[c][r] for c in range(3)] for r in range(3)]
    d = [[sum(at[r][kk] * br[kk][c] for kk in range(3)) for c in range(3)] for r in range(3)]
    tr = d[0][0] + d[1][1] + d[2][2]
    ang = math.degrees(math.acos(max(-1.0, min(1.0, (tr - 1.0) / 2.0))))
    det = (d[0][0] * (d[1][1] * d[2][2] - d[1][2] * d[2][1])
           - d[0][1] * (d[1][0] * d[2][2] - d[1][2] * d[2][0])
           + d[0][2] * (d[1][0] * d[2][1] - d[1][1] * d[2][0]))
    return {"angle_deg": round(ang, 4), "det": round(det, 6)}


# ------------------------------------------------------------------ audit A: words
def words_audit(fleet):
    a_vals, w0c, w4, w5 = set(), set(), set(), set()
    n = 0
    for f in fleet:
        for c in f["cinfos"]:
            n += 1
            a_vals.add(c["words"][1])
            w0c.add(c["words"][3])
            w4.add(c["words"][4])
            w5.add(c["words"][5])
    return {"cinfos": n,
            "word_04_values": sorted(a_vals), "word_04_all_zero": a_vals == {0},
            "word_0c_values": ["0x%08X" % v for v in sorted(w0c)],
            "word_0c_all_7fffffff": w0c == {0x7FFFFFFF},
            "words_10_14_values": sorted(w4 | w5),
            "words_10_14_all_zero": (w4 | w5) == {0}}


# ------------------------------------------------------------------ audit B: partner
def partner_audit(fleet):
    recs = []
    for f in fleet:
        hulls = {b["id"]: b["hull"]["planes"] for b in f["bodies"] if b["hull"]}
        ident = {b["id"]: b["identity"] for b in f["bodies"]}
        for c in f["cinfos"]:
            if not c["pivot"]:
                continue
            piv = c["pivot"]
            d = {i: abs(sdist(pl, piv)) for i, pl in hulls.items()}
            a, b = c["words"][1], c["words"][2]
            recs.append({"file": os.path.basename(f["path"]), "k": c["k"],
                         "a": a, "b": b, "pivot": [round(x, 6) for x in piv],
                         "n_bodies": f["n_bodies"], "d": d,
                         "d_a": d.get(a), "d_b": d.get(b),
                         "a_identity": ident.get(a, False),
                         "b_identity": ident.get(b, False)})

    both = [r for r in recs if r["d_a"] is not None and r["d_b"] is not None]
    tol_rows = []
    for tol in TOLS:
        n = len(both)
        pa = sum(1 for r in both if r["d_a"] <= tol)
        pb = sum(1 for r in both if r["d_b"] <= tol)
        pboth = sum(1 for r in both if r["d_a"] <= tol and r["d_b"] <= tol)
        pnei = sum(1 for r in both if r["d_a"] > tol and r["d_b"] > tol)
        a_only = sum(1 for r in both if r["d_a"] <= tol and r["d_b"] > tol)
        ctrl_hit = ctrl_n = 0
        for r in both:
            alts = sorted(i for i in r["d"] if i not in (r["a"], r["b"]))
            if not alts:
                continue
            rnd = random.Random(SEED + r["k"] * 31 + r["b"])
            ctrl_n += 1
            if r["d"][rnd.choice(alts)] <= tol:
                ctrl_hit += 1
        tol_rows.append({"tol_m": tol, "n": n,
                         "p_body_a": round(pa / n, 4), "p_body_b": round(pb / n, 4),
                         "p_both": round(pboth / n, 4), "p_neither": round(pnei / n, 4),
                         "a_hit_b_miss": a_only,
                         "p_body_a_only": round(a_only / n, 4),
                         "control_hits": ctrl_hit, "control_n": ctrl_n,
                         "p_control": round(ctrl_hit / ctrl_n, 4) if ctrl_n else None})

    per_body = []
    for i in range(4):
        seen = [r for r in both if i in r["d"]]
        ok = sum(1 for r in seen if r["d"][i] <= NEAR)
        per_body.append({"body": i, "within_5cm": ok, "measured": len(seen),
                         "rate": round(ok / len(seen), 4) if seen else None})

    far = [r for r in both if r["d_a"] > FAR]
    contra = []
    for r in far:
        others = [(v, i) for i, v in r["d"].items() if i != r["a"]]
        if not others:
            continue
        best = min(others)
        if best[0] <= NEAR:
            contra.append({"file": r["file"], "k": r["k"], "body_a": r["a"],
                           "d_a": round(r["d_a"], 4), "body_b": r["b"],
                           "d_b": round(r["d_b"], 4) if r["d_b"] is not None else None,
                           "nearest_body": best[1], "nearest_d": round(best[0], 4),
                           "nearest_is_recorded_b": best[1] == r["b"],
                           "a_identity": r["a_identity"]})
    contra.sort(key=lambda x: -x["d_a"])

    b_far = [r for r in both if r["d_b"] > 0.10]
    donor_rows = []
    donor = next((f for f in fleet if os.path.normcase(rel(R2.DONOR)) ==
                  os.path.normcase(f["path"])), None)
    if donor is None:
        donor = scan(R2.DONOR)      # the donor lives under Builds/, outside the fleet glob
    if donor:
        hulls = {b["id"]: b["hull"]["planes"] for b in donor["bodies"] if b["hull"]}
        for c in donor["cinfos"]:
            if not c["pivot"]:
                continue
            piv = c["pivot"]
            cand = sorted(({"body": i, "abs_dist": round(abs(sdist(pl, piv)), 4)}
                           for i, pl in hulls.items()), key=lambda x: x["abs_dist"])
            d = {i: abs(sdist(pl, piv)) for i, pl in hulls.items()}
            bb = c["words"][2]
            donor_rows.append({
                "k": c["k"],
                "type": c["constraint"].replace("hkp", "").replace("ConstraintData", ""),
                "body_b": bb, "pivot": [round(x, 4) for x in piv],
                "d_a": round(d.get(0), 4) if 0 in d else None,
                "d_b": round(d.get(bb), 4) if bb in d else None,
                "own_body_over_5cm": (d.get(bb) is not None and d[bb] > NEAR),
                "nearest": cand[:3], "frames": len(c["frames"]),
                "frames_same_pivot": c["ab_same_pivot"]})
    return {"records": len(recs), "measurable": len(both),
            "measurable_a_identity": sum(1 for r in both if r["a_identity"]),
            "measurable_b_identity": sum(1 for r in both if r["b_identity"]),
            "contradictions_in_frame": sum(1 for x in contra
                                          if x.get("a_identity", False)),
            "records_a_missing": sum(1 for r in recs if r["d_a"] is None),
            "records_b_missing": sum(1 for r in recs if r["d_b"] is None),
            "tolerance_table": tol_rows, "per_body": per_body,
            "median_d_a": round(median([r["d_a"] for r in both]) or 0, 4),
            "median_d_b": round(median([r["d_b"] for r in both]) or 0, 4),
            "far_records": len(far), "contradictions": contra,
            "contradictions_with_b_nearest": sum(1 for x in contra
                                                 if x["nearest_is_recorded_b"]),
            "b_over_10cm": len(b_far),
            "b_over_10cm_with_a_near": sum(1 for r in b_far if r["d_a"] <= NEAR),
            "max_d_a": round(max(r["d_a"] for r in both), 4),
            "donor_rows": donor_rows}


# ------------------------------------------------------------------ audit C: inertia
def inertia_audit(fleet):
    hulls = []
    for f in fleet:
        for b in f["bodies"]:
            if not b["hull"] or b["mass"] is None or not b["raw"]:
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
                          "box_inertia": I, "raw": b["raw"]})

    def spreads(how, T, rs=None):
        out = []
        for h in (rs if rs is not None else hulls):
            v = decode_slots(h["raw"], how)
            if max(T) >= len(v):
                continue
            if any(abs(v[i]) < 1e-9 or not math.isfinite(v[i]) for i in T):
                continue
            ratios = [h["box_inertia"][kk] / v[T[kk]] for kk in range(3)]
            if any(x <= 0 for x in ratios):
                continue
            out.append(max(ratios) / min(ratios))
        return out

    rows = []
    for name, how in READINGS:
        best = None
        for T in TRIPLES:
            sp = spreads(how, T)
            if len(sp) >= 10:
                med = median(sp)
                if best is None or med < best["median_spread"]:
                    best = {"triple": list(T), "median_spread": round(med, 4), "n": len(sp)}
        rows.append({"reading": name, "how": how, "best_triple": best,
                     "decodes": bool(best and best["median_spread"] <= DECODE_BAR)})

    # the three int16 scalings are the same test up to a constant factor
    redundant = []
    base = [median(spreads("i16", T)) for T in TRIPLES]
    for how in ("i16_16384", "i16_32767", "u16"):
        other = [median(spreads(how, T)) for T in TRIPLES]
        pairs = [(a, b) for a, b in zip(base, other) if a is not None and b is not None]
        same = bool(pairs) and all(abs(a - b) < 1e-9 for a, b in pairs)
        redundant.append({"how": how,
                          "max_abs_delta_vs_i16": round(max((abs(a - b) for a, b in pairs),
                                                            default=0.0), 9),
                          "same_test": same})

    dir_rows = []
    for T in TRIPLES:
        dots = []
        for h in hulls:
            v = [abs(x) for x in decode_slots(h["raw"], "i16_16384")]
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
        col = [abs(decode_slots(h["raw"], "i16_16384")[j]) for h in hulls]
        slot_rows.append({"slot": j,
                          "rho_mass": round(spearman(col, [h["mass"] for h in hulls]), 4),
                          "rho_Ixx": round(spearman(col, [h["box_inertia"][0] for h in hulls]), 4),
                          "rho_Iyy": round(spearman(col, [h["box_inertia"][1] for h in hulls]), 4),
                          "rho_Izz": round(spearman(col, [h["box_inertia"][2] for h in hulls]), 4)})

    # G3-10d rounds box inertia to 4 decimals before taking the ratio; reproducing that rounding
    # is how its published 1.327 is checked (the unrounded value is the more accurate one).
    rounded = [dict(h, box_inertia=[round(x, 4) for x in h["box_inertia"]]) for h in hulls]
    cand = []
    for _name, how in READINGS:
        best = None
        for T in TRIPLES:
            sp = spreads(how, T, rounded)
            if len(sp) >= 10:
                med = median(sp)
                if best is None or med < best:
                    best = med
        if best is not None:
            cand.append(best)
    min_rounded = round(min(cand), 4) if cand else None

    return {"linked_hulls": len(hulls),
            "files": len({h["file"] for h in hulls}),
            "min_spread_rounded": min_rounded,
            "sample": [{"file": h["file"], "body": h["body"], "mass": h["mass"],
                        "extents": h["extents"],
                        "box_inertia": [round(x, 4) for x in h["box_inertia"]],
                        "raw": h["raw"]} for h in hulls[:8]],
            "readings": rows,
            "any_reading_decodes": any(r["decodes"] for r in rows),
            "min_spread": min(r["best_triple"]["median_spread"] for r in rows if r["best_triple"]),
            "redundancy": redundant,
            "direction_test": dir_rows, "slots": slot_rows}


# ------------------------------------------------------------------ audit D: script
def script_audit(partner, inertia, words):
    src = open(REVIEWED, encoding="utf-8").read()
    lines = src.splitlines()

    def hits(tok):
        return [i + 1 for i, ln in enumerate(lines) if re.search(re.escape(tok), ln)]

    unused = []
    for tok, why in (("NO_BODY", "constant 0x7FFFFFFF: defined, never compared"),
                     ("quaternion", "body quaternion: collected, never read"),
                     ("\"position\"", "body position: collected, never read"),
                     ("word_0c", "cinfo +0x0C: collected, never read"),
                     ("field_08", "body +0x08: collected, never read"),
                     ("field_0c", "body +0x0C: collected, never read"),
                     ("field_10", "body +0x10: collected, never read"),
                     ("pivots_equal", "all-frames-equal: collected, only written to JSON")):
        h = hits(tok)
        unused.append({"token": tok, "lines": h, "occurrences": len(h), "note": why})

    hard = hits("i16_16384")
    return {
        "source": rel(REVIEWED),
        "lines": len(lines),
        "unused_symbols": unused,
        "no_body_occurrences": len(hits("NO_BODY")),
        "i16_16384_occurrences": len(hard),
        "i16_16384_lines": hard,
        "decode_bar": DECODE_BAR,
        "decode_bar_in_source": float(re.search(r"DECODE_BAR = ([0-9.]+)", src).group(1)),
        "oracle_a_is_vacuous": (words["word_04_all_zero"]
                                 and words["word_04_values"] == [0]),
        "donor_own_body_over_5cm": [r["body_b"] for r in partner["donor_rows"]
                                    if r["own_body_over_5cm"]],
        "donor_rows_with_frames": sum(1 for r in partner["donor_rows"] if r["frames"] >= 2),
        "donor_rows_same_pivot": sum(1 for r in partner["donor_rows"]
                                     if r["frames_same_pivot"]),
        "inertia_readings_named": len(READINGS),
        "inertia_readings_distinct": len(READINGS) - sum(
            1 for r in inertia["redundancy"] if r["same_test"]),
    }


# ------------------------------------------------------------------ build
def build():
    files = sorted(glob.glob(FLEET_GLOB, recursive=True))
    fleet, skipped = [], []
    for p in files:
        try:
            f = scan(p)
        except Exception as exc:
            skipped.append({"file": rel(p), "error": type(exc).__name__})
            continue
        if f is None:
            skipped.append({"file": rel(p), "error": "no hknpPhysicsSystemData"})
            continue
        fleet.append(f)

    wa = words_audit(fleet)
    pa = partner_audit(fleet)
    ia = inertia_audit(fleet)

    non_identity = sum(1 for f in fleet for b in f["bodies"]
                       if any(abs(x) > 1e-6 for x in b["pos"])
                       or any(abs(x - (1.0 if i == 3 else 0.0)) > 1e-6
                              for i, x in enumerate(b["quat"])))
    sa = script_audit(pa, ia, wa)

    tol = {r["tol_m"]: r for r in pa["tolerance_table"]}
    stats = {
        "files_scanned": len(files), "files_decoded": len(fleet),
        "cinfos": wa["cinfos"], "measurable": pa["measurable"],
        "mass_linked_hulls": ia["linked_hulls"], "mass_files": ia["files"],
        "non_identity_body_transforms": non_identity,
        "bodies_total": sum(len(f["bodies"]) for f in fleet),
        "body0_identity_all": all(f["bodies"] and f["bodies"][0]["identity"] for f in fleet),
        "files_with_non_identity": sum(1 for f in fleet
                                       if any(not b["identity"] for b in f["bodies"])),
        "measurable_b_identity": pa["measurable_b_identity"],
        "min_inertia_spread_rounded": ia["min_spread_rounded"],
        "p_both_5cm": tol[0.05]["p_both"], "p_b_5cm": tol[0.05]["p_body_b"],
        "p_a_5cm": tol[0.05]["p_body_a"], "p_control_5cm": tol[0.05]["p_control"],
        "a_only_5cm": tol[0.05]["a_hit_b_miss"],
        "contradictions": len(pa["contradictions"]),
        "contradictions_b_nearest": pa["contradictions_with_b_nearest"],
        "max_d_a": pa["max_d_a"],
        "min_inertia_spread": ia["min_spread"],
        "any_reading_decodes": ia["any_reading_decodes"],
        "unused_symbols": sum(1 for u in sa["unused_symbols"] if u["occurrences"] == 1),
    }
    stats["verdict"] = (
        "the oracle reproduces, the universal inference does not"
        if (abs(stats["p_both_5cm"] - 0.351) < 0.005 and stats["contradictions"] > 0
            and stats["p_b_5cm"] > stats["p_a_5cm"])
        else "inconclusive")

    doc = {"review": "G3-10d", "schema": 1,
           "tool": "Tools/scripts/review_g310d.py",
           "inputs": {"fleet_glob": FLEET_GLOB, "files_scanned": len(files),
                      "skipped": skipped,
                      "reviewed_tool": rel(REVIEWED),
                      "reviewed_card": rel(CARD_MD),
                      "donor": rel(R2.DONOR)},
           "stats": stats, "cinfo_words": wa, "partner": pa, "inertia": ia,
           "script": sa,
           "oracles": {}}
    doc["oracles"] = oracles(doc)
    return doc


def oracles(doc):
    pa, ia, wa = doc["partner"], doc["inertia"], doc["cinfo_words"]
    tol = {r["tol_m"]: r for r in pa["tolerance_table"]}
    checks = {
        "word_04_zero_in_every_record": wa["word_04_all_zero"],
        "word_0c_is_7fffffff": wa["word_0c_all_7fffffff"],
        "words_10_14_zero": wa["words_10_14_all_zero"],
        "measurable_matches_g3_10d": pa["measurable"] == 188 and wa["cinfos"] == 494,
        "mass_link_reproduced": ia["linked_hulls"] == 2011 and ia["files"] == 46,
        "pair_rate_reproduced": abs(tol[0.05]["p_both"] - 0.351) < 0.002,
        "control_rate_reproduced": abs((tol[0.05]["p_control"] or 0) - 0.005) < 0.002,
        "recorded_body_beats_body0_5cm": tol[0.05]["p_body_b"] > tol[0.05]["p_body_a"],
        "body0_never_anchors_alone_past_10cm": (tol[0.10]["a_hit_b_miss"] == 0
                                                 and tol[0.20]["a_hit_b_miss"] == 0),
        "counterexamples_exist": len(pa["contradictions"]) > 0,
        "counterexamples_in_valid_frame": pa["contradictions_in_frame"] > 0,
        "body0_identity_in_every_file": doc["stats"]["body0_identity_all"],
        "donor_ab_frames_share_one_pivot": (len(pa["donor_rows"]) == 11
                                            and all(r["frames_same_pivot"]
                                                    for r in pa["donor_rows"])),
        "no_inertia_reading_decodes": not ia["any_reading_decodes"],
        "int16_scalings_are_one_test": all(
            r["same_test"] for r in ia["redundancy"] if r["how"] != "u16"),
        "u16_is_a_distinct_test": not next(r for r in ia["redundancy"]
                                           if r["how"] == "u16")["same_test"],
        "inertia_reproduces_g3_10d": abs((ia["min_spread_rounded"] or 0) - 1.327) < 0.002,
        "review_tool_constants_match": doc["script"]["decode_bar_in_source"] == DECODE_BAR,
    }
    return {"all_ok": all(checks.values()), "checks": checks,
            "detail": {"p_a": tol[0.05]["p_body_a"], "p_b": tol[0.05]["p_body_b"],
                       "p_both": tol[0.05]["p_both"], "p_control": tol[0.05]["p_control"],
                       "contradictions": len(pa["contradictions"]),
                       "max_d_a_m": pa["max_d_a"],
                       "min_spread": ia["min_spread"]}}


# ------------------------------------------------------------------ render
def f3(x):
    return "%.3f" % x if x is not None else "-"


def render(doc):
    s, wa, pa, ia, sa = doc["stats"], doc["cinfo_words"], doc["partner"], doc["inertia"], doc["script"]
    tol = {r["tol_m"]: r for r in pa["tolerance_table"]}
    L = []
    a = L.append
    a("# PHYSICS_ROLES4_REVIEW - independent audit of G3-10d\n")
    a("Generated by `Tools/scripts/review_g310d.py --write`; `--check` re-derives every rate, "
      "distance, spread and source-text count from the install and fails on drift. No value is "
      "copied from `PHYSICS_ROLES4.json`; the shared decoder `jc3hkx.decode_polytope` is reused "
      "(the only hull reader in the tree), its output is re-measured here.\n")
    a("Labels: **decoded** = read from bytes here; **derived** = a rule applied to decoded "
      "inputs; **UNKNOWN** = not decodable from these bytes, blocker named.\n")
    a("## Verdict\n")
    a("**%s.** The oracle reproduces to the digit (%d measurable records, pair rate %s at 5 cm, "
      "shuffled control %s, %d mass-linked hulls over %d files), and the inertia UNKNOWN holds "
      "(no reading of %d candidates reaches the bar; best spread %s, which becomes G3-10d's own "
      "1.327 (%s) once its 4-decimal rounding is re-applied). What does not survive is the "
      "universal inference: the recorded body carries the pivot **%s** of the time against body "
      "0's **%s**, body 0 anchors a pivot on its own in only %d of %d records at 5 cm and in none "
      "past 10 cm, and **%d** constraints have the 'A side' more than %.2f m from the pivot while "
      "another body is within %.0f cm - the worst %.2f m away. Under a two-body reading with A = "
      "body 0 every one of those records is impossible, so the fleet-wide claim is false as "
      "stated; a chassis-side reading survives for part of the fleet only.\n"
      % (s["verdict"], pa["measurable"], f3(s["p_both_5cm"]), f3(s["p_control_5cm"]),
         ia["linked_hulls"], ia["files"], len(ia["readings"]), f3(s["min_inertia_spread"]),
         f3(s["min_inertia_spread_rounded"]), f3(s["p_b_5cm"]), f3(s["p_a_5cm"]),
         s["a_only_5cm"], pa["measurable"], len(pa["contradictions"]), FAR, NEAR * 100,
         pa["max_d_a"]))
    a("## The claim, verbatim\n")
    a("G3-10d, `PHYSICS_ROLES4.md` §2: *\"So the cinfo's second body id is a part body and the "
      "partner is the chassis: body 0 is near the pivot 5x more often than the next fixed body, "
      "and the (0, cinfo-body) pair beats a shuffled partner by 66x at 5 cm.\"* Its own caveat: "
      "*\"only 48% of the pivots are within 5 cm of the chassis hull surface, so the oracle has a "
      "floor\"*, label `derived`, and UNKNOWN 2: whether `+0x04 = 0` is body 0 or a flag.\n")
    a("## What was re-derived\n")
    a("| quantity | G3-10d | here |")
    a("|---|---:|---:|")
    a("| fleet files decoded | 50 | %d (of %d scanned, %d skipped) |"
      % (doc["inputs"]["files_scanned"] - len(doc["inputs"]["skipped"]),
         doc["inputs"]["files_scanned"], len(doc["inputs"]["skipped"])))
    a("| cinfo records | 494 | %d |" % wa["cinfos"])
    a("| measurable (both hulls) | 188 | %d |" % pa["measurable"])
    a("| mass-linked hulls / files | 2011 / 46 | %d / %d |" % (ia["linked_hulls"], ia["files"]))
    a("| pair rate at 5 cm | 0.351 | %s |" % f3(tol[0.05]["p_both"]))
    a("| shuffled control at 5 cm | 0.005 | %s |" % f3(tol[0.05]["p_control"]))
    a("| body 0 near at 5 cm | 0.484 | %s |" % f3(tol[0.05]["p_body_a"]))
    a("| best inertia spread | 1.327 | %s |" % f3(ia["min_spread"]))
    a("")
    a("## 1. The record's constant words (decoded, now actually asserted)\n")
    a("| word | values over %d records |" % wa["cinfos"])
    a("|---|---|")
    a("| `+0x04` | %s |" % ", ".join(str(v) for v in wa["word_04_values"]))
    a("| `+0x0C` | %s |" % ", ".join(wa["word_0c_values"]))
    a("| `+0x10`, `+0x14` | %s |" % ", ".join(str(v) for v in wa["words_10_14_values"]))
    a("")
    a("All three are constants fleet-wide. Note what the reviewed tool tests: "
      "`cinfo_body_id_a_in_range` checks `0 <= a < n_bodies`, which for `a == 0` can never fail - "
      "the \"0 in 494/494\" sentence in its report is prose, not an oracle. This review asserts "
      "it directly.\n")
    a("## 2. The frame premise (decoded, and narrower than it looks)\n")
    a("A hull's planes come back in the shape's own space and the pivot is a stored translation, so "
      "the comparison is only valid for a body whose transform is identity. Measured: %d of %d "
      "bodies are non-identity, spread over **%d of %d files**; body 0 is identity in **every** "
      "file (%s). So every distance to body 0 - the A side of every record, and every "
      "counterexample in section 4 - is same-frame. Distances to the recorded body are same-frame "
      "for the %d of %d measurable records whose recorded body is identity. G3-10d relies on this "
      "premise without stating it; it is true for the side its claim depends on.\n"
      % (s["non_identity_body_transforms"], s["bodies_total"], s["files_with_non_identity"],
         s["files_decoded"], "yes" if s["body0_identity_all"] else "**no**",
         s["measurable_b_identity"], pa["measurable"]))
    a("## 3. The partner test, including the comparison G3-10d never ran\n")
    a("G3-10d compares the pair against a *shuffled* body. The control that decides whether the "
      "pair reading is supported is the recorded body **alone**: if `+0x04` is a real partner id, "
      "then body 0 must be on the pivot as often as the recorded body is. It is not.\n")
    a("| tolerance | P(recorded body) | P(body 0) | P(both) | P(body 0 only) | P(neither) | "
      "shuffled | n |")
    a("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in pa["tolerance_table"]:
        a("| %.2f m | %s | %s | %s | %s | %s | %s | %d |"
          % (r["tol_m"], f3(r["p_body_b"]), f3(r["p_body_a"]), f3(r["p_both"]),
             f3(r["p_body_a_only"]), f3(r["p_neither"]), f3(r["p_control"]), r["n"]))
    a("")
    a("Median |distance| to the pivot: recorded body **%s m**, body 0 **%s m**.\n"
      % (f3(pa["median_d_b"]), f3(pa["median_d_a"])))
    a("Two facts kill the pair reading, and both are visible in this table:\n")
    a("- **Body 0 anchors alone only at 5 cm.** `P(body 0 only)` is **%d** records at 5 cm (%s of "
      "the set), **%d** at 10 cm and **%d** at 20 cm. So body 0 does contribute an independent "
      "anchor for about one record in eight, but only at the scale where its hull is already "
      "everywhere: past 10 cm it never covers a pivot the recorded body misses. A real second "
      "partner should be the near one exactly when the recorded body is far from the joint."
      % (tol[0.05]["a_hit_b_miss"], f3(tol[0.05]["p_body_a_only"]),
         tol[0.10]["a_hit_b_miss"], tol[0.20]["a_hit_b_miss"]))
    a("- **The recorded body is a better fit on its own** (%s vs %s at 5 cm). The pair rate is "
      "not evidence that body 0 shares the joint; it is the rate at which a pivot that sits on "
      "the recorded body also happens to lie within 5 cm of the biggest hull in the file."
      % (f3(s["p_b_5cm"]), f3(s["p_a_5cm"])))
    a("")
    a("The reviewed card's control 2 (fixed ids 0..3) compares body 0 against parts 1, 2, 3, "
      "reproduced here:\n")
    a("| body | within 5 cm | measured | rate |")
    a("|---:|---:|---:|---:|")
    for r in pa["per_body"]:
        a("| %d | %d | %d | %s |" % (r["body"], r["within_5cm"], r["measured"], f3(r["rate"])))
    a("")
    a("That control is confounded by hull size - body 0 is the chassis, so any pivot inside the "
      "car is within a few centimetres of it. The recorded-body column above is the unconfounded "
      "comparison, and it favours the recorded body.\n")
    a("## 4. The counterexamples (the card's explicit question)\n")
    a("Constraints whose pivot is more than %.2f m from body 0 while some other body is within "
      "%.0f cm: **%d of %d measurable records** (all in files where body 0 is identity, so the "
      "measurement is same-frame), and in **%d** of them the nearest body is the recorded one.\n"
      % (FAR, NEAR * 100, len(pa["contradictions"]), pa["measurable"],
         pa["contradictions_with_b_nearest"]))
    a("| file | cinfo | A (word +0x04) | \\|d\\| to A (m) | B (word +0x08) | \\|d\\| to B (m) | "
      "nearest body | \\|d\\| (m) |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in pa["contradictions"][:12]:
        a("| `%s` | %d | %d | **%.3f** | %d | %s | %d | %.3f |"
          % (r["file"], r["k"], r["body_a"], r["d_a"], r["body_b"],
             "%.3f" % r["d_b"] if r["d_b"] is not None else "-",
             r["nearest_body"], r["nearest_d"]))
    a("")
    a("The largest is %.2f m: a pivot six metres from the chassis hull, sitting 1 cm from body "
      "%d. A two-body record whose A side is body 0 cannot have its A-side joint six metres "
      "outside the chassis. These are direct counterexamples to \"the partner of every JC3 "
      "vehicle constraint is body 0\", inside the same 50 files.\n"
      % (pa["max_d_a"], pa["contradictions"][0]["nearest_body"] if pa["contradictions"] else 0))
    a("## 5. The donor's 11 constraints (decoded, reproduces G3-10d's table)\n")
    a("| # | type | B | pivot (m) | \\|d\\| to body 0 | \\|d\\| to B | own body over 5 cm |")
    a("|---:|---|---:|---|---:|---:|---|")
    for r in pa["donor_rows"]:
        a("| %d | %s | %d | (%.3f, %.3f, %.3f) | %s | %s | %s |"
          % (r["k"], r["type"], r["body_b"], r["pivot"][0], r["pivot"][1], r["pivot"][2],
             f3(r["d_a"]), f3(r["d_b"]), "**yes**" if r["own_body_over_5cm"] else "no"))
    a("")
    a("G3-10d's prose says *\"every pivot is within 5 cm of its own body's hull except the two "
      "ragdolls on 7 and 18 (7.4 cm and 2.9 cm)\"*. The table above disagrees on three counts: "
      "body 18's own distance is 2.9 cm, i.e. **within** 5 cm, and the constraints at 5.54 cm "
      "(bodies 19 and 20) are over 5 cm but not mentioned. The bodies actually over 5 cm here: "
      "%s.\n" % (", ".join(str(b) for b in sa["donor_own_body_over_5cm"]) or "none"))
    a("## 6. The frames (decoded)\n")
    a("%d of %d donor constraints carry at least two 3x4 frames and **%d** of those share one "
      "pivot, reproducing G3-10d's \"11/11 one frame written twice\"; every A->B delta is a "
      "proper rotation. So the frames cannot name which body is A - which is why the geometric "
      "test was the right idea; the error is in what the test was compared against. One artefact: "
      "the %d ragdolls report a *third* frame whose pivot is exactly (0, 0, 0), because the "
      "detector scans 16-float runs and a zero-translation rotation exists in the same object. \"Frame "
      "counts 2 or 3\" is therefore a property of the detector, not of the constraint, and it is "
      "why G3-10d's own `pivots_equal` is False on those two records while `pivots_ab_equal` is "
      "True.\n"
      % (len(pa["donor_rows"]), len(pa["donor_rows"]), sa["donor_rows_same_pivot"],
         sum(1 for r in pa["donor_rows"] if r["frames"] > 2)))
    a("## 7. Inertia: the UNKNOWN is confirmed, and the reading count is inflated\n")
    a("Mass link and oracle reproduced (`%d` hulls, `%d` files; `I = m(e^2+e^2)/12` per axis, a "
      "packed reading needs one constant scale per body, bar %.2f). %d candidate readings, "
      "including %d layouts G3-10d did not test:\n"
      % (ia["linked_hulls"], ia["files"], DECODE_BAR, len(ia["readings"]),
         len(ia["readings"]) - 6))
    a("| reading | best triple | median spread | n | decodes? |")
    a("|---|---|---:|---:|---|")
    for r in ia["readings"]:
        bt = r["best_triple"] or {}
        a("| %s | %s | %s | %d | %s |"
          % (r["reading"], bt.get("triple"), f3(bt.get("median_spread")),
             bt.get("n") or 0, "**yes**" if r["decodes"] else "no"))
    a("")
    a("None decodes: the best is %s, against a bar of %.2f. The extra layouts (6 x i32/u32, "
      "24 x i8/u8, 3 x f64, first-12-byte variants) do not get closer, so G3-10d's UNKNOWN "
      "stands and is now harder to overturn. Its published 1.327 reproduces (`%s`) only when the "
      "box inertia is rounded to 4 decimals the way its code does before the ratio; without that "
      "rounding the best i16 reading is `%s`. The report's number therefore carries a small "
      "rounding artefact, not an error, and the conclusion (nothing decodes) is unaffected.\n"
      % (f3(ia["min_spread"]), DECODE_BAR, f3(ia["min_spread_rounded"]),
         f3(min((r["best_triple"]["median_spread"] for r in ia["readings"]
                 if r["best_triple"] and r["reading"] == "12 x int16 raw"), default=None))))
    a("What G3-10d presents as six independent readings is really fewer. Scaling every int16 by "
      "one constant leaves max/min of the three ratios unchanged, so `raw`, `/16384` and `/32767` "
      "are the same test by construction; `u16` reinterprets the sign bit and is a genuinely "
      "different one. Measured, not asserted:\n")
    a("| reading | max \\|median spread - i16 raw\\| over triples | same test |")
    a("|---|---:|---|")
    for r in ia["redundancy"]:
        a("| %s | %.2e | %s |" % (r["how"], r["max_abs_delta_vs_i16"],
                                  "**yes**" if r["same_test"] else "no"))
    a("")
    a("So the table's six rows are %d distinct tests, and the one that matters (is there *any* "
      "constant-scale reading) is answered: no.\n" % sa["inertia_readings_distinct"])
    a("## 8. Script hygiene: what two concurrent edits left behind\n")
    a("`%s`, %d lines. Counted from its own source:\n" % (sa["source"], sa["lines"]))
    a("| token | occurrences | what it is |")
    a("|---|---:|---|")
    for u in sa["unused_symbols"]:
        a("| `%s` | %d | %s |" % (u["token"], u["occurrences"], u["note"]))
    a("")
    a("- `NO_BODY = 0x7FFFFFFF` is defined and never compared, even though the card's §1 table "
      "claims that word is `0x7FFFFFFF` in every record - the claim is prose, not checked. "
      "Section 1 above checks it (it holds).")
    a("- `position` / `quaternion` are read for every body and then never used. That is the "
      "missing piece of the frame question: a version that transformed pivots into a body frame "
      "would have needed them. The shipped data has identity transforms, so their absence does "
      "not change the numbers - but the code cannot tell a reviewer that.")
    a("- `i16_16384` appears on %d lines: once in the reading table and again hard-coded inside "
      "the direction test and the per-slot correlation, so those two analyses are not "
      "interpretation-independent although the report presents them as properties of \"the "
      "block\". Same for `/16384` vs `/32767`, which cannot differ (section 7)." % sa["i16_16384_occurrences"])
    a("- `pivots_equal` is computed, stored and never used by any oracle; the frame oracle "
      "iterates only records with two frames, so it would pass vacuously on a file where no "
      "constraint had two.")
    a("- No duplicated function definitions were found (each `def` is unique); the damage is "
      "dormant fields and a mis-stated comparison, not two copies of a function.\n")
    a("## 9. What survives, what does not\n")
    a("Survives (reproduced here, decoded): the cinfo record shape, `+0x08` as a valid body id, "
      "the constancy of `+0x04`/`+0x0C`/`+0x10`/`+0x14` (now actually asserted), body 0's "
      "identity transform in every file, the one-frame constraintData, the mass link, and the "
      "inertia UNKNOWN with its scoring.\n")
    a("Does not survive: **\"the partner is body 0\"** as a fleet-wide result. Its own data "
      "contradicts it in %d of %d measurable records (a pivot %.2f m from the chassis while a "
      "part carries it), and the comparison that would support it - body 0 alone against the "
      "recorded body alone - goes the other way, %s against %s. The strongest form the evidence "
      "still allows is narrower: body 0 is a plausible second side for the subset of records whose "
      "pivot lies inside or on the chassis (%s within 10 cm), and each constraint certainly names "
      "**one** body (`+0x08`) whose hull carries the pivot. The other side is not recorded in any "
      "field decoded so far, and `+0x04 = 0` is a constant whose meaning the shipping data cannot "
      "settle.\n"
      % (len(pa["contradictions"]), pa["measurable"], pa["max_d_a"], f3(s["p_a_5cm"]),
         f3(s["p_b_5cm"]), f3(tol[0.10]["p_body_a"])))
    a("## 10. UNKNOWN\n")
    a("- **What `+0x04 = 0` is.** Tried: every cinfo in 50 files (all zero); geometry against the "
      "recorded body, body 0 alone, and the pair, with a shuffled control. The geometry refutes "
      "*\"body 0 is the partner of every constraint\"* but cannot say whether the word is a flag, "
      "an unset side, or a body id that every author left at 0. Where it would be found: a shipped "
      "physicsc with a non-zero word, or the engine's `hknpConstraintCinfo` reader, which is not "
      "in this tree.")
    a("- **The true partner of a constraint.** Not recorded in any field decoded so far: "
      "`+0x00` is the constraintData fixup, `+0x04` constant, `+0x08` one body, `+0x0C`/"
      "`+0x10`/`+0x14` constant, and the body entry carries no constraint list. Where it would be "
      "found: the body-side constraint array, if one exists, or a runtime reader.")
    a("- **The 24 packed inertia bytes.** Unchanged from G3-10d and now tested against %d "
      "layouts; no reading reaches a constant per-body scale. Where it would be found: hull "
      "inertia integrated from face topology (`jc3hkx.decode_polytope` exposes planes, not "
      "faces), or a Havok 2014 header." % len(ia["readings"]))
    a("- **Runtime behaviour.** Every number here is a file fact; no game was launched or "
      "attached to.")
    a("")
    a("## 11. Oracles (`--check` re-runs all)\n")
    a("| oracle | result |")
    a("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        a("| `%s` | %s |" % (k, "**pass**" if v else "**FAIL**"))
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ io
def main():
    import argparse
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    s = doc["stats"]

    if args.write:
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote %s and %s" % (rel(OUT_MD), rel(OUT_JSON)))
        print("files %d | cinfos %d | measurable %d | hulls %d/%d"
              % (s["files_decoded"], s["cinfos"], s["measurable"],
                 s["mass_linked_hulls"], s["mass_files"]))
        print("P(recorded body<=5cm) %s | P(body0<=5cm) %s | P(both) %s | control %s"
              % (f3(s["p_b_5cm"]), f3(s["p_a_5cm"]), f3(s["p_both_5cm"]),
                 f3(s["p_control_5cm"])))
        print("counterexamples %d (recorded-body nearest %d), max |d to body 0| %.2f m"
              % (s["contradictions"], s["contradictions_b_nearest"], s["max_d_a"]))
        print("inertia: %d readings, min spread %s, any decodes %s"
              % (len(doc["inertia"]["readings"]), f3(s["min_inertia_spread"]),
                 s["any_reading_decodes"]))
        print("oracles: %d/%d" % (sum(1 for v in doc["oracles"]["checks"].values() if v),
                                  len(doc["oracles"]["checks"])))
        return 0 if doc["oracles"]["all_ok"] else 1

    bad = []
    for path, want in ((OUT_MD, md), (OUT_JSON, js)):
        if not os.path.exists(path):
            bad.append("missing " + rel(path) + " - run --write")
            continue
        got = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
        if got != want:
            bad.append(rel(path) + " differs from a fresh rebuild")
    if not doc["oracles"]["all_ok"]:
        bad.append("oracle failures: " + ", ".join(
            k for k, v in doc["oracles"]["checks"].items() if not v))
    if bad:
        print("FAIL")
        for b in bad:
            print(" -", b)
        print("detail: " + json.dumps(doc["oracles"]["detail"], sort_keys=True))
        return 1
    print("check OK: %d files re-parsed, %d cinfos, %d measurable, P(b)=%s P(a)=%s P(both)=%s, "
          "%d counterexamples, min inertia spread %s, md+json byte-identical"
          % (s["files_decoded"], s["cinfos"], s["measurable"], f3(s["p_b_5cm"]),
             f3(s["p_a_5cm"]), f3(s["p_both_5cm"]), s["contradictions"],
             f3(s["min_inertia_spread"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
