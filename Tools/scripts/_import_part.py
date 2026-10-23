"""Parametric PSKX -> RBM asset importer: every alignment/scale number lives in
the SPEC FILE, never in this code. One grab logic for all parts; specs are data.

Spec keys:
  pskx       source asset
  keep       material-name substrings to keep
  allow_wheels  also match the wheel/tyre/disc/cockpit materials psk2rbm excludes
  split      null, or {axes:[0,1], at:'median', pick:'largest'} (car-corner split)
  components null, or {min_faces:N, max_dist:U} (connected-component filter; PSK units)
  fit        {mode:'length'|'diameter', to:<reference RBM>} (uniform scale + center/bottom)
  template   {rbm:<path>, block:N|null, writer:'plain'|'deform'}
               plain  = single 12/24 CarPaintMM template (wheels, DaBaby head)
               deform = Nth block of a deform template, kept as deform or --plain-cleared
  plain      with writer deform: clear IS_DEFORM (0x1000), like psk2rbm --plain
  tris       Blender decimate budget; max_verts/weld as in psk2rbm
  out        output .rbm (obj = out with .obj)

Usage: python _import_part.py <spec.json>
Writes the .rbm (+ .obj) and prints a manifest line (spec echo + sha + counts).
Exit nonzero unless every oracle passes (byte roundtrip, counts, u16, finite).
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import rbm_geom as R  # noqa: E402
from psk2rbm import (blender_decimate, build_rbm, build_rbm_deform,  # noqa: E402
                     build_rbm_plain, fit_box, read_obj, read_pskx,
                     smooth_normals, to_jc3, verify, write_obj)

WHEEL_EXCLUDE = ("Wheel_V2", "Tyre", "Discbreak", "Cockpit")


def connected_filter(P, tri_w, W, min_faces, max_dist):
    """Keep components >= min_faces faces whose centroid is within max_dist
    (PSK units) of the largest component. Returns kept face indices."""
    pt = W["p"][tri_w]
    parent = list(range(len(tri_w)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    edge = {}
    for i in range(len(tri_w)):
        a, b, c = sorted(int(x) for x in pt[i])
        for e in ((a, b), (b, c), (a, c)):
            if e in edge:
                ra, rb = find(i), find(edge[e])
                if ra != rb:
                    parent[ra] = rb
            else:
                edge[e] = i
    sizes = Counter(find(i) for i in range(len(tri_w)))
    big = {r for r, n in sizes.items() if n >= min_faces}
    pos = P[W["p"].astype(int)]
    cents = np.array([pos[tri_w[i]].mean(0) for i in range(len(tri_w))])
    by_root = np.array([c for i, c in enumerate(cents)
                        if find(i) == max(sizes, key=sizes.get)]).mean(0)
    near = set()
    for r in big:
        c = np.array([c for i, c in enumerate(cents) if find(i) == r]).mean(0)
        if float(np.linalg.norm(c - by_root)) <= max_dist:
            near.add(r)
    kept = [i for i in range(len(tri_w)) if find(i) in near]
    print("  components: %d, kept %d faces in %d" % (len(sizes), len(kept), len(near)))
    return kept


def fit_diameter(T, lo, hi):
    """Uniform scale so the largest of height/length matches the reference box
    (wheel convention: axle along X, diameter in the Y-Z plane), then the same
    center-X/Z + bottom-Y convention as fit_box."""
    tlo, thi = T.min(0), T.max(0)
    s = (hi[1] - lo[1]) / max(thi[1] - tlo[1], thi[2] - tlo[2])
    T = (T - [(tlo[0] + thi[0]) / 2, tlo[1], (tlo[2] + thi[2]) / 2]) * s
    return T + [(lo[0] + hi[0]) / 2, lo[1], (lo[2] + hi[2]) / 2], s


def run(spec):
    global P_
    P_, W, F, mats = read_pskx(spec["pskx"])
    keep = spec["keep"]
    excl = spec.get("exclude", [] if spec.get("allow_wheels")
                      else list(WHEEL_EXCLUDE))
    km = [i for i, nm in enumerate(mats) if any(k in nm for k in keep)
          and not any(x in nm for x in excl)]
    print("materials kept:", ", ".join(mats[i] for i in km))
    sel = np.isin(F["m"], km)
    faces = np.where(sel)[0]
    print("  faces %d of %d" % (len(faces), len(F)))

    sp = spec.get("split")
    if sp:
        pos = P_[W["p"].astype(int)]
        cen = pos[F["w"][faces]].mean(1)
        at = sp.get("at", "median")
        med = [np.median(cen[:, a]) if at == "median" else 0.0
               for a in sp["axes"]]
        groups = {}
        for i, f in enumerate(faces):
            key = tuple(int(cen[i][a] > m) for a, m in zip(sp["axes"], med))
            groups.setdefault(key, []).append(f)
        pick = sp.get("pick", "largest")
        faces = (np.array(groups[tuple(pick)]) if isinstance(pick, list)
                 else np.array(max(groups.values(), key=len)))
        print("  split quadrants (at %s): %s -> took %d" % (
            at, {k: len(v) for k, v in groups.items()}, len(faces)))

    tri_w = F["w"][faces].astype(np.int64)
    cp = spec.get("components")
    if cp:
        keep_idx = connected_filter(P_, tri_w, W, cp["min_faces"], cp["max_dist"])
        tri_w = tri_w[keep_idx]
    used = np.unique(tri_w)
    remap = np.full(len(W), -1, np.int64)
    remap[used] = np.arange(len(used))
    Vw = to_jc3(P_[W["p"][used]])
    UVw = np.stack([W["u"][used], 1.0 - W["v"][used]], 1)

    ref = R.decode(open(spec["fit"]["to"], "rb").read())
    lo, hi = np.array(ref.bbox_min), np.array(ref.bbox_max)
    mode = spec["fit"]["mode"]
    Vw, s = (fit_box(Vw, lo, hi, "length") if mode == "length"
             else fit_diameter(Vw, lo, hi))
    print("  scale %.5f (mode %s)" % (s, mode))

    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "in.obj")
        dst = os.path.join(td, "out.obj")
        write_obj(src, Vw, UVw, remap[tri_w])
        blender_decimate(src, dst, spec["tris"])
        if spec.get("obj"):
            shutil.copy(dst, spec["obj"])
        V, UV, I, pos_id = read_obj(dst)
    UV[:, 1] = 1.0 - UV[:, 1]
    if spec.get("weld"):
        uniq, first, inv = np.unique(pos_id, return_index=True, return_inverse=True)
        V, UV, I, pos_id = V[first], UV[first], inv[I], np.arange(len(uniq))
    if len(V) > 65535:
        raise SystemExit("%d verts exceed u16: lower tris" % len(V))
    N = smooth_normals(V, I, pos_id)
    if spec.get("max_verts") and len(V) > spec["max_verts"]:
        area = np.linalg.norm(np.cross(V[I[:, 1]] - V[I[:, 0]], V[I[:, 2]] - V[I[:, 0]]), axis=1)
        used_s, keep_t = set(), []
        for t in np.argsort(-area):
            new = set(I[t]) - used_s
            if len(used_s) + len(new) > spec["max_verts"]:
                continue
            used_s |= new
            keep_t.append(t)
        idx = np.array(sorted(used_s))
        remap2 = np.full(len(V), -1, np.int64)
        remap2[idx] = np.arange(len(idx))
        V, UV, N, I = V[idx], UV[idx], N[idx], remap2[I[np.array(keep_t)]]

    t = spec["template"]
    if t["writer"] == "plain" and t.get("block") is None:
        m = build_rbm(t["rbm"], V, UV, I, N)
    elif t["writer"] == "deform":
        m = (build_rbm_plain(t["rbm"], t["block"], V, UV, I, N)
             if spec.get("plain") else build_rbm_deform(t["rbm"], t["block"], V, UV, I, N))
    else:
        raise SystemExit("bad template spec (plain needs block:null, deform needs block:N)")
    raw = m.write()
    err = verify(raw, V, I, N)
    if err:
        raise SystemExit("VERIFY FAILED: " + err)
    open(spec["out"], "wb").write(raw)
    lo_o, hi_o = V.min(0), V.max(0)
    print("wrote %s: %d B, %d verts, %d tris, bbox %.3fx%.3fx%.3f VERIFY PASS" % (
        spec["out"], len(raw), len(V), len(I),
        hi_o[0] - lo_o[0], hi_o[1] - lo_o[1], hi_o[2] - lo_o[2]))
    print("manifest:", json.dumps({
        "out": spec["out"], "sha256": hashlib.sha256(raw).hexdigest(),
        "verts": len(V), "tris": len(I),
        "bbox": [round(float(x), 4) for x in list(lo_o) + list(hi_o)]}))


if __name__ == "__main__":
    run(json.load(open(sys.argv[1])))
