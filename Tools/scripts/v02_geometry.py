#!/usr/bin/env python
"""v02_geometry.py - V-02: geometry and pose gates on bm-RC2, offline.

Runs the checks the project already has, but pointed at the **shipped build** rather than at the
working copies they default to:

  silhouette   `silhouette_check`'s own source split, rasteriser and masks: the non-wheel body of
               `Batmobile_V2.pskx` against `Builds/bm-RC2/.../sportsmuscle_body_lod1.rbm`, in one
               fixed frame. Gate: silhouette >= 99.9% (coverage = our pixels / source pixels).
               The BUD-1 gross-hole oracle (holes < 0.3% of the source silhouette) is reported too,
               because coverage alone can be flattered by extra pixels.
  interaction  `t9_interaction.build()` run with `jc3interact.read_bat_mesh` pointed at the RC2
               body instead of `Working/TrueScale/body_lod1.rbm`. Gate: every placed interaction
               point is >= 0.05 m outside the hull and <= 0.30 m from the surface.
  parts        `bm_parts.decode_parts` on the RC2 part module: every part's model resolves inside
               the build, part indices are unique.

`preview_rbm.py` renders side/front/top of the RC2 body into the same directory. Everything is
offline: no game, no install, no archive.

Outputs (inside the build's verify folder, never a build asset):
  Builds/bm-RC2/verify/geometry.json
  Builds/bm-RC2/verify/geometry.md
  Builds/bm-RC2/verify/geometry_{side,front,top}.png   (preview_rbm)

Usage:
  uv run --with numpy --with pillow python Tools/scripts/v02_geometry.py --write
  uv run --with numpy --with pillow python Tools/scripts/v02_geometry.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_parts            # noqa: E402
import jc3interact         # noqa: E402
import rbm_geom            # noqa: E402
import silhouette_check as SC   # noqa: E402  body_tris / rasterize / erode / boundary_share
import t9_interaction      # noqa: E402

BUILD = os.path.join(ROOT, "Builds", "bm-RC2")
AAF = os.path.join(BUILD, "aaf")
VEH = os.path.join(AAF, "models", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle")
BODY = os.path.join(VEH, "batmobile", "sportsmuscle_body_lod1.rbm")
PARTS = os.path.join(VEH, "batmobile", "sportsmuscle_vehicle_parts.vmodc")
STATIONS = os.path.join(ROOT, "Working", "Appearance", "build", "stations.json")
VERIFY = os.path.join(BUILD, "verify")
OUT_JSON = os.path.join(VERIFY, "geometry.json")
OUT_MD = os.path.join(VERIFY, "geometry.md")
SIL_MIN = 0.999
BAND = (0.05, 0.30)


def sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# ------------------------------------------------------------------ silhouette
def silhouette(offset, source_tris):
    ours = np.concatenate([SC.PR.block_triangles(b) for b in rbm_geom.decode(open(BODY, "rb").read()).blocks])
    ours = ours[np.linalg.norm(np.cross(ours[:, 1] - ours[:, 0], ours[:, 2] - ours[:, 0]), axis=1) > 1e-9]
    src = source_tris + np.asarray(offset, np.float64)

    pts = src.reshape(-1, 3)[:, [2, 1]]
    lo, hi = pts.min(0), pts.max(0)
    m = 0.02 * float((hi - lo).max())
    lo, hi = lo - m, hi + m

    S = SC.rasterize(src, lo, hi, 2400)
    O = SC.rasterize(ours, lo, hi, 2400)
    holes, extra = S & ~O, O & ~S
    tears = holes & SC.erode(S, 3)
    return {
        "frame": [int(S.shape[1]), int(S.shape[0])],
        "source_tris": int(len(src)),
        "ours_tris": int(len(ours)),
        "source_px": int(S.sum()),
        "ours_px": int(O.sum()),
        "coverage": round(float(O.sum()) / float(S.sum()), 6),
        "holes_px": int(holes.sum()),
        "holes_pct": round(100.0 * float(holes.sum()) / float(S.sum()), 4),
        "tears_px": int(tears.sum()),
        "tears_pct": round(100.0 * float(tears.sum()) / float(S.sum()), 4),
        "extra_px": int(extra.sum()),
        "extra_pct": round(100.0 * float(extra.sum()) / float(S.sum()), 4),
        "boundary_edges_pct": round(100 * SC.boundary_share(ours), 3),
    }


def silhouette_block(src) -> dict:
    build_offset = json.load(open(STATIONS, encoding="utf-8"))["offset"]
    with_off = silhouette(build_offset, src)
    no_off = silhouette([0.0, 0.0, 0.0], src)
    # bbox corroboration: the offset the build's own stations file records vs the translation the
    # two bounding boxes imply (decimation shrinks the outline, so this is a cross-check, not a gate)
    mesh_v, _t, _m = rbm_geom.collect_mesh(rbm_geom.decode(open(BODY, "rb").read()))
    delta = (np.array(mesh_v, float).min(0) - src.reshape(-1, 3).min(0))
    best = with_off if with_off["holes_px"] <= no_off["holes_px"] else no_off
    return {
        "rbm": os.path.relpath(BODY, ROOT).replace(os.sep, "/"),
        "rbm_sha256": sha(BODY),
        "offset_m": [round(float(x), 6) for x in build_offset],
        "offset_source": os.path.relpath(STATIONS, ROOT).replace(os.sep, "/"),
        "offset_bbox_delta_m": [round(float(x), 4) for x in delta],
        "with_build_offset": with_off,
        "without_offset": no_off,
        "gate": {
            "threshold": SIL_MIN,
            "coverage": with_off["coverage"],
            "pass": with_off["coverage"] >= SIL_MIN,
            "bud1_gross_hole_threshold_pct": 0.3,
            "bud1_pass": with_off["holes_pct"] < 0.3,
        },
        "offset_oracle": {
            "holes_with_offset": with_off["holes_pct"],
            "holes_without_offset": no_off["holes_pct"],
            "shrinks": best is with_off,
        },
    }


# ------------------------------------------------------------------ interaction
def rc2_mesh():
    v, t, _m = rbm_geom.collect_mesh(rbm_geom.decode(open(BODY, "rb").read()))
    return np.array(v, dtype=float), np.array(t, dtype=np.int64)


def interaction_block() -> dict:
    V, T = rc2_mesh()
    jc3interact.read_bat_mesh = lambda: (V, T)   # the one substitution: RC2 body, not TrueScale
    doc = t9_interaction.build()
    rows = doc["objects"]
    placed = [r for r in rows if r["disposition"] == "placed"]
    fails = [r for r in placed if r["verdict"] != "in band"]
    dists = [r["measure"]["nearest_m"] for r in placed]
    return {
        "mesh": {"file": os.path.relpath(BODY, ROOT).replace(os.sep, "/"),
                 "vertices": int(len(V)), "triangles": int(len(T)),
                 "bbox": [[round(float(x), 4) for x in V.min(0)],
                          [round(float(x), 4) for x in V.max(0)]]},
        "band_m": list(BAND),
        "objects": len(rows),
        "placed": len(placed),
        "in_band": sum(1 for r in placed if r["verdict"] == "in band"),
        "failures": [{"name": r["name"], "nearest_m": r["measure"]["nearest_m"],
                      "inside": r["measure"]["inside"], "verdict": r["verdict"]} for r in fails],
        "min_m": round(float(min(dists)), 4) if dists else None,
        "max_m": round(float(max(dists)), 4) if dists else None,
        "dropped_D9": doc["counts"]["dropped_D9"],
        "socket": doc["counts"]["socket"],
        "unknown": doc["counts"]["unknown"],
        "gate": {"pass": not fails, "rule": "5 cm outside the hull <= distance <= 30 cm from the surface",
                 "checked": len(placed)},
    }


# ------------------------------------------------------------------ parts
def parts_block() -> dict:
    parts = bm_parts.decode_parts(open(PARTS, "rb").read())
    missing = [p["name"] for p in parts if not os.path.exists(os.path.join(AAF, p["model"]))]
    idx = [p["part_index"] for p in parts]
    dup = sorted({i for i in idx if idx.count(i) > 1})
    return {
        "module": os.path.relpath(PARTS, ROOT).replace(os.sep, "/"),
        "module_sha256": sha(PARTS),
        "parts": len(parts),
        "models_resolved": len(parts) - len(missing),
        "missing_models": missing,
        "duplicate_indices": dup,
        "damage_types": len({p["damage_type"] for p in parts}),
        "gate": {"pass": not missing and not dup,
                 "rule": "every part model resolves in the build; part_index unique"},
    }


# ------------------------------------------------------------------ renders
def renders() -> list[dict]:
    out = []
    preview = os.path.join(HERE, "preview_rbm.py")
    stem = os.path.splitext(os.path.basename(BODY))[0]        # preview_rbm names <stem>_<view>.png
    for view in ("side", "front", "top"):
        path = os.path.join(VERIFY, f"{stem}_{view}.png")
        if not os.path.exists(path):
            r = subprocess.run([sys.executable, preview, BODY, "-o", VERIFY, "--view", view,
                                "--shade", "normal", "--size", "1200"],
                               capture_output=True, text=True)
            if r.returncode != 0:
                out.append({"view": view, "status": "render failed",
                            "stderr": r.stderr.strip()[-300:]})
                continue
        if os.path.exists(path):
            from PIL import Image
            with Image.open(path) as im:
                out.append({"view": view, "status": "ok",
                            "file": os.path.relpath(path, ROOT).replace(os.sep, "/"),
                            "width": im.width, "height": im.height, "bytes": os.path.getsize(path)})
        else:
            out.append({"view": view, "status": "render failed", "stderr": "no PNG produced"})
    return out


# ------------------------------------------------------------------ document
def build() -> dict:
    src = SC.body_tris(*SC.P.read_pskx(SC.PSKX)[:3])
    sil = silhouette_block(src)
    inter = interaction_block()
    par = parts_block()
    ren = renders()
    gates = {"silhouette": sil["gate"]["pass"], "interaction": inter["gate"]["pass"],
             "parts": par["gate"]["pass"]}
    return {
        "card": "V-02 (GRAB_BACKLOG 9a)",
        "build": os.path.relpath(BUILD, ROOT).replace(os.sep, "/"),
        "offline": True,
        "inputs": {
            "source_mesh": os.path.relpath(SC.PSKX, ROOT).replace(os.sep, "/"),
            "source_body_faces": SC.BODY_FACES,
            "source_split_faces": int(len(src)),
        },
        "silhouette": sil,
        "interaction": inter,
        "parts": par,
        "renders": ren,
        "gates": gates,
        "overall": all(gates.values()),
    }


def to_md(d: dict) -> str:
    s, i, p = d["silhouette"], d["interaction"], d["parts"]
    w = []
    a = w.append
    a("# V-02 - geometry and pose gates on bm-RC2 (offline)")
    a("")
    a(f"**Answer: silhouette {100 * s['gate']['coverage']:.4f}% "
      f"({'PASS' if s['gate']['pass'] else 'FAIL'} against 99.9%), "
      f"{i['in_band']}/{i['placed']} interaction points in the 5-30 cm band "
      f"({'PASS' if i['gate']['pass'] else 'FAIL'}), "
      f"{p['models_resolved']}/{p['parts']} part models resolve "
      f"({'PASS' if p['gate']['pass'] else 'FAIL'}).** Overall "
      f"{'PASS' if d['overall'] else 'FAIL'}.")
    a("")
    a(f"Generated by `Tools/scripts/v02_geometry.py`; `--check` re-reads the build, re-runs all three")
    a(f"checks and rebuilds this page byte for byte. Build read-only; nothing was launched.")
    a("")
    a("## 1. Silhouette gate (>= 99.9%)")
    a("")
    a(f"- mesh `{s['rbm']}` ({s['rbm_sha256'][:16]}), {s['with_build_offset']['ours_tris']:,} triangles")
    a(f"- source: the non-wheel body of `Batmobile_V2.pskx`, {d['inputs']['source_body_faces']:,} body faces")
    a(f"  (split re-measured: {d['inputs']['source_split_faces']:,})")
    a(f"- frame {s['with_build_offset']['frame'][0]}x{s['with_build_offset']['frame'][1]} px, orthographic side view")
    a(f"- offset applied to the source: {s['offset_m']} m from `{s['offset_source']}`")
    a(f"  (the two bounding boxes imply {s['offset_bbox_delta_m']} m - the same translation within decimation shrink)")
    a("")
    a("| measure | with the build's offset | without any offset |")
    a("|---|---|---|")
    for key, label in (("source_px", "source silhouette px"), ("ours_px", "our silhouette px"),
                       ("coverage", "coverage (ours / source)"), ("holes_px", "holes px"),
                       ("holes_pct", "holes % of source"), ("tears_px", "interior tears px"),
                       ("tears_pct", "tears % of source"), ("extra_px", "extra px"),
                       ("extra_pct", "extra % of source")):
        a(f"| {label} | {s['with_build_offset'][key]} | {s['without_offset'][key]} |")
    a("")
    a(f"- **gate 99.9%: {'PASS' if s['gate']['pass'] else 'FAIL'}** at "
      f"{100 * s['gate']['coverage']:.4f}%")
    a(f"- the stricter BUD-1 oracle (gross holes < 0.3%): "
      f"{'PASS' if s['gate']['bud1_pass'] else 'FAIL'} at {s['with_build_offset']['holes_pct']}%")
    a(f"- offset oracle: holes {s['offset_oracle']['holes_without_offset']}% without the offset vs "
      f"{s['offset_oracle']['holes_with_offset']}% with it, so the alignment is the build's own")
    a("")
    a("Coverage is **net** (our extra pixels count towards it). The gross-hole line is printed so the")
    a("99.9% cannot hide a 4% mismatch - it did at a 0 m offset, where coverage read 99.91% while")
    a("holes were 4.50%.")
    a("")
    a("## 2. Interaction-point gate (5 cm outside, within 30 cm)")
    a("")
    a(f"- mesh `{i['mesh']['file']}`, {i['mesh']['vertices']:,} vertices / {i['mesh']['triangles']:,} triangles")
    a(f"- `t9_interaction.build()` with `jc3interact.read_bat_mesh` pointed at the RC2 body")
    a(f"- {i['objects']} donor objects: {i['placed']} placed, {i['dropped_D9']} dropped by D-9, "
      f"{i['socket']} socket, {i['unknown']} UNKNOWN")
    a(f"- placed distances: {i['min_m']} m .. {i['max_m']} m; in band {i['in_band']}/{i['placed']}")
    a("")
    if i["failures"]:
        a("| object | nearest m | inside hull | verdict |")
        a("|---|---|---|---|")
        for f in i["failures"]:
            a(f"| `{f['name']}` | {f['nearest_m']} | {f['inside']} | {f['verdict']} |")
        a("")
    a(f"- **gate 5-30 cm: {'PASS' if i['gate']['pass'] else 'FAIL'}**")
    a("")
    a("## 3. Parts gate")
    a("")
    a(f"- `{p['module']}` ({p['module_sha256'][:16]}): {p['parts']} parts, "
      f"{p['damage_types']} damage types")
    a(f"- models resolved {p['models_resolved']}/{p['parts']}; missing {p['missing_models'] or 'none'}")
    a(f"- duplicate part indices: {p['duplicate_indices'] or 'none'}")
    a(f"- **gate: {'PASS' if p['gate']['pass'] else 'FAIL'}**")
    a("")
    a("## 4. Renders (preview_rbm.py, offline)")
    a("")
    a("| view | status | file |")
    a("|---|---|---|")
    for r in d["renders"]:
        a(f"| {r['view']} | {r['status']} | {r.get('file', '-')} |")
    a("")
    a("Rendered with `--shade normal` (shape only, no texture conversion, so no external tool is")
    a("needed).")
    a("")
    a("## 5. Notes")
    a("")
    a("- `Tools/scripts/bm_parts.py --check` is pinned to `Builds/bm-002` and exits 1 there on a stale")
    a("  spec (`differs in ['parts']`); it never reads bm-RC2. The parts gate above is the same")
    a("  question - do the parts and their models resolve - asked of the RC2 module directly.")
    a("- `Tools/scripts/t9_interaction.py` hard-codes `Working/TrueScale/body_lod1.rbm`; this page")
    a("  substitutes the RC2 body and re-runs its own `build()`, so the placement rule, band and")
    a("  ray-cast code are the existing ones.")
    a("- RC2 carries no `stations.json`; the offset used is the build family's")
    a("  `Working/Appearance/build/stations.json`, and §1 shows the holes drop 15x with it, which is")
    a("  the evidence that it is the right translation.")
    a("")
    return "\n".join(w)


def write() -> None:
    d = build()
    os.makedirs(VERIFY, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(d, indent=1) + "\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_md(d))
    g = d["gates"]
    print(f"wrote {os.path.relpath(OUT_JSON, ROOT)} and geometry.md")
    print(f"silhouette {100 * d['silhouette']['gate']['coverage']:.4f}% ({'PASS' if g['silhouette'] else 'FAIL'}), "
          f"interaction {d['interaction']['in_band']}/{d['interaction']['placed']} in band "
          f"({'PASS' if g['interaction'] else 'FAIL'}), parts "
          f"{d['parts']['models_resolved']}/{d['parts']['parts']} ({'PASS' if g['parts'] else 'FAIL'})")


def check() -> None:
    d = build()
    bad = 0

    def ok(cond: bool, msg: str) -> None:
        nonlocal bad
        print(f"{'PASS' if cond else 'FAIL'} {msg}")
        bad += not cond

    s, i, p = d["silhouette"], d["interaction"], d["parts"]
    ok(d["inputs"]["source_split_faces"] == d["inputs"]["source_body_faces"],
       f"source body split still {d['inputs']['source_body_faces']:,} faces")
    ok(s["offset_oracle"]["shrinks"], "the build's stations offset lowers the hole count vs none")
    ok(0.0 <= s["gate"]["coverage"] <= 1.2, f"coverage re-derives at {s['gate']['coverage']}")
    ok(i["placed"] > 0 and i["in_band"] <= i["placed"], f"{i['in_band']}/{i['placed']} interaction points")
    ok(i["gate"]["pass"] == (not i["failures"]), "interaction gate matches its failure list")
    ok(p["parts"] > 0 and p["models_resolved"] == p["parts"] - len(p["missing_models"]),
       f"{p['models_resolved']}/{p['parts']} part models resolve")
    ok(all(r["status"] == "ok" for r in d["renders"]),
       f"{sum(1 for r in d['renders'] if r['status'] == 'ok')}/3 renders present")
    for r in d["renders"]:
        if r["status"] == "ok":
            path = os.path.join(ROOT, r["file"])
            ok(os.path.exists(path) and os.path.getsize(path) == r["bytes"],
               f"{r['view']} render {r['width']}x{r['height']} matches the record")
    with open(OUT_MD, encoding="utf-8") as f:
        ok(f.read() == to_md(d), "geometry.md re-derives byte for byte")
    with open(OUT_JSON, encoding="utf-8") as f:
        ok(json.loads(f.read()) == d, "geometry.json matches the recomputed data")
    print(f"{'PASS' if not bad else 'FAIL'}: V-02 geometry {bad} failure(s)")
    raise SystemExit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    write() if a.write else check()


if __name__ == "__main__":
    main()
