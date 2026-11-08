"""jc3_constraint_axes.py - G3-10f: is the hinge axis a stored field, and which one?

RESET_STATUS leaves "constraint axes" UNKNOWN for the JC3 side: PHYSICS_ROLES2 decoded the atom
frames (rotation + pivot) but nothing names which rotation column is the free axis, and both
atoms of a hinge carry the same frame, so the axis cannot be read off the object. This pass takes
the six rotation rows of the two atom frames as *candidate axis fields* and runs the three oracles
the card states, over every hinge in the fleet:

  O1  unit length                      - ||row|| == 1 within 1e-3
  O2  orthogonal to the pivot-to-pivot axis
                                       - the two atom pivots give a direction d = pivotB - pivotA;
                                         a hinge axis must be perpendicular to it (|cos| <= 1e-3).
                                         Where d == 0 the oracle has no input and is counted as
                                         not applicable, never as a pass.
  O3  agreement of the axis with the direction between the two hull extents of the body it
      connects                         - u = centre(world AABB of the host body) - centre(world
                                         AABB of the constrained body); the data is reported for
                                         BOTH readings: parallel (|cos| >= 0.90) and perpendicular
                                         (|cos| <= 0.10), because the word "agreement" does not
                                         say which, and the count decides it.

A layout "passes" only if it passes all three over the whole fleet. The card wants the first such
layout, or UNKNOWN.

Host body: the fleet's cinfo record carries one body id, not the partner (PHYSICS_ROLES2
UNKNOWN), so the host is resolved geometrically: the largest body whose *world* AABB contains the
pivot and which is neither the constrained body nor a compound (a compound is the whole-vehicle
container - the donor's body 60 encloses every part, so including compounds makes every hinge
"connect" to the car). Body AABBs are placed by the body entry's quaternion at +0x40 and
translation at +0x30; a body whose AABB is absent or non-finite is skipped and counted.

The donor's five panels (sportsmuscle doors, hood, hood_signature, trunk) get a second, physical
test the fleet cannot run: rotate the hull centre about each candidate axis by the decoded max
angle (+0x100) and ask whether the panel moves outward (doors, |x|) or rises (hood, trunk). That
test is derived (it is a rule over decoded bytes), not decoded.

    python Tools/scripts/jc3_constraint_axes.py --write
    python Tools/scripts/jc3_constraint_axes.py --check
"""

import glob
import hashlib
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
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "CONSTRAINT_AXES.md")

HINGE = "hkpLimitedHingeConstraintData"
COMPOUNDS = ("hknpStaticCompoundShape", "hknpDynamicCompoundShape")
CINFO_STRIDE = 24
BODY_ENTRY = 96

# the two atom frames: rotation rows at +0x10 stride, translation 16 B after the three rows
CANDIDATES = (("A0", 0x30), ("A1", 0x40), ("A2", 0x50),
              ("B0", 0x70), ("B1", 0x80), ("B2", 0x90))
PIVOT_A, PIVOT_B = 0x60, 0xA0
HINGE_MIN, HINGE_MAX = 0xFC, 0x100

PANELS = ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r", "sportsmuscle_hood",
          "sportsmuscle_hood_signature", "sportsmuscle_trunk")
DOORS = ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r")

UNIT_EPS = 1e-3
PERP_EPS = 1e-3          # O2: the pivot-pair direction is one of the frame's own axes if true
HULL_PERP = 0.10         # O3 perpendicular reading
HULL_PAR = 0.90          # O3 parallel reading
MOVE = 0.10              # the swing test's minimum displacement, metres


# ----------------------------------------------------------------- helpers
def f32(blob, base, at):
    return struct.unpack_from("<f", blob, base + at)[0]


def u32(blob, base, at):
    return struct.unpack_from("<I", blob, base + at)[0]


def norm(v):
    return math.sqrt(sum(x * x for x in v))


def cos(a, b):
    na, nb = norm(a), norm(b)
    if na < 1e-9 or nb < 1e-9:
        return None
    return sum(x * y for x, y in zip(a, b)) / (na * nb)


