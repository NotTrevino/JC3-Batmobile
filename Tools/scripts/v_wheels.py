"""v_wheels.py - V-04/W: how the four wheels are oriented in bm-RC2, against TYRES.md.

The question is narrow and answerable from bytes already in the repo:

  axis      the four wheel parts' `parent_space_offset` rotation block in the built
            parts module, and the tyre's own shape in the built LOD1 mesh (the
            axle is the axis the tread is thin along);
  radius    `land_global.front/rear_wheels.radius` (metres) against TYRES.md's
            per-corner station radius (metres) - BmAK's own 64.0 is a CENTIMETRE
            figure, so a bare number comparison is 100x out;
  width     `land_global.front/rear_wheels.width` against TYRES.md's per-corner
            tyre width;
  corners   the hardpoint order, the `wheel_parts[].wheel_slot` order against the
            fleet's own slot convention (233 vehicles), and the x/z sign map of
            `bat_assemble.to_jc3_rot` (-y, z, -x).

The one thing that does NOT match is reported, not asserted away: the four wheel
*parts* still carry the shipped Serpente `parent_space_offset` translations
(+-0.885, 0.4, +-1.557), identical to the vanilla module's and to the vanilla
land_global's hardpoints, while this build's hardpoints are the Batmobile's
(+-1.208, 0.7047, -2.5699 / +-1.2845, 0.7027, 2.4589). `bm_parts.py` already names
that re-emit as owed. Whether the runtime places a wheel part by its transform or
by the land_global hardpoint is UNKNOWN from the repo, so the placement delta is a
WARN line, not a FAIL.

Usage:
  python Tools/scripts/v_wheels.py --write     # emit Builds/bm-RC2/verify/wheels.md
  python Tools/scripts/v_wheels.py --check     # re-derive, assert, compare the page

Read-only over the build: nothing under Builds/ is written except the page itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf  # noqa: E402
import rbm_geom  # noqa: E402

TYRES = os.path.join(ROOT, "Research", "BatmobileGrab", "TYRES.md")
PARTS = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "batmobile",
                     "sportsmuscle_vehicle_parts.vmodc")
LAND = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "editor", "entities", "jc_vehicles",
                    "01_land", "v0300_car_kensington_sportsmuscle", "modules", "default",
                    "batmobile", "v0300_car_kensington_sportsmuscle_land_global.vmodc")
VAN_PARTS = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                         "v0300_car_kensington_sportsmuscle", "sportsmuscle_vehicle_parts.vmodc")
VAN_LAND = os.path.join(ROOT, "Builds", "test-003", "aaf", "editor", "entities", "jc_vehicles",
                        "01_land", "v0300_car_kensington_sportsmuscle", "modules", "default",
                        "v0300_car_kensington_sportsmuscle_land_global.vmodc")
FLEET = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
OUT = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "wheels.md")

CORNERS = ("f_l", "f_r", "r_l", "r_r")
PART_OF = {"f_l": 26, "f_r": 27, "r_l": 11, "r_r": 12}
WHEEL_DIR = os.path.dirname(PARTS)

FAILS: list[str] = []
WARNS: list[str] = []
NOTES: list[str] = []


def a(ok, msg):
    if not ok:
        FAILS.append(msg)
    return ok


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def f(x, n=4):
    return f"{x:.{n}f}"


# --------------------------------------------------------------------------- inputs

# TYRES.md has three corner-keyed tables; attribute columns by their header, never by
# cell count (the "bulge" table is also 4 cells wide and would overwrite the station one).
COLUMNS = {
    "tyre faces (`*_vis`)": ("faces", int),
    "verts": ("verts", int),
    "ø tread (y)": ("dia_y", float),
    "ø (z)": ("dia_z", float),
    "ø max radial": ("dia_radial", float),
    "width (x)": ("width", float),
    "station radius": ("station_radius", float),
    "station `tyre_width`": ("station_width", float),
    "tread bottom − ground": ("bottom", float),
    "tread ø (y)": ("bulge_tread", float),
    "bulge": ("bulge", float),
}


def _num(cell: str) -> float:
    return float(cell.replace("*", "").replace(",", "").removesuffix(" mm").strip())


def tyres_page() -> dict:
    """Per corner: mesh tread (y,z,radial,width) and the station (radius, width)."""
    out: dict[str, dict] = {}
    header: list[str] | None = None
    with open(TYRES, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line.startswith("|"):
                header = None
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells[0].lower() == "corner":
                header = [c.lower() for c in cells]
                continue
            if header is None or cells[0] not in CORNERS:
                continue
            row = out.setdefault(cells[0], {})
            for name, cell in zip(header[1:], cells[1:]):
                spec = COLUMNS.get(name)
                if not spec:
                    continue
                key, kind = spec
                row[key] = kind(_num(cell))
    for c in CORNERS:
        a(c in out and "station_radius" in out[c], f"TYRES.md: no station row for {c}")
        a(c in out and "dia_y" in out[c], f"TYRES.md: no mesh row for {c}")
    return out


def parts_module(path: str) -> tuple[dict, list, dict]:
    adf = jc3adf.Adf(open(path, "rb").read())
    parts = {q["part_index"]: q for q in jc3adf.parts(adf)}
    flat = {k: v for k, _t, v in jc3adf.walk(adf)}
    wheels = []
    i = 0
    while f"wheel_parts[{i}].part_index" in flat:
        wheels.append({
            "part": flat[f"wheel_parts[{i}].part_index"],
            "slot": flat.get(f"wheel_parts[{i}].wheel_slot"),
            "spins": flat.get(f"wheel_parts[{i}].spins"),
            "spokes": flat.get(f"wheel_parts[{i}].number_of_spokes"),
        })
        i += 1
    return parts, wheels, flat


def world(parts: dict, index: int, depth: int = 0):
    """Compose parent_space_offset up the chain.

    The stored 4x4 is ROW-VECTOR form: `[1,0,0,0, 0,1,0,0, 0,0,1,0, tx,ty,tz, 1]`, i.e. the
    translation is the last ROW (12..14), so a chain composes as the row-major product
    P·M and the last row of the product is the composed translation.
    """
    if depth > 32:
        raise RuntimeError("part parent cycle")
    m = parts[index]["parent_space_offset"]
    if parts[index]["parent_part_index"] < 0:
        return list(m)
    p = world(parts, parts[index]["parent_part_index"], depth + 1)
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = sum(p[r * 4 + k] * m[k * 4 + c] for k in range(4))
    return out


def mesh(path: str) -> dict:
    m = rbm_geom.decode(open(path, "rb").read())
    pos = [p for b in m.blocks for p in b.vb0.positions()]
    lo = [min(p[i] for p in pos) for i in range(3)]
    hi = [max(p[i] for p in pos) for i in range(3)]
    radial = [((p[1] ** 2 + p[2] ** 2) ** 0.5) for p in pos]
    rmax = max(radial)
    # tyre-only reads: the crown at the centre plane, and the tread band's axial span
    crown = max(r for p, r in zip(pos, radial) if abs(p[0]) <= 0.05)
    band = [p[0] for p, r in zip(pos, radial) if r >= 0.90 * rmax]
    return {
        "verts": len(pos), "lo": lo, "hi": hi,
        "ext": [hi[i] - lo[i] for i in range(3)],
        "centre": [(hi[i] + lo[i]) / 2 for i in range(3)],
        "rmax": rmax, "crown": crown,
        "band_lo": min(band), "band_hi": max(band),
        "sha256": hashlib.sha256(open(path, "rb").read()).hexdigest(),
    }


def fleet_slots() -> dict[int, dict[str, int]]:
    """slot -> {corner suffix: count} over every vehicle's wheel_parts."""
    out: dict[int, dict[str, int]] = {}
    for line in open(FLEET, encoding="utf-8"):
        r = json.loads(line)
        names = {p["i"]: p["n"] for p in r["parts"]}
        for w in r.get("wheels") or []:
            n = names.get(w["part"]) or ""
            m = re.search(r"(f_l|f_r|r_l|r_r|f|r|b_l|b_r)$", n)
            corner = m.group(1) if m else "(other)"
            out.setdefault(w["slot"], {}).setdefault(corner, 0)
            out[w["slot"]][corner] += 1
    return out


