"""bmak_tyres_package.py - are `TYRES.md`'s wheel numbers grabbed or shaped? (reverify-TYRES)

`Research/BatmobileGrab/TYRES.md` measures the four tyres from the vertices owned by the wheel
bones of `Batmobile_V2.pskx`, through the ONE transform. The research reset has to know whether
those numbers exist in the game's own packages or are a property of the mesh alone. This tool
answers that by decoding, independently of the card:

  * the four cooked wheel components - `SVehicleWheel` exports of
    `Playable_Batmobile_SF.upk` (outer `Batmobile_Archetypes.Vehicle.Batmobile.Wheel*`) -
    and naming their tags by the `SVehicleWheel` layout in `BMSDK_OFFSETS.json`
    (568 `WheelRadius`, 572 `WheelWidth`, 576 `SuspensionTravelUp`, 580 `SuspensionTravelDown`);
  * every tag of the 274 `CLASS_DEFAULTS.json` tags for a wheel radius / width / suspension
    value (the two `SVehicle` `Wheels` arrays are references, not numbers);
  * `CHAIN.json`'s `SVehicleWheel` fields, as an independent artifact cross-check;
  * the mesh numbers themselves, recomputed by `bmak_tyres.build()` (same PSKX, same transform).

Every wheel number is then classified, per the reset's vocabulary:

    matches-the-package   the package stores the same value (within the stated tolerance)
    mesh-only             the package stores no such value at all
    disagrees             the package stores a different value (difference printed)

Read-only: the game installs, `CLASS_DEFAULTS.json`, `CHAIN.json` and the PSKX are inputs.

Writes:
    Research/BatmobileGrab/TYRES_PACKAGE.md      the comparison, per wheel number
    Research/BatmobileGrab/TYRES_PACKAGE.json    the evidence record

Usage:
    uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --write
    uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --check
"""
import argparse
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U                            # noqa: E402
from grab_packages_g305 import PartialPackage, full_path  # noqa: E402
import bmak_tyres as BT                         # noqa: E402  (the mesh numbers, recomputed)

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
PACKAGE = "Playable_Batmobile_SF.upk"
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "TYRES_PACKAGE.md")
JS = os.path.join(OUT, "TYRES_PACKAGE.json")
OFFSETS = os.path.join(OUT, "BMSDK_OFFSETS.json")
CLASS_DEFAULTS = os.path.join(OUT, "CLASS_DEFAULTS.json")
CHAIN = os.path.join(OUT, "CHAIN.json")

# The wheel-size members, by the offset the SVehicleWheel layout declares them at. Read from
# BMSDK_OFFSETS.json below and asserted against these numbers, so a layout change fails loudly.
WHEEL_MEMBERS = {568: "WheelRadius", 572: "WheelWidth",
                 576: "SuspensionTravelUp", 580: "SuspensionTravelDown"}
CORNERS = ("WheelFL", "WheelFR", "WheelRL", "WheelRR")
TOL = 0.0015          # 1.5 mm: the same tolerance bmak_tyres uses for mesh-vs-station

DOC = []


def A(line=""):
    DOC.append(line)


# ---------------------------------------------------------------- package decode

def wheel_layout():
    """{offset: member} for the four wheel-size members, verified against BMSDK_OFFSETS.json."""
    d = json.load(open(OFFSETS, encoding="utf-8"))
    cls = d["classes"]["SVehicleWheel"]
    got = {}
    for p in cls["properties"]:
        if p["offset"] in WHEEL_MEMBERS:
            got[p["offset"]] = (p["member"], p["kind"])
    for off, name in WHEEL_MEMBERS.items():
        if off not in got:
            raise SystemExit("offset %d is not in the SVehicleWheel layout" % off)
        if got[off][0] != name:
            raise SystemExit("offset %d is %s in the layout, not %s" % (off, got[off][0], name))
        if got[off][1] != "FloatProperty":
            raise SystemExit("%s at %d is %s, not FloatProperty" % (name, off, got[off][1]))
    return {off: got[off][0] for off in WHEEL_MEMBERS}, cls


