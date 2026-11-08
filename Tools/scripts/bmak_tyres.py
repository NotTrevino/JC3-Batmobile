"""bmak_tyres.py - G1-18: the four Batmobile tyres, the three diameters, D-1 (R11).

The card asks which of 1.366 / 1.42 / 1.40 is tread-to-tread, which includes the sidewall bulge
and which is the physics radius x2. Every number in the answer is measured here, from
`Batmobile_V2.pskx` through the ONE transform (`bat_assemble.to_jc3_rot` * `scale` + `offset`,
`Working/TrueScale/stations.json`), on the vertices owned by each wheel bone (`pskx_parts`).

Reads:
  * the PSKX (vertices, faces, per-face material and dominant bone),
  * `stations.json` (scale, offset, ground, per-corner hub / radius / tyre_width),
  * `T_ROWS.jsonl` T-G2 (the `land_global.*_wheels.radius` row) and T-G6 (which keeps the mesh
    radius as the JC3 contact radius),
  * `CHAIN.json` (`SVehicleWheel.WheelRadius`, the BmAK sim radius).

Writes:
    Research/BatmobileGrab/TYRES.md          generated page (tables + the three numbers + D-1)

Usage:
    python Tools/scripts/bmak_tyres.py --write
    python Tools/scripts/bmak_tyres.py --check

`--check` re-derives everything, asserts the invariants the prose relies on and compares the
rendered page with the file on disk, so TYRES.md is generated output from then on.

Deliberately not measured (UNKNOWN, not guessed):
  * the tyre bead aperture and the sidewall ring: the earlier pass quoted ranges with no
    vertex-selection rule, so they cannot be re-derived. No number is printed.
  * what the initial commit's 1.42 in the `bat_assemble.py` docstring measured: no file records
    the method. The quantities near it are printed; the cause is UNKNOWN (R4).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bat_assemble as BA   # noqa: E402  (the ONE transform)
import psk2rbm as P         # noqa: E402
import pskx_parts as PX     # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "TYRES.md")
PSKX = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF",
                    "SkeletalMesh3", "Batmobile_V2.pskx")
STATIONS = os.path.join(ROOT, "Working", "TrueScale", "stations.json")
TROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
CHAIN = os.path.join(OUT, "CHAIN.json")

# corner -> (tyre bone, disc bone, fan bone).  The fronts use `Front` in the *_Vis name and
# `Frnt` in *_Disc/*_Fan; the rears use `Rear` throughout (G1-18's naming gotcha).
CORNERS = (
    ("f_l", "Wheel_Front_Left_Vis", "Wheel_Frnt_Left_Disc", "Wheel_Frnt_Left_Fan"),
    ("f_r", "Wheel_Front_Right_Vis", "Wheel_Frnt_Right_Disc", "Wheel_Frnt_Right_Fan"),
    ("r_l", "Wheel_Rear_Left_Vis", "Wheel_Rear_Left_Disc", "Wheel_Rear_Left_Fan"),
    ("r_r", "Wheel_Rear_Right_Vis", "Wheel_Rear_Right_Disc", "Wheel_Rear_Right_Fan"),
)

_T = None


def transformed():
    """(V, tri, face_bone, bone names) for the PSKX in the JC3 frame, metres."""
    global _T
    if _T is None:
        Pp, W, F, _mats = P.read_pskx(PSKX)
        bones, Wt = PX.skeleton(PSKX)
        names = [b[0] for b in bones]
        fb = PX.face_bones(Pp, W, F, Wt, len(bones))
        st = json.load(open(STATIONS, encoding="utf-8"))
        V = BA.to_jc3_rot(Pp[W["p"]]) * st["scale"] + np.array(st["offset"])
        _T = (V, V[F["w"].astype(np.int64)], fb, names, st, F["w"].astype(np.int64))
    return _T


def bone_faces(bone):
    """(face indices, unique wedge indices) of the faces whose dominant bone is `bone`."""
    V, tri, fb, names, _st, Fw = transformed()
    if bone not in names:
        raise SystemExit("bone %s is not in the PSKX skeleton" % bone)
    idx = np.nonzero(fb == names.index(bone))[0]
    return idx, np.unique(Fw[idx])


def radial(V, pts, hub):
    return np.sqrt((pts[:, 1] - hub[1]) ** 2 + (pts[:, 2] - hub[2]) ** 2)


def measure_corner(key, tyre, disc, fan):
    V, tri, fb, names, st, Fw = transformed()
    hub = np.array(st["corners"][key]["hub_true"])
    tidx, tw = bone_faces(tyre)
    pts = V[tw]
    r = radial(V, pts, hub)
    m = {
        "corner": key, "bone": tyre, "hub": hub,
        "faces": int(len(tidx)), "verts": int(len(tw)),
        "dy": float(pts[:, 1].max() - pts[:, 1].min()),
        "dz": float(pts[:, 2].max() - pts[:, 2].min()),
        "w": float(pts[:, 0].max() - pts[:, 0].min()),
        "maxr": float(r.max()), "dmaxr": float(2 * r.max()),
        "ymin": float(pts[:, 1].min()), "ground": float(st["ground"]),
        "gap": float(pts[:, 1].min() - st["ground"]),
        "x": (float(pts[:, 0].min()), float(pts[:, 0].max())),
        "y": (float(pts[:, 1].min()), float(pts[:, 1].max())),
        "z": (float(pts[:, 2].min()), float(pts[:, 2].max())),
        "station_r": float(st["corners"][key]["radius"]),
        "station_w": float(st["corners"][key]["tyre_width"]),
        "scale": float(st["scale"]),
    }
    # Disc: extents, max radial, and the two "outside the tyre" tests, named.
    didx, dw = bone_faces(disc)
    dpts = V[dw]
    dr = radial(V, dpts, hub)
    beyond_r = dr > m["maxr"]                    # beyond the tyre's max radial (the shoulder)
    beyond_v = np.abs(dpts[:, 1] - hub[1]) > m["station_r"]   # beyond the tyre vertically
    m["disc"] = {
        "bone": disc, "faces": int(len(didx)), "verts": int(len(dw)),
        "x": (float(dpts[:, 0].min()), float(dpts[:, 0].max())),
        "y": (float(dpts[:, 1].min()), float(dpts[:, 1].max())),
        "z": (float(dpts[:, 2].min()), float(dpts[:, 2].max())),
        "maxr": float(dr.max()), "dmaxr": float(2 * dr.max()),
        "gap": float(dpts[:, 1].min() - st["ground"]),
        "beyond_radial": int(beyond_r.sum()),
        "beyond_radial_x": (float(dpts[beyond_r, 0].min()), float(dpts[beyond_r, 0].max())),
        "beyond_radial_z": (float(dpts[beyond_r, 2].min()), float(dpts[beyond_r, 2].max())),
        "beyond_vertical": int(beyond_v.sum()),
        "beyond_vertical_x": (float(dpts[beyond_v, 0].min()), float(dpts[beyond_v, 0].max())),
        "beyond_vertical_z": (float(dpts[beyond_v, 2].min()), float(dpts[beyond_v, 2].max())),
    }
    fidx, fw = bone_faces(fan)
    fpts = V[fw]
    m["fan"] = {
        "bone": fan, "faces": int(len(fidx)), "verts": int(len(fw)),
        "maxr": float(radial(V, fpts, hub).max()),
        "y": float(fpts[:, 1].max() - fpts[:, 1].min()),
        "z": float(fpts[:, 2].max() - fpts[:, 2].min()),
    }
    return m


def wheel_volume_bones(m, slack=0.02, top=2.0):
    """Bones that own faces wholly inside the tyre's bounding box (x/Z +-0.02 m, y 0..2.0)."""
    V, tri, fb, names, _st, Fw = transformed()
    lo = np.array([m["x"][0] - slack, 0.0, m["z"][0] - slack])
    hi = np.array([m["x"][1] + slack, top, m["z"][1] + slack])
    inside = ((tri >= lo) & (tri <= hi)).all(axis=(1, 2))
    rows = {}
    for b in np.unique(fb[inside]):
        rows[names[b]] = int((fb[inside] == b).sum())
    return lo, hi, sorted(rows.items(), key=lambda kv: -kv[1])