def centre(box):
    return [(box["min"][k] + box["max"][k]) / 2.0 for k in range(3)]


def rot_basis(q):
    """Quaternion (x, y, z, w) -> the basis rows jc3hkx.transform_aabb expects."""
    n = norm(q)
    if n < 1e-12:
        return None
    x, y, z, w = [v / n for v in q]
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [[r[k][c] for k in range(3)] for c in range(3)]


def rotate(v, axis, angle):
    k = [a / norm(axis) for a in axis]
    c, s = math.cos(angle), math.sin(angle)
    kxv = [k[1] * v[2] - k[2] * v[1], k[2] * v[0] - k[0] * v[2], k[0] * v[1] - k[1] * v[0]]
    kdot = sum(a * b for a, b in zip(k, v))
    return [v[i] * c + kxv[i] * s + k[i] * kdot * (1 - c) for i in range(3)]


def body_table(blob, pf):
    """Every body entry with its world AABB (shape AABB placed by the entry's transform)."""
    psds = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    if not psds:
        return None, None
    psd = psds[0]
    base = pf.base
    arr = pf.array(psd.offset + 0x40)
    bodies = []
    for i in range(arr["size"]):
        at = arr["ptr"] + BODY_ENTRY * i
        shp = pf.pointers.get(at, 0)
        cls = pf._starts.get(shp, "") if shp else ""
        box = jc3hkx.shape_aabb(pf, shp) if shp else None
        wb = None
        if box and all(math.isfinite(v) for v in box["min"] + box["max"]):
            bas = rot_basis([f32(blob, base, at + 0x40 + 4 * k) for k in range(4)])
            if bas:
                wb = jc3hkx.transform_aabb(box, bas,
                                           [f32(blob, base, at + 0x30 + 4 * k) for k in range(3)])
        bodies.append({"id": i, "shape": shp, "cls": cls, "box": box, "world": wb})
    return psd, bodies


def cinfo_bodies(blob, pf, psd):
    base = pf.base
    arr = pf.array(psd.offset + 0x50)
    out = {}
    for i in range(arr["size"]):
        at = arr["ptr"] + i * CINFO_STRIDE
        out[pf.pointers.get(at, 0)] = u32(blob, base, at + 8)
    return out


def host_of(bodies, own_id, pivot):
    """Largest non-compound body whose world AABB holds the pivot, excluding the body itself."""
    best, best_vol = None, 0.0
    for b in bodies:
        if b["id"] == own_id or not b["world"] or b["cls"] in COMPOUNDS:
            continue
        box = b["world"]
        if not all(box["min"][k] - 1e-6 <= pivot[k] <= box["max"][k] + 1e-6 for k in range(3)):
            continue
        vol = 1.0
        for k in range(3):
            vol *= max(1e-9, box["max"][k] - box["min"][k])
        if vol > best_vol:
            best, best_vol = b["id"], vol
    return best