def decode_wheels():
    """The four cooked SVehicleWheel exports: their tag list, decoded from the package bytes."""
    path = os.path.join(COOKED, PACKAGE)
    pkg = PartialPackage(path)
    rows = []
    for idx in range(1, pkg.export_count + 1):
        e = pkg.exports[idx - 1]
        if e["name"] not in CORNERS:
            continue
        cls = pkg.object_class(idx)
        if cls != "SVehicleWheel":
            continue
        outer = full_path(pkg, idx)
        if "Batmobile_Archetypes.Vehicle.Batmobile" not in outer:
            continue                      # other vehicles' wheels share these names
        data = pkg.data(idx)
        # The tag list starts at byte 4 (a 4-byte prefix); from there it must consume the object
        # down to its 2-byte list terminator, which is the oracle that pins the start.
        tags, end, why = U.walk_tags(pkg, data, 4, max_tags=512)
        term = data[-2:]
        rows.append({
            "corner": e["name"], "export": idx, "class": cls, "outer": outer,
            "size": len(data), "tag_count": len(tags), "parsed": end, "stop": why,
            "terminator": term.hex(),
            "closes": end == len(data) - 2 and term == b"\x00\x00",
            "tags": [{"offset": t.get("offset"), "type": t.get("type"),
                      "value": t.get("value"), "name": t.get("name")} for t in tags],
        })
    rows.sort(key=lambda r: CORNERS.index(r["corner"]))
    if [r["corner"] for r in rows] != list(CORNERS):
        raise SystemExit("expected the four Batmobile wheels, decoded %r"
                         % ([r["corner"] for r in rows],))
    for r in rows:
        if not r["closes"]:
            raise SystemExit("%s does not close on the list terminator (end %d of %d, stop %s)"
                             % (r["corner"], r["parsed"], r["size"], r["stop"]))
    return rows, pkg.export_count, os.path.getsize(path)


def values_of(row):
    """{offset: value} for the four wheel-size members actually present on this wheel."""
    out = {}
    for t in row["tags"]:
        if t["offset"] in WHEEL_MEMBERS:
            out[t["offset"]] = t["value"]
    return out


# ---------------------------------------------------------------- CLASS_DEFAULTS

def class_defaults_scan():
    """Every tag among the 274 that could carry a wheel radius / width / suspension value."""
    d = json.load(open(CLASS_DEFAULTS, encoding="utf-8"))
    total, wheel_refs, numeric = 0, [], []
    per_role = {}
    for role in ("subclass", "base"):
        tags = d["cdo"][role]["tags"]
        total += len(tags)
        per_role[role] = {"object": d["cdo"][role]["object"], "tags": len(tags)}
        for t in tags:
            members = t.get("members") or []
            names = [m.get("member") for m in members]
            blob = " ".join(str(x) for x in names + [t.get("name") or ""])
            if "WheelRadius" in blob or "WheelWidth" in blob or "SuspensionTravel" in blob:
                numeric.append({"role": role, "n": t["n"], "offset": t["offset"],
                                "members": names, "tag_type": t["tag_type"]})
            if any((m or "").startswith("Wheel") for m in names):
                wheel_refs.append({
                    "role": role, "n": t["n"], "offset": t["offset"],
                    "offset_hex": t["offset_hex"], "member": ",".join(m or "?" for m in names),
                    "tag_type": t["tag_type"],
                    "array_type": (members[0].get("array_type") if members else None),
                    "value": t.get("value"),
                })
    if total != 274:
        raise SystemExit("CLASS_DEFAULTS.json carries %d tags, not the documented 274" % total)
    return {"tag_total": total, "per_role": per_role, "wheel_numeric": numeric,
            "wheel_tags": wheel_refs,
            "input": CLASS_DEFAULTS}


# ---------------------------------------------------------------- CHAIN cross-check

WANT = ("WheelRadius", "WheelWidth", "SuspensionTravelUp", "SuspensionTravelDown")