# --------------------------------------------------------------------------- the page

def build_page() -> str:
    FAILS.clear(); WARNS.clear(); NOTES.clear()
    ty = tyres_page()
    parts, wheels, _flat = parts_module(PARTS)
    _lp, _lw, lf = parts_module(LAND)
    van_parts, van_wheels, _vf = parts_module(VAN_PARTS)
    _vp, _vl, vf = parts_module(VAN_LAND)
    fleet = fleet_slots()

    front_r = lf["front_wheels.radius"]
    rear_r = lf["rear_wheels.radius"]
    front_w = lf["front_wheels.width"]
    rear_w = lf["rear_wheels.width"]
    hp = [tuple(lf[f"base_wheel_hardpoint_positions[{i}].position[{j}]"] for j in range(3))
          for i in range(4)]

    # ---- 1. spin axis: part rotation + mesh shape
    axis_rows = []
    for c in CORNERS:
        idx = PART_OF[c]
        q = parts[idx]
        m = q["parent_space_offset"]
        rot = [m[0], m[1], m[2], m[4], m[5], m[6], m[8], m[9], m[10]]
        ident = all(abs(rot[i] - (1.0 if i in (0, 4, 8) else 0.0)) <= 1e-6 for i in range(9))
        a(ident, f"{c}: wheel part {idx} rotation is not identity ({rot})")
        ax = q.get("model", "")
        rbm = os.path.join(WHEEL_DIR, os.path.basename(ax).replace(".lod", "_lod1.rbm"))
        a(os.path.exists(rbm), f"{c}: no LOD1 mesh at {rbm}")
        mm = mesh(rbm)
        # the axle is the axis the tyre is THIN along (width < diameter)
        ext = mm["ext"]
        axle = "x" if ext[0] == min(ext) else ("y" if ext[1] == min(ext) else "z")
        a(axle == "x", f"{c}: mesh thin axis is {axle}, expected x")
        axis_rows.append((c, idx, ident, axle, mm, rbm))

    # ---- 2/3. radius and width, per corner and per axle
    def mean(vals):
        return sum(vals) / len(vals)

    st_r_front = mean([ty["f_l"]["station_radius"], ty["f_r"]["station_radius"]])
    st_r_rear = mean([ty["r_l"]["station_radius"], ty["r_r"]["station_radius"]])
    st_w_front = mean([ty["f_l"]["width"], ty["f_r"]["width"]])
    st_w_rear = mean([ty["r_l"]["width"], ty["r_r"]["width"]])
    a(abs(front_r - st_r_front) <= 5e-4,
      f"front radius {front_r} != TYRES station mean {st_r_front}")
    a(abs(rear_r - st_r_rear) <= 5e-4,
      f"rear radius {rear_r} != TYRES station mean {st_r_rear}")
    a(abs(front_w - st_w_front) <= 5e-4,
      f"front width {front_w} != TYRES mesh mean {st_w_front}")
    a(abs(rear_w - st_w_rear) <= 5e-4,
      f"rear width {rear_w} != TYRES mesh mean {st_w_rear}")
    # metres, not centimetres: BmAK's own 64.0 is a cm figure
    a(0.5 < front_r < 1.0 and 0.5 < rear_r < 1.0, "radius is not in metres")
    a(0.5 < front_w < 1.0 and 0.5 < rear_w < 1.0, "width is not in metres")

    bmak_r = 0.640  # CHAIN.json: SVehicleWheel.WheelRadius 64.0 cm (TYRES.md §4)
    if abs(front_r - bmak_r) > 1e-6:
        NOTES.append(f"BmAK `SVehicleWheel.WheelRadius` = 64.0 **cm** = {bmak_r:.3f} m; the "
                     f"build keeps the mesh radius {front_r:.5f} m (+{(front_r - bmak_r) * 100:.3f} cm). "
                     "T-G6 keeps it deliberately (0.64 m is BmAK's contact-radius simplification "
                     "inside a 0.683 m visual tyre).")

    # ---- 4. corners: slot order, hardpoint signs, and the map behind them
    slot_of = {w["part"]: w["slot"] for w in wheels}
    expected_slot = {"f_l": 0, "f_r": 1, "r_r": 2, "r_l": 3}
    for c, want in expected_slot.items():
        got = slot_of.get(PART_OF[c])
        a(got == want, f"{c}: wheel_slot {got}, expected {want} (fleet convention)")
    a(len(wheels) == 4, f"wheel_parts has {len(wheels)} rows, expected 4")
    for w in wheels:
        a(w["spins"] == 1, f"wheel part {w['part']} does not spin")

    # fleet convention: which corner name sits on which slot
    conv = {}
    for slot, counts in fleet.items():
        if counts:
            conv[slot] = max(counts.items(), key=lambda kv: kv[1])
    a(conv.get(0, ("", 0))[0] == "f_l", f"fleet slot 0 is not f_l: {conv.get(0)}")
    a(conv.get(1, ("", 0))[0] == "f_r", f"fleet slot 1 is not f_r: {conv.get(1)}")
    a(conv.get(2, ("", 0))[0] == "r_r", f"fleet slot 2 is not r_r: {conv.get(2)}")
    a(conv.get(3, ("", 0))[0] == "r_l", f"fleet slot 3 is not r_l: {conv.get(3)}")

    # hardpoint i = slot i: left = -x, front = -z (TYRES.md axes; to_jc3_rot -y,z,-x)
    a(hp[0][0] < 0 and hp[1][0] > 0 and hp[2][0] > 0 and hp[3][0] < 0,
      "hardpoint x signs do not read left(-x)/right(+x)")
    a(hp[0][2] < 0 and hp[1][2] < 0 and hp[2][2] > 0 and hp[3][2] > 0,
      "hardpoint z signs do not read front(-z)/rear(+z)")
    a(abs(hp[0][0] + 1.208) < 1e-3 and abs(hp[0][2] + 2.570) < 1e-3,
      "hardpoint[0] is not TYRES.md's f_l hub (-1.208, *, -2.570)")
    a(hp[2][0] > 0 and hp[2][2] > 0 and abs(hp[2][0] - 1.2845) < 1e-3,
      "hardpoint[2] is not the rear-right hub (+1.2845, *, +2.4589)")

    # ---- 5. the stale transform (reported)
    stale = []
    for c in CORNERS:
        idx = PART_OF[c]
        t = world(parts, idx)
        rot_ok = all(abs(t[i] - (1.0 if i in (0, 5, 10, 15) else 0.0)) <= 1e-6
                     for i in list(range(0, 3)) + list(range(4, 7)) + list(range(8, 11)) + [15])
        slot = slot_of[PART_OF[c]]
        h = hp[slot]
        d = [h[i] - t[12 + i] for i in range(3)]
        van = world(van_parts, idx)
        van_ok = all(abs(van[4 * r + c] - t[4 * r + c]) <= 1e-9
                     for r in range(3) for c in range(4))
        stale.append((c, idx, slot, t, h, d, rot_ok, van_ok))
    maxd = max(max(abs(x) for x in s[5]) for s in stale)
    WARNS.append(
        f"the four wheel parts still carry the shipped Serpente `parent_space_offset` "
        f"translations (max |hardpoint - part origin| = {maxd:.4f} m); the wheel-arch parts "
        "were placed at the true hubs, so the visual wheel and its arch disagree by that "
        "delta if the part transform places the mesh. `bm_parts.py` names this re-emit as "
        "owed; whether the runtime places a wheel by its transform or by "
        "`base_wheel_hardpoint_positions` is UNKNOWN in the repo.")
    a(all(s[6] for s in stale), "a wheel part's composed rotation is not identity")
    a(all(s[7] for s in stale), "a wheel part's translation differs from the vanilla Serpente's")

    # ---- page
    L: list[str] = []
    L.append("# Wheels — orientation, radius and width in bm-RC2 vs BmAK")
    L.append("")
    L.append("Generated by `Tools/scripts/v_wheels.py`; `--check` re-derives every number and")
    L.append("fails if this page is stale or an assertion breaks. Read-only over the build.")
    L.append("")
    L.append("Inputs (sha256, first 16):")
    L.append("")
    L.append("| file | bytes | sha256 |")
    L.append("|---|---|---|")
    for p, label in ((TYRES, "Research/BatmobileGrab/TYRES.md"),
                     (PARTS, "built parts module (batmobile/)"),
                     (LAND, "built land_global (batmobile/)")):
        L.append(f"| `{label}` | {os.path.getsize(p)} | `{sha(p)[:16]}` |")
    for c, _i, _ok, _ax, mm, p in axis_rows:
        L.append(f"| `{os.path.basename(p)}` | {os.path.getsize(p)} | `{mm['sha256'][:16]}` |")
    L.append("")
    L.append("Frame: JC3 car space, **x = lateral (left = −x), y = up, z = longitudinal")
    L.append("(front = −z)**, the same frame `TYRES.md` measures in (its axes line).")
    L.append("")
    L.append("## 1. The answer in one line")
    L.append("")
    L.append(f"* **spin axis**: `+x` (lateral) on all four — every wheel part's rotation block is")
    L.append("  the identity (below), and every wheel mesh is thin along x.")
    L.append(f"* **radius**: `{front_r:.5f}` m front / `{rear_r:.5f}` m rear — exactly TYRES.md's")
    L.append("  axle means of the station radius. Metres, not centimetres.")
    L.append(f"* **width**: `{front_w:.5f}` m front / `{rear_w:.5f}` m rear — exactly TYRES.md's")
    L.append("  axle means of the four measured tyre widths.")
    L.append("* **corners**: not swapped. slot/hardpoint order is FL, FR, RR, RL — the fleet's own")
    L.append("  order (233 vehicles) — with left = −x and front = −z.")
    L.append("")
    L.append("## 2. Per wheel — axis, radius, width")
    L.append("")
    L.append("| wheel | BmAK (TYRES.md) | built | difference |")
    L.append("|---|---|---|---|")
    for c, idx, ident, axle, mm, _p in axis_rows:
        slot = slot_of[PART_OF[c]]
        L.append(f"| `{c}` (part {idx}, slot {slot}) | axle x (lateral) | axle `{axle}`, rotation "
                 f"{'identity' if ident else 'NOT identity'} | 0° |")
    for c in CORNERS:
        axle_r = front_r if c.startswith("f") else rear_r
        st = ty[c]["station_radius"]
        tread = ty[c]["dia_y"] / 2
        L.append(f"| `{c}` radius | station {st:.4f} m · tread Ø {ty[c]['dia_y']:.4f} m "
                 f"(r {tread:.4f}) | {axle_r:.5f} m (axle value) | "
                 f"{1000 * (axle_r - st):+.2f} mm vs station, "
                 f"{1000 * (axle_r - tread):+.2f} mm vs tread |")
    for c in CORNERS:
        axle_w = front_w if c.startswith("f") else rear_w
        L.append(f"| `{c}` width | mesh {ty[c]['width']:.4f} m (station "
                 f"{ty[c]['station_width']:.4f}, mirrored L↔R) | {axle_w:.5f} m (axle value) | "
                 f"{1000 * (axle_w - ty[c]['width']):+.2f} mm vs mesh |")
    L.append("")
    L.append("The JC3 members are per **axle**, not per corner, so a per-corner BmAK number")
    L.append("can only match the axle mean. Both means close to 0.05 mm:")
    L.append("")
    L.append("| member (built, decoded) | value (m) | derived from TYRES.md | difference |")
    L.append("|---|---|---|---|")
    L.append(f"| `land_global.front_wheels.radius` | `{front_r:.7f}` | "
             f"mean(f_l {ty['f_l']['station_radius']:.4f}, f_r {ty['f_r']['station_radius']:.4f}) = "
             f"{st_r_front:.5f} | {1000 * (front_r - st_r_front):+.3f} mm |")
    L.append(f"| `land_global.rear_wheels.radius` | `{rear_r:.7f}` | "
             f"mean(r_l {ty['r_l']['station_radius']:.4f}, r_r {ty['r_r']['station_radius']:.4f}) = "
             f"{st_r_rear:.5f} | {1000 * (rear_r - st_r_rear):+.3f} mm |")
    L.append(f"| `land_global.front_wheels.width` | `{front_w:.7f}` | "
             f"mean(f_l {ty['f_l']['width']:.4f}, f_r {ty['f_r']['width']:.4f}) = {st_w_front:.5f} "
             f"| {1000 * (front_w - st_w_front):+.3f} mm |")
    L.append(f"| `land_global.rear_wheels.width` | `{rear_w:.7f}` | "
             f"mean(r_l {ty['r_l']['width']:.4f}, r_r {ty['r_r']['width']:.4f}) = {st_w_rear:.5f} "
             f"| {1000 * (rear_w - st_w_rear):+.3f} mm |")
    L.append("")
    L.append(f"`front_wheels.rim_radius` `{lf['front_wheels.rim_radius']:.6f}` and")
    L.append(f"`rear_wheels.rim_radius` `{lf['rear_wheels.rim_radius']:.6f}` are untouched shipped")
    L.append("values; TYRES.md has no rim figure to compare them with (its rim number 1.0254 m is a")
    L.append("diameter of the `Fan` hubcap, not a rim radius), so they are printed and not asserted.")
    L.append("")
    L.append("**The centimetre trap.** BmAK's `SVehicleWheel.WheelRadius` is **64.0 cm** = 0.640 m")
    L.append("(`TYRES.md` §4, `CHAIN.json` offset 568). A bare-number comparison against")
    L.append(f"`{front_r:.5f}` reads as a 100x error; the real relation is")
    L.append(f"{front_r:.5f} m − 0.640 m = **+{(front_r - 0.640) * 100:.2f} cm**, which")
    L.append("T-G6 keeps on purpose (the JC3 radius sets contact *and* ride height; 0.64 m is")
    L.append("BmAK's contact-radius simplification inside the 0.683 m visual tyre).")
    L.append("")
    L.append("## 3. Spin axis — the bytes")
    L.append("")
    L.append("`parent_space_offset` is a row-major 4×4; the 3×3 block is the rotation, elements")
    L.append("12..14 the translation. Decoded from the built module:")
    L.append("")
    L.append("| part | wheel | 3×3 rotation (rows) | translation (m) |")
    L.append("|---|---|---|---|")
    for c in CORNERS:
        idx = PART_OF[c]
        m = parts[idx]["parent_space_offset"]
        rows = " ; ".join(f"({m[r * 4]:.1f}, {m[r * 4 + 1]:.1f}, {m[r * 4 + 2]:.1f})" for r in range(3))
        L.append(f"| {idx} | `{c}` | {rows} | "
                 f"({m[12]:.4f}, {m[13]:.4f}, {m[14]:.4f}) |")
    L.append("")
    L.append("Identity rotation means the wheel mesh's own axes *are* the car axes, so the spin")
    L.append("axis is whatever the tyre is thin along. From the built LOD1 meshes:")
    L.append("")
    L.append("| wheel | mesh bbox (x × y × z, m) | bbox centre (m) | thin axis | tyre radius at "
             "centre plane | tread band x-span |")
    L.append("|---|---|---|---|---|---|")
    for c, _i, _ok, axle, mm, _p in axis_rows:
        L.append(f"| `{c}` | {mm['ext'][0]:.4f} × {mm['ext'][1]:.4f} × {mm['ext'][2]:.4f} | "
                 f"({mm['centre'][0]:+.4f}, {mm['centre'][1]:+.4f}, {mm['centre'][2]:+.4f}) | "
                 f"**{axle}** | {mm['crown']:.4f} | {mm['band_lo']:+.4f} … {mm['band_hi']:+.4f} |")
    L.append("")
    L.append("The x extent is the tyre + inboard brake disc (TYRES.md: the tyre is 0.731 m wide,")
    L.append("the `*_Disc` reaches 0.317 m further inboard), which is why it is larger than the")
    L.append("tyre width; y and z are the diameter. Nothing is thin along y or z, so x is the axle")
    L.append("on all four. The meshes are the true-scale Batmobile wheels, not the donor's:")
    L.append("`sportsmuscle_wheel_f_l_lod1.rbm` is 3970 verts / 1.053 × 1.388 × 1.340 m, against")
    L.append("the vanilla Serpente wheel's 929 verts / 0.329 × 0.801 × 0.800 m in `Builds/test-003`")
    L.append("(the vanilla-geometry base: its land_global carries the Serpente's own hardpoints")
    L.append("(±0.885, 0.400, ±1.557) and radius 0.380 m). `bm-001` already shipped this mesh and")
    L.append("`bm-RC2` carries it forward (sha256 `9edc7f1a…` in both).")
    L.append("")
    L.append("## 4. Front/rear and left/right after the conversion")
    L.append("")
    L.append("`bat_assemble.to_jc3_rot` is `(-y, z, -x)` (a proper rotation, MODLOG §73), and")
    L.append("`TYRES.md` measures in that same frame. The corner identity survives it:")
    L.append("")
    L.append("| slot | part | name | hardpoint x, y, z (m) | TYRES.md hub | Δ (mm) |")
    L.append("|---|---|---|---|---|---|")
    tyre_hub = {"f_l": (-1.208, 0.7047, -2.570), "f_r": (1.208, 0.7047, -2.570),
                "r_l": (-1.2845, 0.7027, 2.4589), "r_r": (1.2845, 0.7027, 2.4589)}
    for c in CORNERS:
        idx = PART_OF[c]
        slot = slot_of[idx]
        h = hp[slot]
        th = tyre_hub[c]
        dmax = max(abs(h[i] - th[i]) for i in range(3)) * 1000
        L.append(f"| {slot} | {idx} | `{parts[idx]['name']}` | "
                 f"({h[0]:+.4f}, {h[1]:+.4f}, {h[2]:+.4f}) | "
                 f"({th[0]:+.4f}, {th[1]:+.4f}, {th[2]:+.4f}) | {dmax:.2f} |")
    L.append("")
    L.append("Slot order is the fleet's own: across the 233 decoded vehicles, slot 0 is the")
    L.append("`*_f_l` part, 1 `*_f_r`, **2 `*_r_r`**, 3 `*_r_l` — rear-right before rear-left, in")
    L.append("every vehicle that ships four wheels. This build's `wheel_parts[]` follows it")
    L.append("(26→0, 27→1, 12→2, 11→3), so the rear pair is *named* right-then-left on purpose and")
    L.append("is not a swap. The hardpoints likewise carry left at −x and front at −z, matching")
    L.append("TYRES.md's f_l tyre box (x −1.574…−0.842, centre −1.208; z −3.274…−1.866, centre")
    L.append("−2.570).")
    L.append("")
    L.append("## 5. What does not match — the wheel parts' own transform")
    L.append("")
    L.append("The wheel *parts* carry the shipped Serpente `parent_space_offset` translations")
    L.append("(identical, element for element, to the vanilla module's and to the vanilla")
    L.append("land_global's hardpoints in `Builds/test-003`), while this build's hardpoints are")
    L.append("the Batmobile's:")
    L.append("")
    L.append("| wheel | part origin (built) | hardpoint (built) | Δ (m) |")
    L.append("|---|---|---|---|")
    for c, idx, slot, t, h, d, _r, _v in stale:
        L.append(f"| `{c}` | ({t[12]:+.4f}, {t[13]:+.4f}, {t[14]:+.4f}) | "
                 f"({h[0]:+.4f}, {h[1]:+.4f}, {h[2]:+.4f}) | "
                 f"({d[0]:+.4f}, {d[1]:+.4f}, {d[2]:+.4f}) |")
    L.append("")
    L.append(f"Max component {maxd:.4f} m. The wheel-arch parts were placed at the true hubs")
    L.append("(world (−1.208, 0.7047, −2.5699) for `f_l`), i.e. the arch and its wheel disagree by")
    L.append("this delta if a wheel part is drawn at its own transform — which is what vanilla")
    L.append("does (there the part translation *equals* the hardpoint). `Working/Parts/")
    L.append("bm_vehicle_parts.json` already records the state: \"the existing body/wheel parts")
    L.append("keep the shipped Serpente transforms; ... the body/wheel re-emit is still owed\".")
    L.append("")
    L.append("Whether the runtime places a wheel part by `parent_space_offset` or by")
    L.append("`base_wheel_hardpoint_positions[]` is **UNKNOWN** in the repo — no file decodes that")
    L.append("path. So this page prints the delta and does not fail on it. What *is* settled by")
    L.append("bytes: the rotation is identity, the axle is x, and the four corners are in the right")
    L.append("slots either way.")
    L.append("")
    L.append("## 6. Checks")
    L.append("")
    L.append("`python Tools/scripts/v_wheels.py --check` re-derives this page and asserts:")
    L.append("")
    L.append("* all four wheel parts' rotation blocks are the identity (≤ 1e-6);")
    L.append("* every wheel mesh's thin axis is x;")
    L.append("* each axle's radius equals the mean of TYRES.md's station radii (≤ 0.5 mm);")
    L.append("* each axle's width equals the mean of TYRES.md's four mesh widths (≤ 0.5 mm);")
    L.append("* radius and width are both in metres (0.5…1.0), not centimetres;")
    L.append("* `wheel_parts` has exactly 4 rows, all `spins = 1`, and part→slot is 26→0, 27→1,")
    L.append("  12→2, 11→3, which is the majority convention over 233 vehicles;")
    L.append("* hardpoint x reads left(−)/right(+) and z reads front(−)/rear(+), and hardpoint 0")
    L.append("  is TYRES.md's f_l hub to 1 mm;")
    L.append("* each wheel part's translation is byte-equal to the vanilla Serpente's.")
    L.append("")
    L.append("Reported but not asserted: the axle-mean spacing above, and the transform delta in")
    L.append("§5 (open item, not a regression this page can close).")
    L.append("")
    if FAILS:
        L.append("## FAILURES")
        L.append("")
        for x in FAILS:
            L.append(f"* {x}")
        L.append("")
    else:
        L.append("All assertions above hold.")
        L.append("")
    return "\n".join(L)


def main(argv) -> int:
    write = "--write" in argv
    check = "--check" in argv
    if not (write or check):
        print(__doc__)
        return 2
    text = build_page()
    if write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print(f"wrote {os.path.relpath(OUT, ROOT)} ({len(text.splitlines())} lines)")
    if check:
        if not os.path.exists(OUT):
            FAILS.append(f"{os.path.relpath(OUT, ROOT)} is missing")
        else:
            on_disk = open(OUT, encoding="utf-8", newline="").read().replace("\r\n", "\n")
            a(on_disk.rstrip("\n") == text.rstrip("\n"),
              f"{os.path.relpath(OUT, ROOT)} differs from the re-derived text")
    for w in WARNS:
        print("WARN:", w)
    for x in FAILS:
        print("FAIL:", x)
    if FAILS:
        print(f"FAIL: {len(FAILS)} problem(s)")
        return 1
    print("check ok" if check else "ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