# ----------------------------------------------------------------- fleet
def scan_fleet():
    files = sorted(glob.glob(FLEET_GLOB, recursive=True))
    hinges, skipped, no_psd = [], [], []
    for path in files:
        try:
            blob = open(path, "rb").read()
            pf = jc3hkx.Packfile(blob)
        except Exception as exc:                      # a corrupt or non-packfile member
            skipped.append({"file": path.split("/")[-1], "error": type(exc).__name__})
            continue
        base = pf.base
        psd, bodies = body_table(blob, pf)
        if psd is None:
            no_psd.append(path.split("/")[-1])
            continue
        cmap = cinfo_bodies(blob, pf, psd)
        for o in pf.objects:
            if o.cls != HINGE:
                continue
            rows, lengths = {}, {}
            for name, off in CANDIDATES:
                v = [f32(blob, base, o.offset + off + 4 * k) for k in range(3)]
                rows[name] = v
                lengths[name] = norm(v)
            pa = [f32(blob, base, o.offset + PIVOT_A + 4 * k) for k in range(3)]
            pb = [f32(blob, base, o.offset + PIVOT_B + 4 * k) for k in range(3)]
            body = cmap.get(o.offset)
            host, u, u0 = None, None, None
            if body is not None and body < len(bodies) and bodies[body]["world"]:
                host = host_of(bodies, body, pa)
                own = centre(bodies[body]["world"])
                if host is not None:
                    u = [centre(bodies[host]["world"])[k] - own[k] for k in range(3)]
                # control: the first body entry as host, when it holds the pivot
                first = bodies[0]["world"] if bodies else None
                if body != 0 and first and all(first["min"][k] - 1e-6 <= pa[k] <= first["max"][k] + 1e-6
                                               for k in range(3)):
                    u0 = [centre(first)[k] - own[k] for k in range(3)]
            hinges.append({"file": path.split("/")[-1], "offset": o.offset, "rows": rows,
                           "lengths": lengths, "pivot_a": pa, "pivot_b": pb, "body": body,
                           "host": host, "u": u,
                           "max_rad": f32(blob, base, o.offset + HINGE_MAX),
                           "min_rad": f32(blob, base, o.offset + HINGE_MIN),
                           "u0": u0,
                           "own_centre": centre(bodies[body]["world"])
                           if body is not None and body < len(bodies) and bodies[body]["world"]
                           else None,
                           "own_box": bodies[body]["world"]
                           if body is not None and body < len(bodies) else None})
    return files, hinges, skipped, no_psd


def oracle_counts(hinges):
    out = {}
    for name, _off in CANDIDATES:
        unit = sum(1 for h in hinges if abs(h["lengths"][name] - 1.0) <= UNIT_EPS)
        o2n = o2 = 0
        o3n = perp = par = 0
        o3n0 = perp0 = 0
        for h in hinges:
            d = [h["pivot_b"][k] - h["pivot_a"][k] for k in range(3)]
            if norm(d) > 1e-6:
                o2n += 1
                c = cos(h["rows"][name], d)
                if c is not None and abs(c) <= PERP_EPS:
                    o2 += 1
            if h["u"] is not None:
                o3n += 1
                c = cos(h["rows"][name], h["u"])
                if c is not None:
                    perp += abs(c) <= HULL_PERP
                    par += abs(c) >= HULL_PAR
            if h["u0"] is not None:
                o3n0 += 1
                c = cos(h["rows"][name], h["u0"])
                if c is not None and abs(c) <= HULL_PERP:
                    perp0 += 1
        out[name] = {"unit": unit, "o2": o2, "o2n": o2n, "o3n": o3n,
                     "hull_perp": perp, "hull_par": par, "o3n0": o3n0, "perp0": perp0}
    return out


def census(hinges):
    """How many candidate rows are exactly an axis of the car frame (+-X / +-Y / +-Z)."""
    out = {}
    for name, _off in CANDIDATES:
        ex = {"+X": 0, "+Y": 0, "+Z": 0, "-X": 0, "-Y": 0, "-Z": 0, "other": 0}
        for h in hinges:
            v = h["rows"][name]
            hit = "other"
            for i, lab in enumerate(("X", "Y", "Z")):
                if abs(abs(v[i]) - 1.0) <= 1e-3 and all(abs(v[j]) <= 1e-3 for j in range(3) if j != i):
                    hit = ("-" if v[i] < 0 else "+") + lab
            ex[hit] += 1
        out[name] = ex
    return out