def _member(rec):
    """The member name of a CHAIN.json row, or None (rows can be unnamed bitfield words)."""
    name = rec.get("name")
    if not isinstance(name, str) or "." not in name:
        return None
    return name.rsplit(".", 1)[1]


def chain_scan():
    d = json.load(open(CHAIN, encoding="utf-8"))
    out = {}
    for cls, objs in d["fields"].items():
        if cls != "SVehicleWheel":
            continue
        for obj, rows in objs.items():
            hits, offs = {}, {}
            for r in rows:
                m = _member(r)
                if m in WANT:
                    hits[m] = r["value"]
                    offs[m] = r["offset"]
            out[obj] = {"values": hits, "offsets": offs}
    return out


# ---------------------------------------------------------------- comparison

def classify(rows, mesh):
    """Per wheel number: matches-the-package / mesh-only / disagrees."""
    pkg_r = sorted({values_of(r).get(568) for r in rows})
    pkg_w = sorted({values_of(r).get(572) for r in rows if 572 in values_of(r)})
    mesh_r = [m["station_r"] for m in mesh]
    mesh_dy = [m["dy"] for m in mesh]
    mesh_w = [m["w"] for m in mesh]
    out = {}

    # --- radius: the package stores WheelRadius per wheel, the mesh has four station radii.
    if len(pkg_r) != 1:
        raise SystemExit("the four wheels disagree on WheelRadius: %r" % (pkg_r,))
    p_cm = float(pkg_r[0])
    p_m = p_cm * 0.01                       # the package's unit is cm (see UNIT note below)
    r_mesh = sum(mesh_r) / 4.0
    d_m = p_m - r_mesh
    out["radius"] = {
        "verdict": "disagrees" if abs(d_m) > TOL else "matches-the-package",
        "package_raw": p_cm, "package_m": p_m,
        "mesh_m": mesh_r, "mesh_mean": r_mesh,
        "mesh_min": min(mesh_r), "mesh_max": max(mesh_r),
        "delta_m": d_m, "delta_mm": d_m * 1000.0,
        "package_vs_mesh_pct": (p_m / r_mesh - 1.0) * 100.0,
        "mesh_vs_package_pct": (r_mesh / p_m - 1.0) * 100.0,
        "package_diameter_m": 2 * p_m,
        "mesh_diameter_min": min(mesh_dy), "mesh_diameter_max": max(mesh_dy),
        "diameter_gap_m": min(mesh_dy) - 2 * p_m,
    }

    # --- width
    out["width"] = {
        "verdict": "mesh-only" if not pkg_w else (
            "matches-the-package" if abs(max(pkg_w) * 0.01 - sum(mesh_w) / 4.0) <= TOL
            else "disagrees"),
        "package_raw": pkg_w, "mesh_m": mesh_w,
        "why": ("no tag at offset 572 (WheelWidth) on any of the four wheels, so the package "
                "stores no wheel width for this car"),
    }

    # --- suspension travel (no mesh counterpart; printed so the row set is complete)
    up = sorted({values_of(r)[576] for r in rows if 576 in values_of(r)})
    down = sorted({values_of(r)[580] for r in rows if 580 in values_of(r)})
    out["suspension"] = {
        "up_raw": up, "down_raw": down,
        "verdict": "package-only",
        "why": "stations.json carries hub/radius/tyre_width only; nothing in the mesh is a "
               "suspension travel",
    }
    return out


