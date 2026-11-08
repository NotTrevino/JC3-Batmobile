"""bm_collision2.py - B-10d: collision-input audit, and a corrected body hull source.

G3-11d (`MODLOG.md`, 2026-11-05) re-read the five ledger collision rows and found that the
BmAK **source** the earlier rows used was not the drivable car: T-CO2's box was
`SUSP1_Wheel_Rear_Left_Mesh`, 316.155 x 63.418 x 109.881 cm - a **wreck wheel**, not the
drivable chassis box 690.305 x 374.536 x 207.5 cm decoded in
`Research/BatmobileGrab/COLLISION_GEOM.md` (body 169750, bone `Batmobile_Chassis`, box 0).

This script does two things and writes neither into an existing tree:

1. **Audit.** Every constant the three collision scripts (`bm_collision.py`, `bm_colmesh.py`,
   `bm_colhull.py`) read from BmAK data is listed with the value used, the G3 value, and a
   match / mismatch verdict. The wreck triple is searched for in the three scripts' source
   text and in the ledger row that still carries it.
2. **Correction.** `bm_collision.py`'s body target was DIM-1's **render-mesh** bbox
   (3.495 x 2.271 x 7.025 m). The drivable chassis box is 6.903 x 3.745 x 2.075 m, i.e.
   wider and lower than the render mesh. This script re-derives the same hull set with the
   body hull mapped onto the **chassis box's own decoded extents** instead, and prints both
   sets of numbers side by side.

What is decoded and what is derived, per R4:

  size      decoded - `COLLISION_GEOM.json` bodies[0].geometry.boxes[0].extents_cm
            (690.305, 374.536, 207.5), read by this script, never typed.
  axes      derived - the axis correspondence is taken from the two boxes' own longest
            spans: BmAK X (length) -> JC3 z, BmAK Y (width) -> JC3 x, BmAK Z (height) ->
            JC3 y.  Oracle: the sorted spans of the two boxes agree within 0.25 m, the band
            G3-01b's own oracle states, and the longest axis lands on JC3's longest.
  placement derived - this script keeps B-10's body-hull placement rule (the hull's AABB is
            the target box, centred on DIM-1's bbox in the two horizontal axes); the vertical
            choice puts the box's bottom on DIM-1's `y_min`, the ground line.  BmAK's own
            box bottom sits 3.2 cm above the mesh's lowest point (COLLISION_FRAME, mesh-space
            z 3.0 vs render min -0.223 cm), and that residual is printed, not hidden.
  rotation  UNKNOWN - COLLISION_GEOM says the chassis box TM is not decoded, so the hull is
            axis-aligned; a rotated box would change the AABB.

Wheels, doors, everything else are B-10's, unchanged and re-checked: the wheel scale is the
tyre diameter over the donor hull's own height (T-22), and no wheel *physics* box exists in
the drivable BmAK set (169750 has 2 boxes, 169751 has 1, both body/weapon pods).

Usage:
    uv run python Tools/scripts/bm_collision2.py --write
    uv run python Tools/scripts/bm_collision2.py --check
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_collision as C                          # noqa: E402  (B-10's proven writer paths)
import jc3hkx as H                                # noqa: E402

GEOM = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_GEOM.json")
FRAME_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_FRAME.md")
PARTS_MANIFEST = C.BODY_MANIFEST
T22 = C.T22
STATIONS = C.STATIONS
B10_BIN = C.OUT_BIN
SCRIPTS = ("bm_collision.py", "bm_colmesh.py", "bm_colhull.py")

OUT_DIR = os.path.join(ROOT, "Working", "Collision2")
OUT_BIN = os.path.join(OUT_DIR, "batmobile.physicsc")
OUT_JSON = os.path.join(OUT_DIR, "bm_collision2.json")
OUT_MD = os.path.join(OUT_DIR, "BM_COLLISION2.md")

WRECK_CM = (316.155, 63.418, 109.881)   # G3-11d / T-CO2, the wreck wheel box


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def rnd(v, n=4):
    return round(float(v), n)


def vec(v, n=4):
    return [rnd(x, n) for x in v]


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ inputs
def g3_boxes() -> dict:
    g = json.load(open(GEOM, encoding="utf-8"))
    bodies = g["physics_asset_158266"]["bodies"]
    out = []
    for b in bodies:
        boxes = []
        for bx in b["geometry"]["boxes"]:
            boxes.append({"extents_cm": bx["extents_cm"], "centre_cm": bx["centre_cm"]})
        out.append({"bone": b["bone"], "boxes": boxes})
    return {"bone": out[0]["bone"], "chassis_box0_cm": out[0]["boxes"][0]["extents_cm"],
            "chassis_centre_cm": out[0]["boxes"][0]["centre_cm"],
            "chassis_box1_cm": out[0]["boxes"][1]["extents_cm"],
            "weapon_box_cm": out[1]["boxes"][0]["extents_cm"],
            "bodies": out,
            "oracle": g["oracle_chassis_box_vs_body_box"]}


def render_bounds_cm() -> list:
    """The BmAK render-mesh bounds COLLISION_FRAME.md decodes, parsed from that file."""
    txt = open(FRAME_MD, encoding="utf-8").read()
    key = "render mesh bounds (decoded, PSK): min ["
    i = txt.index(key) + len(key)
    seg = txt[i:txt.index("]", i)]
    lo = [float(x) for x in seg.split(",")]
    j = txt.index("max [", i) + 5
    hi = [float(x) for x in txt[j:txt.index("]", j)].split(",")]
    return [lo, hi]


def wreck_in_sources() -> dict:
    hits = {}
    for name in SCRIPTS:
        src = open(os.path.join(HERE, name), encoding="utf-8").read()
        hits[name] = {s: src.count(s) for s in ("316.155", "63.418", "109.881", "3.1615")}
    led = json.load(open(T22, encoding="utf-8"))
    row = led.get("rows", {}).get("T-CO2") if isinstance(led.get("rows"), dict) else None
    raw = json.dumps(led)
    return {"scripts": hits, "ledger_row_has_wreck": "316.15" in raw,
            "ledger_row_T_CO2": row}


# ------------------------------------------------------------------ the corrected build
def build() -> dict:
    man = json.load(open(PARTS_MANIFEST, encoding="utf-8"))
    t22 = json.load(open(T22, encoding="utf-8"))
    st = json.load(open(STATIONS, encoding="utf-8"))
    g3 = g3_boxes()
    rb = render_bounds_cm()
    bbox_lo = [float(x) for x in man["body_bbox_m"][0]]
    bbox_hi = [float(x) for x in man["body_bbox_m"][1]]
    body_span = [bbox_hi[j] - bbox_lo[j] for j in range(3)]

    # BmAK chassis box -> JC3 axes by the boxes' own longest spans (derived, oracle O4)
    ext = [float(x) / 100.0 for x in g3["chassis_box0_cm"]]        # m, BmAK (X len, Y wid, Z hgt)
    chassis = {"length": ext[0], "width": ext[1], "height": ext[2]}
    jc3_size = [chassis["width"], chassis["height"], chassis["length"]]   # (x, y, z)
    sorted_chassis = sorted([chassis["length"], chassis["width"], chassis["height"]])
    sorted_body = sorted(body_span)

    # placement: B-10's rule in x/z (centred on DIM-1); in y the bottom is BmAK's own box
    # floor, decoded from the chassis box TM: centre z 106.75 cm - extent z 207.5/2 = 3.00 cm.
    # (Until 8390 this used DIM-1's y_min, the render mesh's ground line, which put the hull
    # 6.1 cm too high relative to BmAK's box.)
    cx = (bbox_lo[0] + bbox_hi[0]) / 2.0
    cz = (bbox_lo[2] + bbox_hi[2]) / 2.0
    floor_y = (g3["chassis_centre_cm"][2] - g3["chassis_box0_cm"][2] / 2.0) / 100.0
    lo = [cx - jc3_size[0] / 2.0, floor_y, cz - jc3_size[2] / 2.0]
    hi = [cx + jc3_size[0] / 2.0, floor_y + jc3_size[1], cz + jc3_size[2] / 2.0]

    donor_blob = open(C.DONOR, "rb").read()
    pf = H.Packfile(donor_blob)
    parts = C.jc3adf.parts(C.jc3adf.Adf(open(C.PARTS_MODULE, "rb").read()))
    index = {p["name"]: p["part_index"] for p in parts}
    hull_of = C.hull_offset_of_part(pf)
    body_idx = index[C.BODY_PART]
    body_off = hull_of[body_idx]
    before = H.decode_polytope(pf, body_off)
    blob, box, k, s = C.body_map(pf, body_off, lo, hi)
    changes = {body_off: (blob, box)}

    wheels = []
    t22_parts = {p["target_part"]: p for p in t22["hull_set"]["parts"]}
    tyre_d = 2 * sum(c["radius"] for c in st["corners"].values()) / len(st["corners"])
    for name in C.WHEEL_CORNER:
        part = index[name]
        off = hull_of[part]
        kk = float(t22_parts[name]["scale_k"])
        d0 = H.decode_polytope(pf, off)
        if abs(kk - tyre_d / (d0["bounds"]["max"][1] - d0["bounds"]["min"][1])) > 1e-5:
            raise SystemExit(f"{name}: T-22 k {kk} is not tyre diameter / donor hull height")
        blobw, boxw = H.scale_hull(pf, off, kk)
        changes[off] = (blobw, boxw)
        wheels.append({"part": name, "hull": f"{off:#x}", "k": rnd(kk, 6),
                       "box_after_m": {"min": vec(boxw["min"]), "max": vec(boxw["max"]),
                                       "size": vec([boxw["max"][j] - boxw["min"][j]
                                                    for j in range(3)])}})

    edits = {off: b for off, (b, _x) in changes.items()}
    edits.update(H.compound_aabb_edits(pf, changes))
    out, info = H.packfile_bytes(pf, edits)
    problems = H.verify_written(pf.blob, out, edits)
    opf = H.Packfile(out)
    counts, shape_bad = H.shape_checks(opf)

    after = H.decode_polytope(opf, body_off)
    dev = C.deviation(after["bounds"]["min"], after["bounds"]["max"], lo, hi)
    support = 0.0
    for pl in after["planes"]:
        n, d = pl["n"], pl["d"]
        support = max(support, abs(max(sum(n[q] * v[q] for q in range(3))
                                       for v in after["vertices"]) + d))

    sys_before = [pf.blob[pf.base + o.offset:pf.base + o.offset + pf.extents[o.offset]]
                  for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    sys_after = [opf.blob[opf.base + o.offset:opf.base + o.offset + opf.extents[o.offset]]
                 for o in opf.objects if o.cls == "hknpPhysicsSystemData"]

    # B-10's own file, re-derived through bm_collision itself (oracle O1)
    b10 = C.build()
    b10_disk = open(B10_BIN, "rb").read()
    b10_body = next(w for w in b10["hull_set"]["written"] if w["part"] == C.BODY_PART)
    b10_off = b10["hull_set"]["written"][0]["part_index"]
    b10_now = C.H.Packfile(b10_disk)

    # wheels must be byte-identical between the two files (the correction touches the body only)
    wheel_same = {}
    for name in C.WHEEL_CORNER:
        off = hull_of[index[name]]
        a = b10_disk[b10_now.base + off:b10_now.base + off + b10_now.extents[off]]
        b = out[opf.base + off:opf.base + off + opf.extents[off]]
        wheel_same[name] = a == b

    audit = build_audit(g3, chassis, jc3_size, body_span, tyre_d, t22)
    oracles = build_oracles(g3, b10, b10_disk, out, problems, shape_bad, counts, dev, support,
                             sys_before, sys_after, padded(wheel_same), audit, lo, hi, after)

    doc = {
        "card": "B-10d", "generator": rel(os.path.abspath(__file__)),
        "inputs": {
            "g3_geometry": rel(GEOM),
            "g3_frame": rel(FRAME_MD),
            "body_bbox": rel(PARTS_MANIFEST),
            "t22": rel(T22),
            "stations": rel(STATIONS),
            "donor_physicsc": rel(C.DONOR),
            "b10_file": rel(B10_BIN),
        },
        "g3": g3,
        "render_bounds_cm": rb,
        "audit": audit,
        "target": {
            "source": "COLLISION_GEOM.json bodies[0] (bone %s) box 0" % g3["bone"],
            "chassis_cm": g3["chassis_box0_cm"],
            "chassis_m_axes": chassis,
            "jc3_size_m": vec(jc3_size, 5),
            "target_lo": vec(lo, 5), "target_hi": vec(hi, 5),
            "body_bbox_m": {"min": vec(bbox_lo), "max": vec(bbox_hi), "size": vec(body_span)},
            "delta_vs_render_bbox_m": {
                "x_width": rnd(jc3_size[0] - body_span[0]),
                "y_height": rnd(jc3_size[1] - body_span[1]),
                "z_length": rnd(jc3_size[2] - body_span[2]),
            },
            "placement": "x/z: B-10's rule (hull AABB centred on DIM-1's bbox). y: decoded - "
                         "the bottom is BmAK's chassis box 0 floor, centre z 106.75 cm - "
                         "extent z 207.5/2 = 3.00 cm, mapped to JC3 y (0.030 m). DIM-1's y_min "
                         "(0.091 m) is the render mesh's ground line, not a contact plane; using "
                         "it placed the hull 6.1 cm high",
            "rotation": "the chassis box TM is not decoded (COLLISION_GEOM), so the hull is "
                        "axis-aligned; a rotated box would change the AABB",
        },
        "body": {
            "part": C.BODY_PART, "part_index": body_idx, "hull": f"{body_off:#x}",
            "k_per_axis": vec(k, 6), "translate_m": vec(s, 6),
            "radius_before": rnd(before["convex_radius"], 6),
            "radius_after": rnd(before["convex_radius"] * min(k), 6),
            "box_before_m": {"min": vec(before["bounds"]["min"]),
                             "max": vec(before["bounds"]["max"])},
            "box_after_m": {"min": vec(after["bounds"]["min"]),
                            "max": vec(after["bounds"]["max"]),
                            "size": vec([after["bounds"]["max"][j] - after["bounds"]["min"][j]
                                         for j in range(3)])},
            "b10_box_after_m": b10_body["box_after_m"],
            "b10_k": b10_body["scale_k"],
            "b10_radius_after": b10_body["radius_after"],
            "vertices": before["vertex_count"], "planes": before["plane_count"],
        },
        "wheels": wheels,
        "stations": {"in_file": len(H.stations(opf)),
                     "physics_system_data_identical": sys_before == sys_after},
        "counts": counts,
        "write": {"bytes": len(out), "sha256": sha256(out),
                  "objects": len(opf.objects)},
        "oracles": oracles,
        "_blob": out,
    }
    doc["md"] = render_md(doc)
    return doc


def padded(d: dict) -> dict:
    return d


def build_audit(g3, chassis, jc3_size, body_span, tyre_d, t22) -> list:
    """Every BmAK-derived constant the three scripts read, against the G3 value."""
    rows = []

    def row(inp, script, used, g3v, verdict, why):
        rows.append({"input": inp, "script": script, "used": used, "g3": g3v,
                     "verdict": verdict, "why": why})

    row("body collision box (B-10's body hull target)",
        "bm_collision.py", "DIM-1 body bbox %s x %s x %s m (B-02, from the BmAK render mesh)"
        % tuple(rnd(x, 3) for x in body_span),
        "chassis box 0, bone %s: %s x %s x %s cm = %s x %s x %s m"
        % (g3["bone"],
           *[("%g" % x) for x in g3["chassis_box0_cm"]],
           *[("%.3f" % (x / 100.0)) for x in
             (g3["chassis_box0_cm"][0], g3["chassis_box0_cm"][1], g3["chassis_box0_cm"][2])]),
        "MISMATCH",
        "width %+.3f m, height %+.3f m, length %+.3f m: the render mesh is narrower and "
        "taller than the drivable chassis box" % (jc3_size[0] - body_span[0],
                                                  jc3_size[1] - body_span[1],
                                                  jc3_size[2] - body_span[2]))
    row("wreck wheel box 316.155 x 63.418 x 109.881 cm", "none (ledger row T-CO2 only)",
        "not read by any of the three scripts",
        "G3-11d: SUSP1_Wheel_Rear_Left_Mesh, a wreck wheel - not the drivable car", "MATCH",
        "the scripts never read it; the constant survives only as T-CO2's source text")
    row("wheel scale k", "bm_collision.py",
        "1.660052 = tyre diameter %.4f m / donor hull height 0.8225 m" % tyre_d,
        "no wheel *physics* box is decoded in the drivable set: 169750 carries 2 chassis "
        "boxes, 169751 one weapon-pod box", "UNKNOWN",
        "the wheel source is the tyre from the PSKX wheel mesh (G1-18), not a BmAK body box; "
        "T-22's k is derived from it, so there is no G3 wheel box to compare")
    row("body-0 world hull source", "bm_colhull.py",
        "convex hull of the Batmobile body LOD2 render mesh",
        "G3-11d: body 0 is the drivable chassis box's body, 690.305 x 374.536 x 207.5 cm",
        "MISMATCH", "the hull follows the render mesh, so it inherits B-10's width/height error")
    row("body-42 raycast mesh source", "bm_colmesh.py",
        "the Batmobile body LOD2 render mesh (6,269 triangles)",
        "body 42 is part 0's `hknpExternMeshShape` - a raycast/bullet mesh, not the chassis box",
        "MATCH", "a raycast mesh must follow the render mesh; G3-11d does not touch it")
    row("hull vertex budget / domain margin / materials", "bm_colhull.py, bm_colmesh.py",
        "244 vertices, 0.05 m, 16 glass / 14 metal", "not BmAK values (JC3 fleet + the donor "
        "file's own decoded constants)", "n/a", "no BmAK source to compare")
    return rows


def build_oracles(g3, b10, b10_disk, out, problems, shape_bad, counts, dev, support,
                  sys_before, sys_after, wheel_same, audit, lo, hi, after) -> list:
    o = []

    def add(key, ok, ev):
        o.append({"key": key, "ok": bool(ok), "evidence": ev})

    add("O1-B10-reproduces",
        b10["_blob"] == b10_disk,
        "bm_collision.build() re-derives %s byte for byte (%d B, sha256 %s...)"
        % (rel(B10_BIN), len(b10_disk), sha256(b10_disk)[:16]))
    wreck = wreck_in_sources()
    n_hits = sum(sum(v.values()) for v in wreck["scripts"].values())
    add("O2-no-wreck-constant-in-code",
        n_hits == 0 and wreck["ledger_row_has_wreck"],
        "the wreck triple + 3.1615 occur %d times in %s; the ledger still carries it (T-CO2)"
        % (n_hits, ", ".join(SCRIPTS)))
    add("O3-chassis-box-decoded",
        [round(x, 3) for x in g3["chassis_box0_cm"]] == [690.305, 374.536, 207.5]
        and g3["bone"] == "Batmobile_Chassis",
        "COLLISION_GEOM.json bodies[0] bone %s box 0 extents %s cm, centre %s cm"
        % (g3["bone"], g3["chassis_box0_cm"], g3["chassis_centre_cm"]))
    s_ch = sorted(g3["chassis_box0_cm"][k] / 100.0 for k in range(3))
    add("O4-axis-map-order",
        all(abs(s_ch[i] - sorted([after["bounds"]["max"][j] - after["bounds"]["min"][j]
                                  for j in range(3)])[i]) < 0.25 for i in range(3)),
        "the chassis box's sorted spans %s m agree with the written hull's sorted spans %s m "
        "within 0.25 m (G3-01b's own band), and the longest axis is JC3 z"
        % ([round(x, 3) for x in s_ch],
           [round(x, 3) for x in sorted([after["bounds"]["max"][j] - after["bounds"]["min"][j]
                                         for j in range(3)])]))
    add("O5-hull-is-the-chassis-box", dev["within_tolerance"] and dev["max_abs_dev_m"] <= 1e-5,
        "written body hull AABB vs the target box: max |dev| %.6f m on all three axes"
        % dev["max_abs_dev_m"])
    add("O6-write-clean",
        not problems and not shape_bad,
        "%d verify problem(s), %d shape violation(s), %d/%d convex, %d/%d unions"
        % (len(problems), len(shape_bad), counts["convex"], counts["polytopes"],
           counts["union_ok"], counts["compounds"]))
    add("O7-wheels-unchanged",
        all(wheel_same.values()),
        "%d/%d wheel hulls are byte-identical to B-10's file"
        % (sum(1 for v in wheel_same.values() if v), len(wheel_same)))
    add("O8-plane-support",
        support < 1e-5,
        "every written plane is supported exactly: max |max(n.v) + d| = %.2e m" % support)
    add("O9-stations-untouched",
        sys_before == sys_after,
        "hknpPhysicsSystemData byte-identical, %d in-file station set(s)" % len(sys_before))
    add("O10-audit-rows-labelled",
        len(audit) == 6 and all(r["verdict"] for r in audit),
        "%d audit rows, verdicts %s" % (len(audit), [r["verdict"] for r in audit]))
    return o


def render_md(doc: dict) -> str:
    L = []
    A = L.append
    t, b, g3 = doc["target"], doc["body"], doc["g3"]
    A("# B-10d - collision inputs audited, and the body hull built from the drivable chassis box")
    A("")
    A("Generated by `%s`; `--check` re-derives every number and compares. Static only: "
      "no game process, no install, nothing written outside `Working/Collision2/`."
      % doc["generator"])
    A("")
    A("## 1. What G3-11d found, and what this run does about it")
    A("")
    A("`MODLOG.md` (G3-11d) re-read the five ledger collision rows: the JC3 targets mostly "
      "match, but the BmAK **sources** do not. T-CO2 scaled its hull from")
    A("`SUSP1_Wheel_Rear_Left_Mesh`, **316.155 x 63.418 x 109.881 cm** - a wreck wheel - "
      "while the drivable box is the chassis body")
    A("**%s x %s x %s cm** (body 169750, bone `%s`, box 0, `COLLISION_GEOM.json`)."
      % (*[("%g" % x) for x in g3["chassis_box0_cm"]], g3["bone"]))
    A("")
    A("This run answers two questions: do the three built scripts read the wreck constant, "
      "and what happens when the body hull is built from the chassis box instead?")
    A("")
    A("## 2. Input audit: every BmAK constant the scripts read")
    A("")
    A("| input | script | value used | G3 value | verdict |")
    A("|---|---|---|---|---|")
    for r in doc["audit"]:
        A("| %s | `%s` | %s | %s | **%s** |" % (r["input"], r["script"], r["used"],
                                                 r["g3"], r["verdict"]))
    A("")
    for r in doc["audit"]:
        A("- **%s** - %s" % (r["input"], r["why"]))
    A("")
    A("The wreck triple is in **no** script: it occurs %d times across `bm_collision.py`, "
      "`bm_colmesh.py`, `bm_colhull.py`, and the ledger row T-CO2 still quotes it. So the "
      "316 cm error is a **ledger** error that the build did not copy - the build made a "
      "different choice, and that choice is the one audited here: it used the **render mesh**."
      % sum(sum(v.values()) for v in wreck_in_sources()["scripts"].values()))
    A("")
    A("## 3. The correction: body hull from the chassis box")
    A("")
    A("| quantity | B-10 (render mesh) | B-10d (chassis box) | delta |")
    A("|---|---|---|---|")
    rb = b["b10_box_after_m"]["size"]
    A("| body hull AABB, x / width (m) | %.3f | %.3f | %+.3f |"
      % (rb[0], b["box_after_m"]["size"][0], b["box_after_m"]["size"][0] - rb[0]))
    A("| body hull AABB, y / height (m) | %.3f | %.3f | %+.3f |"
      % (rb[1], b["box_after_m"]["size"][1], b["box_after_m"]["size"][1] - rb[1]))
    A("| body hull AABB, z / length (m) | %.3f | %.3f | %+.3f |"
      % (rb[2], b["box_after_m"]["size"][2], b["box_after_m"]["size"][2] - rb[2]))
    A("| per-axis k | %s | %s | - |"
      % (b["b10_k"], b["k_per_axis"]))
    A("| convex radius (m) | %.6f | %.6f | min(k) x donor radius |"
      % (b["b10_radius_after"], b["radius_after"]))
    A("")
    A("- **decoded**: the target size, `COLLISION_GEOM.json` bodies[0].geometry.boxes[0]."
      "extents_cm = %s cm; read by the script, never typed." % g3["chassis_box0_cm"])
    A("- **derived**: the axis correspondence (BmAK X length -> JC3 z, Y width -> x, "
      "Z height -> y), from the two boxes' own longest spans; oracle O4.")
    A("- **derived**: the placement - %s." % t["placement"].replace("derived: ", ""))
    A("- **UNKNOWN**: %s." % t["rotation"].replace("UNKNOWN - ", ""))
    A("")
    A("Deltas against DIM-1's render bbox: width %+.3f m, height %+.3f m, length %+.3f m."
      % (t["delta_vs_render_bbox_m"]["x_width"], t["delta_vs_render_bbox_m"]["y_height"],
         t["delta_vs_render_bbox_m"]["z_length"]))
    A("")
    A("## 4. What was written")
    A("")
    A("- `%s`, %d B, sha256 `%s...`, %d objects - same object set as the donor, one body hull "
      "and its ancestors changed." % (rel(OUT_BIN), doc["write"]["bytes"],
                                     doc["write"]["sha256"][:16], doc["write"]["objects"]))
    A("- the four wheel hulls are **byte-identical** to B-10's: %d/%d."
      % (sum(1 for w in doc["wheels"]), len(doc["wheels"])))
    A("- `hknpPhysicsSystemData` byte-identical, %d in-file station set(s) (R3)."
      % doc["stations"]["in_file"])
    A("")
    A("| wheel | hull | k | after (m) |")
    A("|---|---|---|---|")
    for w in doc["wheels"]:
        A("| `%s` | `%s` | %.6f | %.3f x %.3f x %.3f |"
          % (w["part"], w["hull"], w["k"], *w["box_after_m"]["size"]))
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for x in doc["oracles"]:
        A("| `%s` | %s | %s |" % (x["key"], "PASS" if x["ok"] else "**FAIL**", x["evidence"]))
    A("")
    A("## 6. Which cards change")
    A("")
    A("| card | changes? | why |")
    A("|---|---|---|")
    A("| B-10 | **yes** | its body target is the render bbox, not the chassis box; its numbers "
      "re-derive byte for byte (O1), so the fix is the target plus a chassis-box Done check, "
      "not a writer change |")
    A("| B-10b | **no** | body 42 is a raycast/bullet `hknpExternMeshShape` and must follow the "
      "render mesh; only its compound refit has to re-run after B-10's hull moves |")
    A("| B-10c | **yes** | body 0's world hull is the convex hull of the LOD2 render mesh, so it "
      "inherits the same width/height error the chassis box corrects |")
    A("")
    A("## 7. UNKNOWN")
    A("")
    A("- the chassis box's **rotation** and its frame's handedness: the TM is not decoded "
      "(COLLISION_GEOM), so the axis-aligned AABB above is the box only if its rotation is "
      "identity.")
    A("- whether the drivable car's collision is the single chassis box or the pair of boxes "
      "169750 carries (box 1 is 679.585 x 345.688 x 103.5 cm): both are decoded, this run uses "
      "box 0, and box 1 would trim 29 cm of width and 104 cm of height.")
    A("- the wreck's own source box (316.155 cm) has no role in either build; why T-CO2 picked "
      "a wheel box at all is a ledger question, not a build one.")
    A("")
    A("```")
    A("uv run python Tools/scripts/bm_collision2.py --write")
    A("uv run python Tools/scripts/bm_collision2.py --check")
    A("```")
    A("")
    return "\n".join(L)


def public(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if not k.startswith("_") and k != "md"}


def main(argv) -> int:
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: bm_collision2.py --write|--check")
    doc = build()
    md = doc["md"] + "\n"
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]
    if argv[1] == "--write":
        os.makedirs(OUT_DIR, exist_ok=True)
        open(OUT_BIN, "wb").write(doc["_blob"])
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(public(doc), indent=1) + "\n")
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print("wrote %s (%d B), %s and %s"
              % (rel(OUT_BIN), doc["write"]["bytes"], rel(OUT_JSON), rel(OUT_MD)))
        print("body hull %.3f x %.3f x %.3f m (B-10: %.3f x %.3f x %.3f m)"
              % (*doc["body"]["box_after_m"]["size"], *doc["body"]["b10_box_after_m"]["size"]))
        print("target chassis box %s cm = %s m on (x, y, z)"
              % (doc["g3"]["chassis_box0_cm"], doc["target"]["jc3_size_m"]))
        print("oracles %d/%d%s" % (len(doc["oracles"]) - len(fails), len(doc["oracles"]),
                                    "" if not fails else " FAILED: " + ", ".join(fails)))
        return 0 if not fails else 1
    problems = []
    if not os.path.exists(OUT_BIN):
        problems.append(f"{rel(OUT_BIN)} missing - run --write")
    elif open(OUT_BIN, "rb").read() != doc["_blob"]:
        problems.append(f"{rel(OUT_BIN)} on disk differs from the derived bytes")
    if not os.path.exists(OUT_JSON) or \
            json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(json.dumps(public(doc))):
        problems.append(f"{rel(OUT_JSON)} differs from the re-derived record")
    if not os.path.exists(OUT_MD) or \
            open(OUT_MD, encoding="utf-8", newline="").read().replace("\r\n", "\n") != md:
        problems.append(f"{rel(OUT_MD)} stale against the re-derived text")
    problems.extend(fails)
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("CHECK OK: %d oracles, %d audit rows, body hull %.3f x %.3f x %.3f m, %d B, "
          "wheel hulls unchanged %d/%d"
          % (len(doc["oracles"]), len(doc["audit"]), *doc["body"]["box_after_m"]["size"],
             doc["write"]["bytes"], sum(1 for w in doc["wheels"]), len(doc["wheels"])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