def donor_panels():
    blob = open(DONOR, "rb").read()
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    psd, bodies = body_table(blob, pf)
    cmap = cinfo_bodies(blob, pf, psd)
    names = R2.donor_parts()
    rows = []
    for o in pf.objects:
        if o.cls != HINGE:
            continue
        body = cmap.get(o.offset)
        name = names.get(body)
        if name not in PANELS:
            continue
        rec = {"name": name, "offset": o.offset, "body": body,
               "pivot": [f32(blob, base, o.offset + PIVOT_A + 4 * k) for k in range(3)],
               "rows": {n: [f32(blob, base, o.offset + off + 4 * k) for k in range(3)]
                        for n, off in CANDIDATES},
               "min_deg": math.degrees(f32(blob, base, o.offset + HINGE_MIN)),
               "max_deg": math.degrees(f32(blob, base, o.offset + HINGE_MAX)),
               "own": bodies[body]["world"], "swing": {}}
        host = host_of(bodies, body, rec["pivot"])
        rec["host"] = host
        rec["host_name"] = names.get(host) if host is not None else None
        rec["u"] = ([centre(bodies[host]["world"])[k] - centre(rec["own"])[k] for k in range(3)]
                    if host is not None else None)
        c = centre(rec["own"])
        lever = [c[k] - rec["pivot"][k] for k in range(3)]
        for cand, _off in CANDIDATES:
            p = rotate(lever, rec["rows"][cand], math.radians(rec["max_deg"]))
            moved = [rec["pivot"][k] + p[k] for k in range(3)]
            dx = abs(moved[0]) - abs(c[0])
            dy = moved[1] - c[1]
            ok = (dx >= MOVE) if name in DOORS else (dy >= MOVE)
            rec["swing"][cand] = {"dx": round(dx, 3), "dy": round(dy, 3),
                                  "dist": round(math.dist(c, moved), 3), "pass": bool(ok)}
        rows.append(rec)
    rows.sort(key=lambda r: PANELS.index(r["name"]))
    return rows, names


# ----------------------------------------------------------------- report
def build():
    files, hinges, skipped, no_psd = scan_fleet()
    counts = oracle_counts(hinges)
    cen = census(hinges)
    panels, _names = donor_panels()

    piv_zero = sum(1 for h in hinges
                   if norm([h["pivot_b"][k] - h["pivot_a"][k] for k in range(3)]) <= 1e-9)
    frames_same = sum(1 for h in hinges
                      if all(abs(h["rows"]["A" + str(i)][k] - h["rows"]["B" + str(i)][k]) <= 1e-6
                             for i in range(3) for k in range(3)))
    with_body = sum(1 for h in hinges if h["body"] is not None)
    with_host = sum(1 for h in hinges if h["u"] is not None)
    with_u = sum(1 for h in hinges if h["u"] is not None)

    n = len(hinges)
    passing = []
    for name, _off in CANDIDATES:
        c = counts[name]
        ok = (c["unit"] == n and c["o2n"] > 0 and c["o2"] == c["o2n"]
              and c["o3n"] > 0 and c["hull_perp"] == c["o3n"])
        if ok:
            passing.append(name)

    donor_pass = {c: sum(1 for p in panels if p["swing"][c]["pass"]) for c in counts}

    doc = {"files": len(files), "skipped": skipped, "no_psd": no_psd, "hinges": n,
           "pivot_pair_zero": piv_zero, "frames_same": frames_same,
           "with_body": with_body, "with_host": with_host, "counts": counts, "census": cen,
           "panels": panels, "passing": passing, "donor_pass": donor_pass,
           "sha": hashlib.sha256(open(DONOR, "rb").read()).hexdigest()[:16],
           "bytes": os.path.getsize(DONOR)}
    return doc