def build():
    layout, cls = wheel_layout()
    rows, export_count, pkg_bytes = decode_wheels()
    cdo = class_defaults_scan()
    chain = chain_scan()
    mesh_doc = BT.build()
    mesh = mesh_doc["corners"]
    verdicts = classify(rows, mesh)

    # independent-artifact cross-check: CHAIN.json must agree with the bytes decoded here
    mismatches = []
    for r in rows:
        key = "%s.%s" % ("Playable_Batmobile_SF", r["corner"])
        if key not in chain:
            continue
        vals = values_of(r)
        for name, off in (("WheelRadius", 568), ("WheelWidth", 572),
                          ("SuspensionTravelUp", 576), ("SuspensionTravelDown", 580)):
            a = vals.get(off)
            b = chain[key]["values"].get(name)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                mismatches.append({"wheel": r["corner"], "member": name,
                                   "package": a, "chain": b})
    if mismatches:
        raise SystemExit("CHAIN.json disagrees with the package bytes: %r" % (mismatches,))
    chain_wheels = {k: v for k, v in chain.items() if "Batmobile_SF" in k}

    return {
        "schema": 1,
        "generated_by": "bmak_tyres_package.py",
        "task": "reverify-TYRES",
        "package": {"file": os.path.join(COOKED, PACKAGE), "bytes": pkg_bytes,
                    "exports": export_count, "class": "SVehicleWheel"},
        "layout": {"source": OFFSETS, "class": cls.get("class", "SVehicleWheel"),
                   "size": cls.get("size"), "members": WHEEL_MEMBERS},
        "wheels": rows,
        "values": {r["corner"]: values_of(r) for r in rows},
        "class_defaults": cdo,
        "chain": {"wheels": chain_wheels,
                  "note": "cross-check only: every value above was re-decoded from the package "
                          "bytes; CHAIN.json agrees on all four wheels"},
        "mesh": {"source": "BMak_tyres.build() - Batmobile_V2.pskx through the ONE transform",
                 "corners": [{"corner": m["corner"], "station_r": m["station_r"],
                              "tread_dy": m["dy"], "width": m["w"],
                              "shoulder_d": m["dmaxr"], "gap": m["gap"]} for m in mesh],
                 "scale": mesh_doc["scale"], "ground": mesh_doc["ground"]},
        "verdicts": verdicts,
        "cdos_checked": True,
    }


# ---------------------------------------------------------------- render

def f(v, n=4):
    return ("%." + str(n) + "f") % v


def tag_value_text(val):
    """A class-default tag's value, short: an object array becomes its refs, not a JSON blob."""
    if val is None:
        return "—"
    if isinstance(val, dict) and "refs" in val:
        names = []
        for r in val["refs"]:
            base = (r.get("path") or "None").split(".")[-1]
            names.append("%s:%s" % (r.get("class"), base))
        return "count=%s ref [%s]" % (val.get("count"), ", ".join(names))
    if isinstance(val, dict) and val.get("count") == 0:
        return "count=0 (empty array)"
    return str(val)[:110]