def t_rows():
    want = {}
    with open(TROWS, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["id"] in ("T-G2", "T-G6"):
                want[r["id"]] = r
    return want


def wheel_radius_m():
    d = json.load(open(CHAIN, encoding="utf-8"))
    vals = []

    def walk(o):
        if isinstance(o, dict):
            if o.get("name") == "SVehicleWheel.WheelRadius":
                vals.append(o.get("value"))
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(d)
    vals = sorted({v for v in vals if v is not None})
    if len(vals) != 1:
        raise SystemExit("CHAIN.json SVehicleWheel.WheelRadius values: %r" % (vals,))
    return float(vals[0])


def build():
    ms = [measure_corner(*c) for c in CORNERS]
    rows = t_rows()
    if "T-G2" not in rows:
        raise SystemExit("T-G2 is missing from %s" % os.path.relpath(TROWS, ROOT))
    t2 = rows["T-G2"]["cells"]
    radii = [float(x) for x in t2[4].replace("`", "").split("/")]
    wr_cm = wheel_radius_m()
    doc = {
        "corners": ms,
        "scale": ms[0]["scale"],
        "ground": ms[0]["ground"],
        "t2_radii": radii,
        "t2_cells": t2,
        "t6_cells": rows["T-G6"]["cells"] if "T-G6" in rows else None,
        "wheel_radius_m": wr_cm * 0.01,
    }
    return doc


def fmt(v, n=4):
    return ("%." + str(n) + "f") % v


def N(v):
    return "{:,}".format(int(v))


def render(doc):
    ms = doc["corners"]
    ground = doc["ground"]
    dy = [m["dy"] for m in ms]
    sh = [m["dmaxr"] for m in ms]
    wd = [m["w"] for m in ms]
    spread = max(dy) - min(dy)
    dy_mean = sum(dy) / 4.0
    dr_mean = sum(m["station_r"] for m in ms) / 4.0
    rd_gap = max(abs(m["dy"] - 2 * m["station_r"]) for m in ms)
    m0 = ms[0]
    t2 = doc["t2_cells"]
    disc = m0["disc"]
    fan = m0["fan"]
    lo, hi, bones = wheel_volume_bones(m0)
    # union box over tyre + disc + fan (what a box over "the wheel" would read)
    ux = [m0["x"], disc["x"]]
    uy = [m0["y"], disc["y"]]
    union_r = max(m0["maxr"], disc["maxr"], fan["maxr"])
    union_y = max(m0["y"][1], disc["y"][1]) - min(m0["y"][0], disc["y"][0])
    # the 1.40 comparisons, on both bases
    pct_tread = (1.40 / dy_mean - 1) * 100
    ratio_tread = 1.40 / dy_mean
    pct_sh = (1.40 / max(sh) - 1) * 100
    ratio_sh = 1.40 / max(sh)
    bulge = [m["dmaxr"] - m["dy"] for m in ms]
    bulge_mean = max(sh) - dy_mean
    need = 1.40 - dy_mean
    L = []
    a = L.append
    a("# Batmobile tyres — the three diameters (G1-18)")
    a("")
    a("Generated by `Tools/scripts/bmak_tyres.py` from `Batmobile_V2.pskx`, **vertices owned by")
    a("the wheel bones**, in metres through the ONE transform (`bat_assemble.to_jc3_rot`, then ×")
    a("`scale` %s + `offset` from `Working/TrueScale/stations.json`) — the same transform" % fmt(doc["scale"], 2))
    a("`bat_assemble.py` uses for the whole car, so these numbers are directly comparable to")
    a("`T_ROWS.jsonl` T-G1/T-G2 and to JC3's `land_global.*_wheels.radius`. `--check` re-derives")
    a("every number below and compares this page with the stored file.")
    a("")
    a("Axes in that frame (MODLOG §70): **x = axle (lateral, left = −x), y = vertical, z =")
    a("longitudinal**; ground is y = %s." % fmt(ground, 2))
    a("")
    a("## 1. Per wheel — tyre, rim, width")
    a("")
    a("| corner | tyre faces (`*_Vis`) | verts | Ø tread (y) | Ø (z) | Ø max radial | width (x) |")
    a("|---|---|---|---|---|---|---|")
    for m in ms:
        a("| %s | %s | %s | **%s** | %s | %s | %s |" % (
            m["corner"], N(m["faces"]), N(m["verts"]), fmt(m["dy"]), fmt(m["dz"]),
            fmt(m["dmaxr"]), fmt(m["w"])))
    a("")
    a("| corner | station radius | station `tyre_width` | tread bottom − ground |")
    a("|---|---|---|---|")
    for m in ms:
        a("| %s | %s | %s | %+.4f |" % (m["corner"], fmt(m["station_r"]), fmt(m["station_w"]),
                                        m["gap"]))
    a("")
    a("All four tyres are the same mould to **%s mm** (tread Ø %s–%s, shoulder Ø %s–%s," % (
        fmt(spread * 1000, 1), fmt(min(dy)), fmt(max(dy)), fmt(min(sh)), fmt(max(sh))))
    a("width %s–%s m). Each tread Ø is 2 × the corner's `stations.json` `radius` to ≤ %s mm" % (
        fmt(min(wd)), fmt(max(wd)), fmt(rd_gap * 1000, 1)))
    a("(2 × %s–%s = %s–%s); the tread sits on the ground plane (rear %+.4f, front %+.4f)." % (
        fmt(min(m["station_r"] for m in ms)), fmt(max(m["station_r"] for m in ms)),
        fmt(2 * min(m["station_r"] for m in ms)), fmt(2 * max(m["station_r"] for m in ms)),
        min(ms, key=lambda m: m["gap"])["gap"], max(ms, key=lambda m: m["gap"])["gap"]))
    a("")
    a("**Station `tyre_width` is mirrored L↔R in `stations.json`**: the file's f_l %s is the mesh's" % fmt(m0["station_w"]))
    a("f_r width %s, and the file's f_r %s is the mesh's f_l %s (rears likewise). Nothing in" % (
        fmt(ms[1]["w"]), fmt(ms[1]["station_w"]), fmt(m0["w"])))
    a("`stations.json` records a `tyre_bone`, so the derivation cannot be traced; whoever consumes")
    a("`tyre_width` for physics must check the corner attribution (R3).")
    a("")
    a("**Rim** (front-left): `%s`, %d faces. The figure quoted as rim Ø is the **max radial" % (
        fan["bone"], fan["faces"]))
    a("distance from the hub**, %s → **Ø %s**; the cap is dished, so its own y/z extent is" % (
        fmt(fan["maxr"]), fmt(2 * fan["maxr"])))
    a("%s / %s m, not the same measure." % (fmt(fan["y"]), fmt(fan["z"])))
    a("")
    a("**Tyre bead aperture and sidewall ring: UNKNOWN.** The earlier pass quoted Ø1.135–1.360 and")
    a("1.322–1.371 for them, but gave no vertex-selection rule, so neither can be re-derived from")
    a("this page's inputs. No number is printed rather than an unreproducible one (R4).")
    a("")
    a("### The wheel bones (naming gotcha: `Front` vs `Frnt`)")
    a("")
    a("| bone | what it is | front-left extent (m) |")
    a("|---|---|---|")
    a("| `%s` | the tyre | x %s (%s…%s) · y %s · z %s · Ø %s max radial |" % (
        m0["bone"], fmt(m0["w"]), fmt(m0["x"][0], 3), fmt(m0["x"][1], 3), fmt(m0["dy"]),
        fmt(m0["dz"]), fmt(m0["dmaxr"])))
    a(("| `%s` | inner wheel structure (hub / strut / brake), not a second tyre: it spans "
       "the tyre's width | x %s (%s…%s) · y %s (%s…%s) · z %s · Ø %s max radial |") % (disc["bone"],
        fmt(disc["x"][1] - disc["x"][0]), fmt(disc["x"][0], 3), fmt(disc["x"][1], 3),
        fmt(disc["y"][1] - disc["y"][0]), fmt(disc["y"][0], 3), fmt(disc["y"][1], 3),
        fmt(disc["z"][1] - disc["z"][0]), fmt(disc["dmaxr"])))
    a("| `%s` | hubcap disc | Ø %s (see the rim measure above) |" % (fan["bone"], fmt(2 * fan["maxr"])))
    a("")
    a("The Disc overlaps the tyre across its whole width: the tyre spans x %s…%s and the Disc" % (
        fmt(m0["x"][0], 3), fmt(m0["x"][1], 3)))
    a("%s…%s, so only its inner end (%s) is %s m inboard of the tyre's inner face — it is not" % (
        fmt(disc["x"][0], 3), fmt(disc["x"][1], 3), fmt(disc["x"][1], 3),
        fmt(disc["x"][1] - m0["x"][1], 3)))
    a("an inboard-only structure (`*_Disc` owns the brake and the strut inside the tyre too).")
    a("")
    a("More than three bones own faces in the wheel volume. Faces whose three vertices lie inside")
    a("the tyre's bounding box (x %s…%s, y 0…2.0, z %s…%s):" % (
        fmt(lo[0], 3), fmt(hi[0], 3), fmt(lo[2], 3), fmt(hi[2], 3)))
    a("")
    a("| bone | faces inside that box |")
    a("|---|---|")
    for name, n in bones:
        a("| `%s` | %s |" % (name, N(n)))
    a("")
    a("Only `Wheel_*_Vis` is the tyre; the diameters above use it alone.")
    a("")
    a("#### `Disc` vertices outside the tyre envelope (both tests, named)")
    a("")
    a("| corner | radial: √((y−hub)²+(z−hub)²) > tyre max radial | vertical: \\|y−hub\\| > station radius |")
    a("|---|---|---|")
    for m in ms:
        d = m["disc"]
        a("| %s | **%s** of %s — x %s…%s, z %s…%s | **%s** of %s — x %s…%s, z %s…%s |" % (
            m["corner"], N(d["beyond_radial"]), N(d["verts"]),
            fmt(d["beyond_radial_x"][0], 3), fmt(d["beyond_radial_x"][1], 3),
            fmt(d["beyond_radial_z"][0], 3), fmt(d["beyond_radial_z"][1], 3),
            N(d["beyond_vertical"]), N(d["verts"]),
            fmt(d["beyond_vertical_x"][0], 3), fmt(d["beyond_vertical_x"][1], 3),
            fmt(d["beyond_vertical_z"][0], 3), fmt(d["beyond_vertical_z"][1], 3)))
    a("")
    a("The two counts differ because they are different tests; the earlier pass printed the")
    a("vertical one (front-left %s) under the words \"beyond the tyre's radius\"." % (
        N(disc["beyond_vertical"])))
    a("")
    a("The front-left Disc's lowest vertex is y %s — **%s cm above the ground plane y = %s** —" % (
        fmt(disc["y"][0]), fmt(disc["gap"] * 100, 1), fmt(ground, 2)))
    a("and its top is %s cm above the tyre crown (y %s); its radial envelope reaches Ø %s." % (
        fmt((disc["y"][1] - m0["y"][1]) * 100, 1), fmt(m0["y"][1]), fmt(disc["dmaxr"])))
    a("")
    a("## 2. The three numbers")
    a("")
    a("| number | what it actually is | source |")
    a("|---|---|---|")
    t6 = (doc["t6_cells"][5].replace("`", "").replace("**", "")
          if doc["t6_cells"] else "UNKNOWN")
    a("| **1.366** | **tread-to-tread through the hub, and 2 × the physics radius** — the same "
      "number by design | this page: tread Ø %s–%s = 2 × `stations.json` `radius` %s–%s "
      "(≤ %s mm, above) = T-G2's `land_global.*_wheels.radius` %s / %s, which T-G6 keeps as "
      "the JC3 contact radius (its cell: %s) |" % (
          fmt(min(dy)), fmt(max(dy)), fmt(min(m["station_r"] for m in ms)),
          fmt(max(m["station_r"] for m in ms)), fmt(rd_gap * 1000, 1),
          doc["t2_radii"][0], doc["t2_radii"][1], t6))
    a("| **1.40** | the **lore reference** — neither mesh nor physics | 4 ft 7 in = 1.397 m "
      "wiki estimate, user-verified against footage with Batman at 188 cm (MODLOG §70) |")
    a("| **1.42** | **no source in the repo** — the initial-commit `bat_assemble.py` "
      "docstring figure | written in `7a0a07d`; `git log -S \"1.42 m\"` returns no other commit "
      "and no file measures 1.42. What the docstring measured is **UNKNOWN** (§3 prints the "
      "quantities near it) |")
    a("")
    a("T-G2 does **not** carry a rear-tyre figure: its cells are \"%s\", \"%s\", decoded, \"%s\"." % (
        t2[1], t2[2], t2[4]))
    a("No repo file records a rear diameter different from the front, and all four tyres measure")
    a("1.3652–1.3657 — a separate rear figure was in the earlier version of this page and is gone.")
    a("")
    a("### The sidewall question D-1 asked")
    a("")
    a("D-1: keep the PSKX true scale \"unless G1-18 shows the 1.366 excludes the sidewall bulge\".")
    a("It does exclude the bulge, and the bulge is small:")
    a("")
    a("| corner | tread Ø (y) | Ø max radial (shoulder) | bulge |")
    a("|---|---|---|---|")
    for m, b in zip(ms, bulge):
        a("| %s | %s | %s | %s mm |" % (m["corner"], fmt(m["dy"]), fmt(m["dmaxr"]),
                                        fmt(b * 1000, 1)))
    a("")
    a("Per corner the shoulder adds **%s–%s mm** on its own tread; against the four-corner mean" % (
        fmt(min(bulge) * 1000, 1), fmt(max(bulge) * 1000, 1)))
    a("tread Ø %s the largest shoulder is %s mm higher. Reaching 1.40 from the shoulder (Ø %s)" % (
        fmt(dy_mean), fmt(bulge_mean * 1000, 1), fmt(max(sh))))
    a(("needs ×%s (+%s%%); from the tread (Ø %s) it needs ×%s (+%s%%) — %s m, i.e. %s mm of "
       "rubber that is not in the mesh.") % (
          fmt(ratio_sh, 3), fmt(pct_sh, 1), fmt(dy_mean), fmt(ratio_tread, 3), fmt(pct_tread, 1),
          fmt(need, 4), fmt(need * 1000, 1)))
    a("Ø including the shoulder = **%s**, still %s%% short of 1.40 on that basis. None of the" % (
        fmt(max(sh)), fmt(pct_sh, 1)))
    a("three headline numbers is \"the bulge number\" — that number is %s." % fmt(max(sh)))
    a("")
    a("## 3. What 1.42 might have measured — UNKNOWN")
    a("")
    a("The quantities near 1.42 in the wheel volume, all measured here:")
    a("")
    a("| quantity | value (m) |")
    a("|---|---|")
    a("| front-left `Disc` vertical extent | %s (%s…%s) |" % (
        fmt(disc["y"][1] - disc["y"][0]), fmt(disc["y"][0], 3), fmt(disc["y"][1], 3)))
    a("| box over tyre + Disc + Fan: vertical extent | %s |" % fmt(union_y))
    a("| box over tyre + Disc + Fan: max radial Ø | %s |" % fmt(2 * union_r))
    a("| tyre tread Ø | %s (%s…%s) |" % (fmt(dy_mean), fmt(min(dy)), fmt(max(dy))))
    a("")
    a("A bounding box taken over \"the wheel\" rather than over the tyre reads Ø%s radial / %s" % (
        fmt(2 * union_r), fmt(union_y)))
    a("vertical, not 1.42 of rubber. Which of these — if either — the 1.42 in the initial")
    a("docstring measured is **UNKNOWN**: no file records the method, and `git log -S` only shows")
    a("when the string entered the history.")
    a("")
    a("## 4. Physics chain — what the diameter is used for")
    a("")
    a("| value | radius (m) | Ø (m) | source | used? |")
    a("|---|---|---|---|---|")
    a("| mesh / JC3 contact | %s | %s–%s | `stations.json` = T-G2 "
      "`land_global.*_wheels.radius` %s / %s, mesh bounds verified against it | **yes** — "
      "T-G6 keeps it: the JC3 radius sets contact and ride height |" % (
          " · ".join(fmt(m["station_r"]) for m in ms), fmt(min(dy)), fmt(max(dy)),
          doc["t2_radii"][0], doc["t2_radii"][1]))
    a(("| BmAK `SVehicleWheel.WheelRadius` | %s | %s | `CHAIN.json` (offset 568, %s cm) | "
       "**no** — a contact-radius simplification inside the %s m visual tyre (T-G6); not "
       "imported |") % (
          fmt(doc["wheel_radius_m"], 3), fmt(2 * doc["wheel_radius_m"], 3),
          fmt(doc["wheel_radius_m"] * 100, 1), fmt(dy_mean, 3)))
    a("| lore wiki | 0.699 | 1.397 (≈1.40) | MODLOG §70 | reference only |")
    a("")
    a("`front/rear_wheels.radius` therefore stays **%s / %s** and the wheel RBMs stay at" % (
        doc["t2_radii"][0], doc["t2_radii"][1]))
    a("true scale.")
    a("")
    a("## 5. Decision D-1 — resolved: keep the PSKX true scale")
    a("")
    a("**No rescale of the car.** The measurement closes D-1's condition:")
    a("")
    a(("1. the tyre reads Ø%s–%s tread-to-tread and Ø%s–%s including the shoulder — the "
       "bulge is %s–%s mm, far short of the %s mm needed to reach 1.40;") % (
          fmt(min(dy)), fmt(max(dy)), fmt(min(sh)), fmt(max(sh)),
          fmt(min(bulge) * 1000, 1), fmt(max(bulge) * 1000, 1), fmt(need * 1000, 1)))
    a("2. 1.42 has no source in the repo, and what the initial docstring measured is UNKNOWN;")
    a("3. T-G6 already keeps the mesh radius as the JC3 physics radius, so ride height, contact and")
    a("   track are unchanged; the whole car would move together through the one transform (R2) if")
    a("   it ever were rescaled.")
    a("")
    a("DIM-2 (\"tyre diameter matches the lore reference\") is satisfied as **%s measured vs 1.40" % fmt(dy_mean, 3))
    a("reference, %s%% apart, accepted**: the mesh is the physics source and the wiki number is" % fmt(pct_tread, 1))
    a("an estimate. Nothing in the repo is edited to make the tyre read 1.40.")
    a("")
    a("## 6. How to re-measure")
    a("")
    a("```")
    a("python Tools/scripts/bmak_tyres.py --check")
    a("```")
    a("")
    a("It re-reads the PSKX, `stations.json`, T-G2/T-G6 and `CHAIN.json`, re-derives every table")
    a("above and fails if this page differs from the render or an invariant breaks (four corners,")
    a("tread spread ≤ 0.6 mm, each tread Ø = 2 × station radius within 1.5 mm, tread on the ground")
    a("within 0.4 cm).")
    a("")
    return "\n".join(L) + "\n"


def invariants(doc):
    ms = doc["corners"]
    fail = []
    if len(ms) != 4:
        fail.append("expected 4 corners, measured %d" % len(ms))
    dy = [m["dy"] for m in ms]
    if max(dy) - min(dy) > 0.0006:
        fail.append("tread spread %.4f m > 0.6 mm" % (max(dy) - min(dy)))
    for m in ms:
        if abs(m["dy"] - 2 * m["station_r"]) > 0.0015:
            fail.append("%s: tread Ø %.4f vs 2 x station radius %.4f" % (
                m["corner"], m["dy"], 2 * m["station_r"]))
        if not (-0.001 <= m["gap"] <= 0.004):
            fail.append("%s: tread bottom - ground %+.4f m out of range" % (m["corner"], m["gap"]))
        if m["faces"] <= 0 or m["verts"] <= 0:
            fail.append("%s: tyre bone owns no faces" % m["corner"])
    return fail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = render(doc)
    ms = doc["corners"]
    dy = [m["dy"] for m in ms]
    sh = [m["dmaxr"] for m in ms]
    wd = [m["w"] for m in ms]
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8").write(text)
        print("wrote", os.path.relpath(MD, ROOT), "(%d lines)" % text.count("\n"))
    if a.check:
        fail = invariants(doc)
        disk = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        if not disk:
            fail.append("TYRES.md is missing")
        elif disk != text:
            import difflib
            diff = [l for l in difflib.unified_diff(disk.splitlines(), text.splitlines(),
                                                    "on disk", "re-derived", lineterm="")
                    if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            fail.append("TYRES.md differs from the render (%d changed lines; first: %s)"
                        % (len(diff), diff[0][:120] if diff else "?"))
        for bad in ("1.369", "4.8 cm"):
            if bad in text:
                fail.append("the removed claim %r is back in the render" % bad)
        if "UNKNOWN" not in text:
            fail.append("the UNKNOWN rows are missing")
        if fail:
            print("FAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("OK: 4 tyres; tread Ø %.4f-%.4f, shoulder Ø %.4f-%.4f, width %.4f-%.4f; "
              "station radius vs mesh <= %.1f mm" % (
                  min(dy), max(dy), min(sh), max(sh), min(wd), max(wd),
                  max(abs(m["dy"] - 2 * m["station_r"]) for m in ms) * 1000))
        print("OK: TYRES.md matches the re-derived render (%d lines)" % text.count("\n"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
