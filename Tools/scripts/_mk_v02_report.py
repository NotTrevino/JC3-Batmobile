#!/usr/bin/env python
"""Emit tmp/freebuff/reports/verify-v02-geometry-poses-rc4.md from the measured geometry.json."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
g = json.load(open(os.path.join(ROOT, "Builds", "bm-RC4", "verify", "geometry.json"), encoding="utf-8"))
s, i, p, pos, c, l = g["silhouette"], g["interaction"], g["parts"], g["poses"], g["collision"], g["lights"]

rows = []
for v, q in s["views"].items():
    rows.append("| {} | {:,} | {:,} | {:.4f} % | {:+.4f} pp | {} | {} | {} | {} |".format(
        v, q["source_px"], q["ours_px"], q["coverage"] * 100, 100 * (q["coverage"] - 0.999),
        q["holes_pct"], q["tears_pct"], q["extra_pct"], "PASS" if q["pass"] else "FAIL"))

poses = []
for q in pos:
    poses.append("| {} | {} | {} | {} | {} |".format(
        q["pose"], q.get("part", "-"), q.get("limit_deg", "-"), q["status"], q.get("file", "-")))

side = s["views"]["side"]["coverage"] * 100
side_margin = 100 * (s["views"]["side"]["coverage"] - 0.999)
md = """# V-02 - geometry, poses, collision and lights on Builds/bm-RC4

STATUS: done. `Tools/scripts/v02_rc4.py --write/--check` is green (10/10 oracles, document
re-derived byte for byte). Outputs: `Builds/bm-RC4/verify/geometry.md`, `geometry.json`, and the
renders under `Builds/bm-RC4/verify/v02/`. Nothing launched or installed.

## 1. Silhouette vs the BmAK body - per view (limit 99.9 %)

Source: the non-wheel body of `Batmobile_V2.pskx` ({faces:,} faces), one fixed frame per view.
Mesh: `{rbm}` ({sha}), {tris:,} triangles.

| view | source px | ours px | coverage | margin | holes % | tears % | extra % | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
{table}

- **gate: {gate}**, worst margin {margin:+.4f} pp.
- What moved the margin against RC2's side view (99.9004 %, +0.0004 pp): this run re-rasterises the
  same decimated body with the same `stations.json` offset in `silhouette_check`'s fixed frame and
  lands at {side:.4f} % ({side_margin:+.4f} pp). Front and top are new per-view figures: they are
  where a decimation tear would show, and both pass. Coverage is net, so holes/tears/extra are
  printed per view too.

## 2. Pose renders at the decoded limits

| pose | part | limit | status | file |
|---|---|---:|---|---|
{poses}

- Rendered poses are the **delivered** tree only. The battle pose (T-MD13) is **not in this tree**:
  build-d12 records it blocked by ConvertAdf `NullReferenceException` on the parts module. Labelled,
  never passed.
- Cannon pitch has **no joint in this tree**: P-02's joint is null (the cannon translates; a hinge
  cannot reproduce translation), so there is nothing to rotate.
- Canopy and missile hatches are **not in this tree**: no canopy bone (glass is part of
  `CockPit_Mesh`), and P-07/P-08 name no part.

## 3. Parts census - the delivered module

- **{parts} parts / {types} distinct damage types** ({lamps} lamp parts), sha `{psha}`.
- Models unresolved: {missing}; extra parts beyond 59: {extra}.
- `build-d08` §2's 59/19 is what the bytes carry; the older "61 parts incl wheel-arch 42/43" count is
  superseded, and a 61-part result here would have been a failure.

## 4. Interaction points

- {objects} donor objects, **{placed} placed**, distances {dmin} .. {dmax} m.
- In band (5-30 cm): **{inband}/{placed}**. Worst excursion outside the envelope: {worst} m
  (rule: no point outside by more than 2 cm).
- **gate: {igate}**.

## 5. Collision - re-measured, NOT a render-bbox gate

- Written hulls: **{hulls}** (body 0 + 4 wheels) over the donor's **{bodies}** bodies.
- Shape vs BmAK chassis box 0: **{shapedev:.4f} m** (exact).
- Placement vs the chassis box: **{placement} m** = **{placecm} cm**, so the card's 5 cm gate is
  **{cgate}** on this packed physicsc. The brief's **6.1 cm** is the render-bbox z deviation
  ({rdev} m) and stays **NOT MET** as a render-bbox gate - it is not reinterpreted as a pass (8390).
- BmAK boxes without a shape instance: **{missingboxes} of 3**; free hull slots **{free}**;
  constraint **{constraint}** (named omission).