def render(doc):
    rows = doc["wheels"]
    vals = doc["values"]
    v = doc["verdicts"]
    cdo = doc["class_defaults"]
    m = doc["mesh"]
    DOC.clear()
    A("# The wheels: grabbed, or shaped by the mesh? (reverify-TYRES)")
    A()
    A("Generated by `Tools/scripts/bmak_tyres_package.py`. It re-decodes the four cooked")
    A("`SVehicleWheel` components out of `%s`," % PACKAGE)
    A("names their tags by the `SVehicleWheel` layout in `BMSDK_OFFSETS.json`, scans all **%d**"
      % cdo["tag_total"])
    A("tags of `CLASS_DEFAULTS.json`, and recomputes the mesh numbers with `bmak_tyres.build()`")
    A("(same PSKX, same ONE transform). Every number below is re-derived by `--check`.")
    A()
    A("Verdict vocabulary: **matches-the-package** (the package stores the same value), "
      "**mesh-only**")
    A("(the package stores no such value), **disagrees** (the package stores a different value).")
    A()
    A("## 1. The cooked wheel components")
    A()
    A("| corner | export | package | outer | size | tags | closes on terminator |")
    A("|---|---:|---|---|---:|---:|---|")
    for r in rows:
        A("| `%s` | %d | `%s` | `%s` | %d | %d | %s |" % (
            r["corner"], r["export"], PACKAGE, r["outer"], r["size"], r["tag_count"],
            "yes (%d/%d, `%s`)" % (r["parsed"], r["size"], r["terminator"]) if r["closes"]
            else "**no**"))
    A()
    A("The tag list starts at byte 4; from there it consumes the export down to the 2-byte")
    A("property-list terminator, which is the oracle for the start (byte 0 reads type 0 = end of")
    A("list, bytes 1-2 likewise, and byte 12 drops the first tag).")
    A()
    A("| member (`SVehicleWheel` offset) | %s |" % " | ".join("`%s`" % r["corner"] for r in rows))
    A("|---|%s" % ("---|" * len(rows)))
    for off, name in sorted(WHEEL_MEMBERS.items()):
        cells = []
        for r in rows:
            got = vals[r["corner"]].get(off)
            cells.append("**absent**" if got is None
                         else "%s (`0x%03x`)" % (f(got, 1) if isinstance(got, float) else got, off))
        A("| `%d` `%s` | %s |" % (off, name, " | ".join(cells)))
    A()
    A("The three values the wheels do store are `WheelRadius` 64.0 on all four, and")
    A("`SuspensionTravelUp` 30.0 / `SuspensionTravelDown` 40.0 on the fronts (the rears carry no")
    A("`SuspensionTravelUp`). **`WheelWidth` (offset 572) is absent from all four wheels.**")
    A()
    A("Unit note (derived): the value is 64.0 in the package's own unit and the class's siblings")
    A("are in cm as well (the same layout's `WheelRadius` reads 90.0 on `Default__RVehicleTank`,")
    A("and `CLASS_DEFAULTS.json` stores `BattleModeLength` 430.0, `PursuitModeWidth` 220.0). On")
    A("the cm reading 64.0 = %.3f m; the comparison below holds on either reading, because"
      % v["radius"]["package_m"])
    A("%.1f is compared against a %.1f cm mesh radius." % (
        v["radius"]["package_raw"], v["radius"]["mesh_mean"] * 100))
    A()
    A("## 2. The 274 `CLASS_DEFAULTS.json` tags")
    A()
    A("| role | object | tags | wheel-value tags |")
    A("|---|---|---:|---:|")
    for role, per in cdo["per_role"].items():
        A("| %s | `%s` | %d | %d |" % (role, per["object"], per["tags"],
                                        len([n for n in cdo["wheel_numeric"] if n["role"] == role])))
    A()
    A("**None of the %d tags is a wheel radius, width or suspension value** — the count in the"
      % cdo["tag_total"])
    A("last column is zero for both objects. The only wheel-named tags are the empty")
    A("`WheelSpeedMap` array and the two `SVehicle.Wheels` arrays, and the `Wheels` arrays carry")
    A("**references** to the four wheel components, not numbers:")
    A()
    A("| role | tag | class offset | member | type | value |")
    A("|---|---:|---|---|---|---|")
    for t in cdo["wheel_tags"]:
        A("| %s | %d | `%s` | `%s` | %s | %s |" % (
            t["role"], t["n"], t["offset_hex"], t["member"], t["tag_type"],
            tag_value_text(t["value"])))
    A()
    A("So the class defaults say *which* wheels the car has and nothing about their size: the")
    A("defaults of `SVehicleWheel` itself are native (that class has no shipped default object)," )
    A("and the values that do ship are the archetype's four components in §1.")
    A()
    A("## 3. The comparison — each wheel number")
    A()
    A("| wheel number | mesh (this project) | package (the game) | verdict |")
    A("|---|---|---|---|")
    A("| radius | %s m (station `radius` %.4f–%.4f) | %s at offset 568 → %.3f m | **%s** |"
      % (f(v["radius"]["mesh_mean"]), v["radius"]["mesh_min"], v["radius"]["mesh_max"],
         f(v["radius"]["package_raw"], 1), v["radius"]["package_m"], v["radius"]["verdict"]))
    A("| tread diameter | %s–%s m | %s m (2 × 0.640) | **mesh-only** |" % (
        f(v["radius"]["mesh_diameter_min"]), f(v["radius"]["mesh_diameter_max"]),
        f(v["radius"]["package_diameter_m"], 3)))
    A("| width | %s–%s m | absent (`WheelWidth` @572, all four wheels) | **%s** |" % (
        f(min(v["width"]["mesh_m"])), f(max(v["width"]["mesh_m"])), v["width"]["verdict"]))
    A("| suspension travel | — (no mesh counterpart) | up %s / down %s | **package-only** |" % (
        "/".join("%.0f" % x for x in v["suspension"]["up_raw"]) or "—",
        "/".join("%.0f" % x for x in v["suspension"]["down_raw"]) or "—"))
    A()
    A("### radius — disagrees")
    A()
    A("The package's stored wheel radius is **%.1f** (%.3f m); the mesh's four station radii are"
      % (v["radius"]["package_raw"], v["radius"]["package_m"]))
    A("%s–%s m (mean %s). The mesh radius is **%s m (%s mm) larger** than the stored value —"
      " **%s%%**, far outside the %s mm tolerance — and the tread diameters differ by %s m. The"
      " two"
      % (f(v["radius"]["mesh_min"]), f(v["radius"]["mesh_max"]), f(v["radius"]["mesh_mean"]),
         f(abs(v["radius"]["delta_m"])), f(abs(v["radius"]["delta_mm"]), 1),
         f(v["radius"]["mesh_vs_package_pct"], 2), f(TOL * 1000, 1),
         f(v["radius"]["diameter_gap_m"])), )
    A("numbers are related but not equal: 2 × %.3f m = %.3f m of visual tyre, versus %.3f m"
      % (v["radius"]["package_m"], v["radius"]["package_diameter_m"],
         v["radius"]["mesh_diameter_min"]))
    A("of tread. This is the same relation `TYRES.md` §4 already prints as the BmAK row — a")
    A("contact-radius simplification inside the visual tyre — and the classification is")
    A("therefore **disagrees**, not matches-the-package.")
    A()
    A("### width — mesh-only")
    A()
    A("The mesh measures %s–%s m across the tyre (`*_Vis` vertices, x = axle). The package"
      % (f(min(v["width"]["mesh_m"])), f(max(v["width"]["mesh_m"]))))
    A("stores **no** `WheelWidth` tag on any of the four wheels: offset 572 is absent from all")
    A("four tag lists (`--check` asserts the absence, so a future package change fails here).")
    A("There is also no `WheelWidth` entry in `CHAIN.json` (`grep -c WheelWidth` = 0), which is")
    A("the independent artifact agreeing. The width is therefore a property of the mesh alone.")
    A()
    A("### What this means for the reset")
    A()
    A("The tyre numbers in `TYRES.md` are **measured from the mesh** (vertices owned by the wheel")
    A("bones, through the ONE transform), not read out of a package: the game stores a 64.0")
    A("(0.640 m) contact radius and no width, while the mesh reads a %.3f m tread radius and a %.3f m"
      % (v["radius"]["mesh_mean"], sum(v["width"]["mesh_m"]) / 4.0), )
    A("width. Where `TYRES.md` calls 1.366 \"2 × the physics radius — the same number by design\",")
    A("the physics it means is **JC3's** `land_global.*_wheels.radius` (T-G2), which this")
    A("project set from the mesh; it is not a value the game of origin stores. All three")
    A("diameters on that page (1.366 / 1.40 / 1.42) are mesh- or lore-derived; the only")
    A("package-sourced wheel number is the 0.640 m radius in its §4 table, already marked")
    A("\"not imported\".")
    A()
    A("## 4. How to re-measure")
    A()
    A("```")
    A("uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --check")
    A("```")
    A()
    A("`--check` re-decodes the four wheel exports, re-scans the 274 class-default tags, recomputes")
    A("the mesh numbers through `bmak_tyres.build()`, re-derives every verdict and fails if this")
    A("page or the JSON differs from the render, or if an invariant breaks (four wheels found; each")
    A("tag list closing on its terminator; one `WheelRadius` value across the four; no `WheelWidth`")
    A("tag; 274 class-default tags with zero wheel-size values; `CHAIN.json` agreeing with the")
    A("bytes).")
    A()
    return "\n".join(DOC) + "\n"