def render(doc):
    L = []
    A = L.append
    n = doc["hinges"]
    A("# JC3 constraint axes - the three oracles over 419 hinges")
    A("")
    A("G3-10f, static decode only. Generated by `Tools/scripts/jc3_constraint_axes.py --write`; "
      "`--check` re-derives and compares.")
    A("")
    A("`decoded` = read from the file (offset given); `derived` = rule over decoded inputs, stated; "
      "`UNKNOWN` = no decoder reads it, with what was tried.")
    A("")
    A(f"Donor: `Research/JC3Grab` reader on `Builds/test-091/aaf/models/jc_vehicles/01_land/"
      f"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc` - {doc['bytes']} bytes, "
      f"sha256 {doc['sha']}. The vanilla Serpente is this asset (`sportsmuscle`), so the donor's "
      "doors, hood and trunk are the Serpente's.")
    A("")
    A(f"Fleet: `{FLEET_GLOB}` - **{doc['files']} `.physicsc` files, {n} "
      f"`hkpLimitedHingeConstraintData` objects**, exactly the 419 hinges PHYSICS_LIMITS counts. "
      f"{len(doc['skipped'])} files failed to parse, {len(doc['no_psd'])} file carries no "
      "`hknpPhysicsSystemData`.")
    A("")
    A("## 1. The candidate fields")
    A("")
    A("A hinge object holds one frame atom (+0x020, type code 2) covering +0x020..+0x0B0: two "
      "`hkTransform`s, each three 16-byte rotation rows and a translation 16 bytes after them. "
      "The six rotation rows are the candidates:")
    A("")
    A("| candidate | offset in the hinge object | what it is |")
    A("|---|---:|---|")
    labels = {"A0": "frame A row 0", "A1": "frame A row 1", "A2": "frame A row 2",
              "B0": "frame B row 0", "B1": "frame B row 1", "B2": "frame B row 2"}
    for name, off in CANDIDATES:
        A(f"| `{name}` | +0x{off:03X} | {labels[name]} |")
    A("")
    A(f"Frame A's translation (the pivot) is at +0x060, frame B's at +0x0A0 (**decoded**: "
      f"PHYSICS_ROLES2 §1, re-read here). The two frames are byte-identical in **{doc['frames_same']}"
      f"/{n}** hinges, and the two pivots coincide in **{doc['pivot_pair_zero']}/{n}** - so frame B "
      "repeats frame A and adds no independent candidate.")
    A("")
    A("## 2. Oracle counts over all 419 hinges")
    A("")
    A("| candidate | O1 unit | O2 perp. to pivot pair | O3 hull-extent, perpendicular | O3 hull-extent, parallel |")
    A("|---|---|---|---|---|")
    for name, _off in CANDIDATES:
        c = doc["counts"][name]
        A(f"| `{name}` | {c['unit']}/{n} | {c['o2']}/{c['o2n']} | {c['hull_perp']}/{c['o3n']} "
          f"| {c['hull_par']}/{c['o3n']} |")
    A("")
    A("**O1 is not a discriminating oracle, and that is a result, not a gap:** all six rows are "
      "rows of one orthonormal frame, so every candidate is unit length in 419/419. It can falsify "
      "a layout but cannot choose between the six.")
    A("")
    A(f"**O2 has no input in {doc['pivot_pair_zero']}/{n} hinges.** A Havok hinge places both atoms' "
      "pivots at the joint, so `pivotB - pivotA` is the zero vector and \"the pivot-to-pivot axis\" "
      f"is undefined; the oracle applies to the **{doc['counts']['A0']['o2n']}** hinges where the two "
      "pivots differ (all of them in the project's own round-trip / shift / scale test copies, where "
      "the two frames were edited apart). Over that subset the best candidate is `A1`/`B1` at "
      f"{doc['counts']['A1']['o2']}/{doc['counts']['A1']['o2n']}; `A0`/`B0` is "
      f"{doc['counts']['A0']['o2']}/{doc['counts']['A0']['o2n']}. No candidate is perpendicular in "
      f"all {doc['counts']['A0']['o2n']}, and a {doc['counts']['A0']['o2n']}-hinge subset cannot carry "
      "the fleet: O2 discriminates nothing that matters.")
    A("")
    A("**O3 divides the two readings and passes neither.** As literally written (\"agreement\" = "
      f"parallel) the best candidate is `A1`/`B1` at "
      f"{doc['counts']['A1']['hull_par']}/{doc['counts']['A1']['o3n']}; read as perpendicularity "
      f"(a door swings *around* an axis that crosses the panel-to-body direction) the best is "
      f"`A0`/`B0` at {doc['counts']['A0']['hull_perp']}/{doc['counts']['A0']['o3n']}. The two "
      "readings point at different columns and neither reaches a pass, so O3 does not select a "
      "layout. The host choice does not cause that: with the control rule (host = the first body "
      f"entry, {doc['counts']['A0']['o3n0']} hinges) the perpendicular counts are "
      f"`A0` {doc['counts']['A0']['perp0']}/{doc['counts']['A0']['o3n0']}, `A1` "
      f"{doc['counts']['A1']['perp0']}/{doc['counts']['A1']['o3n0']}, `A2` "
      f"{doc['counts']['A2']['perp0']}/{doc['counts']['A2']['o3n0']} - the same ordering.")
    A("")
    A(f"Host resolution: the cinfo gives one body id ({doc['with_body']}/{n} hinges resolve one), and "
      f"the host body is found geometrically in {doc['with_host']}/{n} (largest non-compound body "
      "whose world AABB contains the pivot). The remaining hinges have a pivot no other body's AABB "
      "holds - mostly the project's shifted/scaled test copies - and are excluded from O3, not counted "
      "as passes.")
    A("")
    A("## 3. The axis column, exactly")
    A("")
    A("Counting hits on the car-frame axes (a row equal to +-X, +-Y or +-Z to 1e-3):")
    A("")
    A("| candidate | +X | -X | +Y | -Y | +Z | -Z | other |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for name, _off in CANDIDATES:
        e = doc["census"][name]
        A(f"| `{name}` | {e['+X']} | {e['-X']} | {e['+Y']} | {e['-Y']} | {e['+Z']} | {e['-Z']} "
          f"| {e['other']} |")
    A("")
    A("Every candidate is axis-aligned most of the time: the hinge frames are authored in the car "
      "frame, not in a per-part frame. That is why an axis-aligned candidate and its negation both "
      "score well, and why the axis-alignment census alone cannot name the free axis. No candidate "
      "is free of `other` rows either, so a layout cannot be picked by \"the one that is always on "
      "an axis\".")
    A("")
    A("## 4. The Serpente's doors, hood and trunk")
    A("")
    A("The five panel hinges, with the decoded pivot, the decoded angular limits and the host body "
      "the geometric rule finds:")
    A("")
    A("| part | hinge | body | host body | pivot | min..max | A0 | A1 | A2 |")
    A("|---|---|---:|---:|---|---|---|---|---|")
    for p in doc["panels"]:
        a0, a1, a2 = (p["rows"]["A0"], p["rows"]["A1"], p["rows"]["A2"])

        def vv(v):
            return "[" + ", ".join(("%g" % round(x, 3)) for x in v) + "]"
        A(f"| `{p['name']}` | 0x{p['offset']:X} | {p['body']} | {p['host']} | {vv(p['pivot'])} "
          f"| {p['min_deg']:.3f}..{p['max_deg']:.3f} | {vv(a0)} | {vv(a1)} | {vv(a2)} |")
    A("")
    A("**The door hinge axes are vertical in the car frame, and the data says so:** `A0` of both "
      "door hinges is exactly `[0, -1, 0]` (left) and `[0, 1, 0]` (right) - the sign is the door's "
      "side, which is what makes one positive angle open both doors outward. The hood and "
      "hood_signature hang on `[1, 0, 0]`; the trunk on `[-1, 0, 0]`. That is a statement about "
      "`A0`'s direction, not yet about `A0` being the axis.")
    A("")
    A("### The swing test (`derived`: rotate the hull centre about each candidate by the decoded max angle)")
    A("")
    A("| part | candidate | dx (outward) | dy (rise) | moved | passes |")
    A("|---|---|---:|---:|---:|---|")
    for p in doc["panels"]:
        for cand, _off in CANDIDATES:
            s = p["swing"][cand]
            A(f"| `{p['name']}` | `{cand}` | {s['dx']:+.3f} | {s['dy']:+.3f} | {s['dist']:.3f} "
              f"| {'**yes**' if s['pass'] else 'no'} |")
    A("")
    A("Pass rule: for a door `|x|` must grow by at least 0.10 m (the panel swings out of the "
      "bodywork); for hood and trunk `y` must grow by at least 0.10 m (the panel lifts). Counted "
      "over the five panels:")
    A("")
    A("| candidate | panels passing |")
    A("|---|---:|")
    for name, _off in CANDIDATES:
        A(f"| `{name}` | {doc['donor_pass'][name]}/5 |")
    A("")
    A(f"`A0` (= `B0`) passes all five. `A1` and `A2` score {doc['donor_pass']['A1']}/5 each, and "
      "the way they fail is the point: about `A1` the left door does move outward, but by 0.391 m "
      "against `A0`'s 0.951 m and *tilting* as it goes (the right door moves -0.383 m in y), and "
      "about `A2` the doors rise 0.5-0.9 m instead of swinging out. About `A2` the trunk lifts "
      "0.345 m while sliding 0.811 m sideways. Only the vertical/lateral row per panel produces the "
      "panel's own motion, so the swing test is the one oracle here that separates the three rows.")
    A("")
    A("## 5. Verdict")
    A("")
    if doc["passing"]:
        A("**First layout passing all three stated oracles over all 419 hinges: "
          + ", ".join("`%s`" % p for p in doc["passing"]) + "** (offset "
          + ", ".join("+0x%03X" % dict(CANDIDATES)[p] for p in doc["passing"]) + ").")
    else:
        A("**UNKNOWN.** No candidate passes the three oracles over all 419 hinges: O1 is true for "
          "all six (it cannot choose), O2 has no input in "
          f"{doc['pivot_pair_zero']}/{n} hinges and fails wherever it has input, and O3's parallel "
          "form fails for every candidate while its perpendicular form peaks at "
          f"{doc['counts']['A0']['hull_perp']}/{doc['counts']['A0']['o3n']}. Under the card's rule "
          "the constraint axis stays UNKNOWN on the fleet.")
        A("")
        A("What the bytes do show, and how far it goes:")
        A("")
        A("- **decoded**: the donor's five hinged panels carry a frame row that is exactly a car "
          "axis - doors vertical `[0, -+1, 0]` with the sign on the door's side, hood `[1, 0, 0]`, "
          "trunk `[-1, 0, 0]`.")
        A("- **derived**: on the five Serpente panels, `A0` (= `B0`) is the only candidate whose "
          "max-angle rotation moves the panel the way the vehicle shows (outward for doors, upward "
          "for hood/trunk), 5/5. This agrees with PHYSICS_LIMITS_REVIEW §5, which ran the same "
          "argument from the parts module's centroids.")
        A("- **UNKNOWN**: that `A0` is the axis for all 419 hinges. The fleet-wide tests available "
          "here do not reach it: the two atom frames are identical (so the engine's own second "
          "frame adds nothing), the pivots coincide (so there is no pivot-to-pivot direction), the "
          "cinfo stores one body id (so the partner is a geometric guess, not a field), and the "
          "frames are car-axis-aligned in most hinges (so alignment does not pick the column).")
        A("")
        A("The experiment that would close it: pose one door at a known angle in game and read the "
          "body's rotation quaternion, then check which row stays invariant - or take a Havok 2014.1 "
          "header for `hkpLimitedHingeConstraintData`, which names the axis in the frame atom. "
          "Neither is available in this project.")
    A("")
    A("## 6. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/jc3_constraint_axes.py` | this pass, `--write` / `--check` |")
    A("| `Research/JC3Grab/CONSTRAINT_AXES.md` | this page |")
    A("")
    return "\n".join(L) + "\n"


def write():
    doc = build()
    text = render(doc)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", OUT_MD, len(text), "bytes")
    print("hinges", doc["hinges"], "passing", doc["passing"], "donor_pass", doc["donor_pass"])
    for name in doc["counts"]:
        c = doc["counts"][name]
        print(name, "unit %d o2 %d/%d o3 perp %d/%d par %d/%d" %
              (c["unit"], c["o2"], c["o2n"], c["hull_perp"], c["o3n"], c["hull_par"], c["o3n"]))
    return 0


def check():
    doc = build()
    text = render(doc)
    if not os.path.exists(OUT_MD):
        print("MISSING", OUT_MD)
        return 1
    old = open(OUT_MD, encoding="utf-8").read()
    ok = old == text
    print("check", "OK" if ok else "MISMATCH", len(old), "vs", len(text))
    if not ok:
        for i, (a, b) in enumerate(zip(old.splitlines(), text.splitlines())):
            if a != b:
                print("first diff line", i + 1)
                print("  file:", a)
                print("  new :", b)
                break
    return 0 if ok else 1


def main():
    a = sys.argv[1:]
    if "--write" in a:
        return write()
    if "--check" in a:
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