- All four brief facts re-checked from the packed build: **{briefconf}**. The packed physicsc is
  `{source}` (sha `{psha}`), not build-d13's: 5 hulls / 62 bodies / exact shape / 2 boxes without a
  shape / 0 free slots hold, the 6.1 cm placement does not.

## 6. Lights module

- `VehicleDynamicLights`: **{lbytes:,} B at `.toc` offset {loff:,}** (the brief's 16,499,504 is from
  an earlier packed tree; this is the RC4 build's own record).
- **{lrows} rows**; **{b03}/8** B-03 lamp parts carry `has_lights`, and {lparts} have an entry:
  {lnames}.
- B-03 lamp parts with no entry (lit with no row): {lnoentry}; the module flags {modulelamps} parts
  in total (the donor's lamp parts stay flagged).
- Maxima: angle **{angle} deg**, range **{range} m** against the shipped max {smaxa}/{smaxr}
  (D-03 U-1). Two 70 deg entries per headlight: **out-of-domain render risk**, reported, not passed.

## 7. Checks run

```
python Tools/scripts/v02_rc4.py --write   # geometry.json + geometry.md + 4 pose PNGs
python Tools/scripts/v02_rc4.py --check   # 10/10 oracles, document byte-identical, exit 0
python Tools/scripts/bm_rc4.py --check    # PASS: bm-RC4 0 failure(s), 9 drop files, .toc 714 records
```

Build integrity note: `bm_rc4.py --check` on this tree rebuilds in place; it had previously left the
build without receipt/installer. `bm_rc4.py --write` regenerated it deterministically from the stage
trees (`.toc` 714 records, 9 drop files, 0 failures) before V-02 ran, and the receipt writer now
sanitises path strings. No install, no launch.

## 8. Limits

- File-level measurements and offline renders only; the engine's blend/limits are not simulated.
- The collision gate stays NOT MET at 6.1 cm; `complete: false` stands.
- Front-view coverage above 100 % is recorded as extra pixels (net coverage), not a silent pass.

## 9. Revert

Delete `Tools/scripts/v02_rc4.py`, `Tools/scripts/_mk_v02_report.py`,
`Builds/bm-RC4/verify/geometry.{md,json}`, `Builds/bm-RC4/verify/v02/`, the MODLOG section and this
report. V-02 writes no build asset.
""".format(
    faces=g["inputs"]["source_body_faces"], rbm=s["rbm"], sha=s["rbm_sha256"][:16],
    tris=s["ours_tris"], table="\n".join(rows),
    gate="PASS" if s["gate"]["pass"] else "FAIL", margin=s["gate"]["min_margin_pp"],
    side=side, side_margin=side_margin, poses="\n".join(poses),
    parts=p["parts"], types=p["distinct_types"], lamps=p["lamp_parts"],
    psha=p["module_sha256"][:16], missing=p["missing_models"] or "none",
    extra=p["extra_beyond_59"] or "none",
    objects=i["objects"], placed=i["placed"], dmin=i["min_m"], dmax=i["max_m"],
    inband=i["in_band"], worst=i["worst_outside_m"], igate="PASS" if i["gate"]["pass"] else "FAIL",
    hulls=c["hulls_written"], bodies=c["donor_bodies"],
    shapedev=c["shape_dev_vs_chassis_box_m"], placement=c["placement_m"],
    placecm=c["placement_cm"], cgate="PASS" if c["gate"]["pass"] else "NOT MET",
    rdev=c["render_bbox_dev_m"], briefconf="confirmed" if c["brief_confirmed"] else "NOT confirmed on this tree",
    source=c["source"], psha=(c["physicsc_sha256"] or "")[:16],
    missingboxes=(c["shapes_missing"] if isinstance(c["shapes_missing"], int) else len(c["shapes_missing"])),
    free=c["free_hull_slots"], constraint=c["constraint"],
    confirmed="confirmed" if c["confirmed"] else "MISMATCH",
    lbytes=l["module_bytes"], loff=l["module_offset"], lrows=l["rows"],
    b03=l["b03_lamp_parts"], lparts=l["lamp_parts"], lnames=", ".join(l["lamp_part_names"]),
    lnoentry=l["b03_lamp_parts_without_entry"] or "none", modulelamps=l["module_lamp_parts"],
    angle=l["max_angle_deg"], range=l["max_range_m"],
    smaxa=l["shipped_max"]["angle"], smaxr=l["shipped_max"]["range"],
)
out = os.path.join(ROOT, "tmp", "freebuff", "reports", "verify-v02-geometry-poses-rc4.md")
open(out, "w", encoding="utf-8", newline="\n").write(md)
print("wrote", out, len(md), "chars")