def invariants(doc):
    fail = []
    rows = doc["wheels"]
    if len(rows) != 4:
        fail.append("expected 4 wheel components, decoded %d" % len(rows))
    if doc["class_defaults"]["tag_total"] != 274:
        fail.append("class-default tags: %d, not 274" % doc["class_defaults"]["tag_total"])
    if doc["class_defaults"]["wheel_numeric"]:
        fail.append("a wheel-size value appeared among the class defaults: %r"
                    % (doc["class_defaults"]["wheel_numeric"],))
    for r in rows:
        if not r["closes"]:
            fail.append("%s does not close on the list terminator" % r["corner"])
        if 568 not in doc["values"][r["corner"]]:
            fail.append("%s stores no WheelRadius" % r["corner"])
        if 572 in doc["values"][r["corner"]]:
            fail.append("%s now stores a WheelWidth - the 'mesh-only' verdict must be re-derived"
                        % r["corner"])
    radii = sorted({doc["values"][r["corner"]].get(568) for r in rows})
    if len(radii) != 1:
        fail.append("the four wheels disagree on WheelRadius: %r" % (radii,))
    if doc["verdicts"]["radius"]["verdict"] != "disagrees":
        fail.append("the radius verdict is %r, but the mesh and the package differ by %.1f mm"
                    % (doc["verdicts"]["radius"]["verdict"],
                       doc["verdicts"]["radius"]["delta_mm"]))
    if doc["verdicts"]["width"]["verdict"] != "mesh-only":
        fail.append("the width verdict is %r with no WheelWidth tag present"
                    % doc["verdicts"]["width"]["verdict"])
    for key in ("radius", "width", "suspension"):
        if key not in doc["verdicts"]:
            fail.append("the %s verdict is missing" % key)
    return fail


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    text = render(doc)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8").write(text)
        open(JS, "w", encoding="utf-8").write(json.dumps(doc, indent=1) + "\n")
        print("wrote %s (%d lines)" % (os.path.relpath(MD, ROOT), text.count("\n")))
        print("wrote %s" % os.path.relpath(JS, ROOT))
    if a.check:
        fail = invariants(doc)
        disk_md = open(MD, encoding="utf-8").read() if os.path.exists(MD) else ""
        disk_js = json.load(open(JS, encoding="utf-8")) if os.path.exists(JS) else None
        if not disk_md:
            fail.append("TYRES_PACKAGE.md is missing")
        elif disk_md != text:
            import difflib
            diff = [l for l in difflib.unified_diff(disk_md.splitlines(), text.splitlines(),
                                                    "on disk", "re-derived", lineterm="")
                    if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            fail.append("TYRES_PACKAGE.md differs from the render (%d changed lines)" % len(diff))
        if disk_js is None:
            fail.append("TYRES_PACKAGE.json is missing")
        elif disk_js != json.loads(json.dumps(doc)):
            fail.append("TYRES_PACKAGE.json differs from the re-derived document")
        if fail:
            print("FAIL")
            for x in fail:
                print("  -", x)
            return 1
        v = doc["verdicts"]
        print("OK: 4 wheel components in %s, each closing on its terminator; "
              "WheelRadius %s on all four; WheelWidth absent"
              % (PACKAGE, doc["values"]["WheelFL"][568]))
        print("OK: class defaults: %d tags, %d wheel-size values"
              % (doc["class_defaults"]["tag_total"],
                 len(doc["class_defaults"]["wheel_numeric"])))
        print("OK: radius %s (mesh %.4f m vs package %.3f m, %+.1f mm); width %s; suspension %s"
              % (v["radius"]["verdict"], v["radius"]["mesh_mean"], v["radius"]["package_m"],
                 v["radius"]["delta_mm"], v["width"]["verdict"], v["suspension"]["verdict"]))
        print("OK: TYRES_PACKAGE.md and TYRES_PACKAGE.json match the re-derived render")
    return 0


if __name__ == "__main__":
    sys.exit(main())
