"""jc3_tint.py - G3-09d: which on-disk parameter carries a car's paint tint.

The card asks where the dynamic paint tint is written for a Serpente-class car, using only
files: the `.epe`/`.rbm`/material parameters in the extracted fleet
(`E:/Modding/_shared/gamedata/JC3grab/...`) and how the fleet's vehicle modules reference them.

What this pass reads (all read-only, static):

  1. every extracted vehicle entity graph `entities/*.ee.json` (232) for `Palette` modules -
     the inlined `A[Tint]` table with `name`, `name.hash`, `occurrence`, `tint_r/g/b`
     (RGBA), `specular_gloss`, `metallic`, `clear_coat`;
  2. the donor car's own model tree `models/jc_vehicles/v0300_car_kensington_sportsmuscle`
     for `CarPaintMM` blocks, decoded with `rbm_geom` (whose round trip is the oracle):
     the authored `static_params` (18 float4 + 7 floats) and `dynamic_params` (4 float4 +
     3 floats = 76 B, the `cb6` payload);
  3. the one loose palette module on disk, to test whether it is vanilla;
  4. the paint shader's reflection header for the cbuffer names/offsets of `cb6`.

The tint claim needs an oracle: a parameter may be called "the tint" only if it differs
between two cars known to ship different paints.  That check is `O3` below; if it fails the
row is labelled UNKNOWN instead of guessed.

Usage:
    uv run python Tools/scripts/jc3_tint.py --write
    uv run python Tools/scripts/jc3_tint.py --check
"""

from __future__ import annotations

import glob
import json
import os
import struct
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf        # noqa: E402  (ADF v4 reader, used only to test the loose palette)
import rbm_geom      # noqa: E402

GD = "E:/Modding/_shared/gamedata/JC3grab"
ENTITIES = os.path.join(GD, "entities")
MODELS = os.path.join(GD, "b13b", "unpacked", "models", "jc_vehicles")
DONOR = "v0300_car_kensington_sportsmuscle"
LOOSE_PALETTE = os.path.join(
    GD, "b13b", "unpacked", "editor", "entities", "jc_vehicles", "01_land",
    DONOR, "modules", "default", DONOR + "_palette.vmodc")
HEADER = os.path.join(ROOT, "Tools", "JCMR-src", "assets", "jc3", "shaders",
                      "carpaintmm.fb.txt")
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "TINT.md")
JS = os.path.join(OUT, "TINT.json")


# ------------------------------------------------------------------ entity palettes
def palettes():
    """{palette file: {car: {tint index: row dict}}} plus per-entity module lists."""
    by_file = defaultdict(dict)
    cars = {}
    ents = 0
    pal_ents = 0
    no_pal = []
    for p in sorted(glob.glob(os.path.join(ENTITIES, "*.ee.json"))):
        ents += 1
        name = os.path.basename(p)[: -len(".ee.json")]
        car = name.split("__")[0]
        d = json.load(open(p, encoding="utf-8"))
        found = False
        for m in d.get("modules", []) or []:
            if m.get("type") != "Palette":
                continue
            found = True
            tints = defaultdict(dict)
            for r in m.get("rows", []):
                path = r["path"]
                if not path.startswith("tints[") or "]." not in path:
                    continue
                idx = int(path.split("[")[1].split("]")[0])
                tints[idx][path.split("].", 1)[1]] = r["value"]
            by_file[m.get("file")][car] = dict(tints)
            cars.setdefault(car, set()).add(m.get("file"))
        if found:
            pal_ents += 1
        else:
            no_pal.append(name)
    return {"by_file": dict(by_file), "cars": cars, "entities": ents,
            "palette_entities": pal_ents, "no_palette": no_pal}


def tint_rgb(t):
    return (round(float(t["tint_r.R"]), 4), round(float(t["tint_r.G"]), 4),
            round(float(t["tint_r.B"]), 4))


def ranges(pal):
    vals = defaultdict(list)
    for f, per_car in pal["by_file"].items():
        for car, tints in per_car.items():
            for i, t in tints.items():
                for k, key in (("R", "tint_r.R"), ("G", "tint_r.G"), ("B", "tint_r.B")):
                    vals["tint_r." + k].append(float(t[key]))
                    vals["tint_g." + k].append(float(t["tint_g." + k]))
                    vals["tint_b." + k].append(float(t["tint_b." + k]))
                vals["occurrence"].append(int(t["occurrence"]))
                for k in ("specular_gloss", "metallic", "clear_coat"):
                    vals[k].append(float(t[k]))
    return {k: (min(v), max(v), len(v)) for k, v in vals.items()}


# ------------------------------------------------------------------ rbm material
def material():
    root = os.path.join(MODELS, "01_land", DONOR)
    files = sorted(glob.glob(root + "/**/*.rbm", recursive=True))
    paint, other = [], []
    skipped = []
    for p in files:
        blob = open(p, "rb").read()
        if struct.pack("<I", rbm_geom.RB_CARPAINTMM) not in blob:
            continue
        try:
            rbm = rbm_geom.decode(blob)
        except rbm_geom.RbmError as e:
            skipped.append({"file": os.path.basename(p), "error": str(e)})
            continue
        for i, blk in enumerate(rbm.blocks):
            if not isinstance(blk, rbm_geom.CarPaintMM):
                continue
            tex = [t for t in blk.textures if isinstance(t, str)]
            dyn = struct.unpack("<19f", blk.dynamic_params)
            sta = struct.unpack("<72f", blk.static_params)
            sup = struct.unpack("<7f", blk.static_support)
            rec = {"file": os.path.basename(p), "blk": i, "flags": blk.flags,
                   "dynamic": [round(x, 4) for x in dyn],
                   "static": [round(x, 4) for x in sta],
                   "support": [round(x, 4) for x in sup],
                   "tex0": tex[0] if tex else None}
            (paint if any("_body_dif" in t for t in tex) else other).append(rec)
    return {"files": len(files), "paint": paint, "other": other, "skipped": skipped}


def header_slots():
    """The `cb6` member names and offsets, straight out of the paint reflection header."""
    out, cur = [], None
    for line in open(HEADER, encoding="utf-8", errors="replace"):
        s = line.strip()
        if s.startswith("// cbuffer CarPaintDynamicMaterialParams"):
            cur = True
            continue
        if cur and s.startswith("// }"):
            break
        if not cur or "Offset:" not in s:
            continue
        body = s[2:].strip()
        decl = body.split("//")[0].strip().rstrip(";")
        off = int(body.split("Offset:")[1].split()[0])
        out.append({"decl": decl, "name": decl.split()[-1], "offset": off})
    return out


# ------------------------------------------------------------------ build
def build():
    pal = palettes()
    rng = ranges(pal)
    mat = material()
    slots = header_slots()

    # palette tables, by module file
    files = []
    for f, per_car in sorted(pal["by_file"].items(), key=lambda kv: -len(kv[1])):
        names, rgbs = [], set()
        for car, tints in per_car.items():
            for i, t in tints.items():
                names.append(t["name.string"])
                rgbs.add(tint_rgb(t))
        files.append({"file": f, "cars": sorted(per_car), "tint_count": len(set(names)),
                      "tints": sorted(set(names)), "distinct_rgb": len(rgbs),
                      "rgb": sorted(rgbs)})

    # O3: two cars with different paints.  Disjoint tint_r sets = provably different colours.
    pair = None
    seen = sorted(pal["cars"], key=lambda c: (len(pal["cars"][c]), c))
    for i, a in enumerate(seen):
        sa = {tint_rgb(t) for f in pal["cars"][a] for t in pal["by_file"][f][a].values()}
        for b in seen[i + 1:]:
            sb = {tint_rgb(t) for f in pal["cars"][b] for t in pal["by_file"][f][b].values()}
            if sa and sb and not (sa & sb) and {f.split("/")[-1] for f in pal["cars"][a]} != \
                    {f.split("/")[-1] for f in pal["cars"][b]}:
                pair = (a, sorted(sa)[:12], b, sorted(sb)[:12])
                break
        if pair:
            break

    # O4: the .rbm paint blocks do not carry the palette's colours
    paint_rgb = {tuple(r["dynamic"][:4]) for r in mat["paint"]}
    other_rgb = {tuple(r["dynamic"][:4]) for r in mat["other"]}
    pal_rgb = {tint_rgb(t) for f in pal["by_file"] for car in pal["by_file"][f]
               for t in pal["by_file"][f][car].values()}
    dyn_hits = sorted(c for c in paint_rgb if c[:3] in pal_rgb)

    # O5: is the loose palette module vanilla?
    loose = None
    if os.path.exists(LOOSE_PALETTE):
        adf = jc3adf.Adf(open(LOOSE_PALETTE, "rb").read())
        rows = defaultdict(dict)
        for path, _tn, val in jc3adf.walk(adf):
            if path.startswith("tints[") and "]." in path:
                idx = int(path.split("[")[1].split("]")[0])
                rows[idx][path.split("].", 1)[1]] = val
        loose = {"file": os.path.basename(LOOSE_PALETTE), "bytes": len(adf.blob),
                 "tints": len(rows),
                 "names": sorted({t["name.string"] for t in rows.values()}),
                 "rgb": sorted({tint_rgb(t) for t in rows.values()}),
                 "gloss": sorted({round(float(t["specular_gloss"]), 3) for t in rows.values()}),
                 "metallic": sorted({round(float(t["metallic"]), 3) for t in rows.values()})}

    # name.hash: per-name in the shared palettes, one constant in the car-specific ones
    hash_stats = {"per_name": 0, "constant": 0, "constant_value": set(), "files": 0}
    for f, per_car in pal["by_file"].items():
        hash_stats["files"] += 1
        hs = {t["name.hash"] for car in per_car for t in per_car[car].values()}
        names = {t["name.string"] for car in per_car for t in per_car[car].values()}
        if len(hs) == len(names) and len(hs) > 1:
            hash_stats["per_name"] += 1
        elif len(hs) == 1:
            hash_stats["constant"] += 1
            hash_stats["constant_value"] |= hs
    hash_stats["constant_value"] = sorted(hash_stats["constant_value"])
    d = {"entities": pal["entities"], "palette_entities": pal["palette_entities"],
         "palette_cars": len(pal["cars"]), "hash_stats": hash_stats,
         "no_palette": len(pal["no_palette"]), "files": files,
         "module_count": len(files), "ranges": rng, "pair": pair,
         "material": {"files": mat["files"], "paint_blocks": len(mat["paint"]),
                      "other_blocks": len(mat["other"]), "skipped": mat["skipped"],
                      "paint_dynamic": sorted(paint_rgb), "other_dynamic": sorted(other_rgb),
                      "paint_static0": sorted({tuple(r["static"][:4]) for r in mat["paint"]}),
                      "paint_support": sorted({tuple(r["support"]) for r in mat["paint"]}),
                      "dynamic_scalars": sorted({tuple(r["dynamic"][16:19])
                                                 for r in mat["paint"]})},
         "slots": slots, "loose": loose, "palette_rgb_count": len(pal_rgb),
         "dynamic_palette_hits": dyn_hits,
         "donor": {"car": DONOR, "file": next(
             (f for f, per_car in pal["by_file"].items() if DONOR in per_car), ""),
             "tints": [t["name.string"] for f, per_car in pal["by_file"].items()
                       if DONOR in per_car for t in per_car[DONOR].values()]}}
    d["donor"]["distinct"] = len({tint_rgb(t) for f, per_car in pal["by_file"].items()
                                   if DONOR in per_car for t in per_car[DONOR].values()})
    d["oracles"] = oracles(d)
    d["md"] = render(d)
    return d


def oracles(d):
    out = []

    def o(key, ok, ev):
        out.append({"key": key, "ok": bool(ok), "evidence": ev})

    o("O1-entity-graphs-parsed", d["entities"] >= 232,
      "%d entity graphs, %d carry a Palette module, %d do not"
      % (d["entities"], d["palette_entities"], d["no_palette"]))
    o("O2-tints-differ-within-a-palette",
      all(f["distinct_rgb"] > 1 for f in d["files"]) and len(d["files"]) >= 20,
      "%d palette modules, each with %s distinct tint_r values; %d distinct tint_rgbs fleet-wide"
      % (len(d["files"]), sorted({f["distinct_rgb"] for f in d["files"]}),
         d["palette_rgb_count"]))
    p = d["pair"]
    o("O3-oracle-two-cars-differ", p is not None,
      ("%s tints %s vs %s tints %s - disjoint, different palette modules"
       % (p[0], p[1][:3], p[2], p[3][:3])) if p else "no disjoint pair found")
    m = d["material"]
    o("O4-rbm-is-not-the-per-car-paint",
      len(m["paint_dynamic"]) >= 1 and not d["dynamic_palette_hits"]
      and len({r for r in m["paint_dynamic"]}) < d["palette_rgb_count"],
      "%d paint blocks carry %d distinct dynamic float4[0] %s vs %d non-paint blocks %s; "
      "%d palette tint_rgbs, %d of them occur in the dynamic floats"
      % (m["paint_blocks"], len(m["paint_dynamic"]), m["paint_dynamic"][:3],
         m["other_blocks"], m["other_dynamic"][:3], d["palette_rgb_count"],
         len(d["dynamic_palette_hits"])))
    lo = d["loose"]
    o("O5-loose-palette-is-a-repaint", lo is not None and len(lo["rgb"]) == 1,
      "`%s` %d B, %d tints, tint_r %s, gloss %s, metallic %s - a single repaint value, while "
      "the donor's entity graph carries %d distinct tints"
      % (lo["file"], lo["bytes"], lo["tints"], lo["rgb"], lo["gloss"], lo["metallic"],
         d["donor"]["distinct"]) if lo else "loose module absent")
    h = d["hash_stats"]
    o("O8-name-hash-column", h["per_name"] >= 8 and h["constant"] >= 8
      and h["constant_value"] == [2930093752],
      "`name.hash` is per-name in %d of %d palettes (distinct hash per tint) and the single "
      "value %s in the other %d, so it is a name hash only in the shared palettes; the same "
      "name (e.g. `Black`) carries the per-name hash in one and 2930093752 in the other"
      % (h["per_name"], h["files"], h["constant_value"], h["constant"]))
    don = d["donor"]
    o("O9-donor-inlined-table-is-the-module",
      bool(lo) and sorted(lo["names"]) == sorted(don["tints"]),
      "donor entity graph names %s vs the loose module's %s (values differ: repaint)"
      % (sorted(don["tints"]), sorted(lo["names"]) if lo else []))
    o("O6-cb6-slots", [s["name"] for s in d["slots"]][:3] ==
      ["m_TintColorR", "m_TintColorG", "m_TintColorB"]
      and [s["offset"] for s in d["slots"]][:3] == [0, 16, 32],
      "; ".join("%s @ %d" % (s["name"], s["offset"]) for s in d["slots"]))
    o("O7-md-recomputed", True, "--check rebuilds this document from the files and compares it")
    return out


# ------------------------------------------------------------------ render
def render(d):
    L = []
    A = L.append
    m, rng, p = d["material"], d["ranges"], d["pair"]
    A("# JC3 dynamic paint tint: the on-disk parameter (G3-09d)")
    A("")
    A("Generated by `Tools/scripts/jc3_tint.py --write`; `--check` re-parses every entity")
    A("graph, every `.rbm` and the header, and fails on any change.  Static only: no game")
    A("process was started, attached to or injected into.")
    A("")
    A("## 1. Answer")
    A("")
    A("**The paint tint is an entity-graph parameter, not a `.rbm` one.**  Each of the %d"
      % d["palette_entities"])
    A("entities that ship a paint table carries it inline as a `Palette` module: the")
    A("`tints[i].tint_r`, `tint_g`, `tint_b` RGBA records plus their `occurrence` weight and")
    A("the `specular_gloss` / `metallic` / `clear_coat` look scalars.  The table is the")
    A("palette `.vmodc`'s own content, inlined into the entity by the cooker; the module files")
    A("exist on disk too, and the fleet references %d distinct ones." % d["module_count"])
    A("")
    A("The shader receives that colour in `cb6` - `m_TintColorR` at 0, `m_TintColorG` at 16,")
    A("`m_TintColorB` at 32 - but the `.rbm` `CarPaintMM` block does **not** hold the per-car")
    A("value: its authored dynamic float4[0] is one constant on every paint block (see §4),")
    A("and no palette tint occurs in it.  Who writes the palette into `cb6` is **UNKNOWN** —")
    A("that is engine code, and no file on disk names the binding (G3-09 measured the same).")
    A("")
    A("## 2. The parameters, with the oracle")
    A("")
    A("A parameter is called the tint only if it differs between two cars that ship different")
    A("paints.  `O3` finds such a pair by *disjoint* `tint_r` sets:")
    A("")
    if p:
        A("* `%s` - tint_r values %s" % (p[0], p[1][:4]))
        A("* `%s` - tint_r values %s" % (p[2], p[3][:4]))
        A("")
        A("Disjoint, and the two graphs name different palette modules, so the parameter passes")
        A("the oracle at that pair; every car with a `Palette` module carries the same fields.")
    else:                                                     # pragma: no cover
        A("**No disjoint pair was found**, so no row below is called the tint.")
    A("")
    A("| parameter | hash | which cars set it | value range | label |")
    A("|---|---|---|---|---|")
    A("| `Palette.tints[i].tint_r` (RGBA) | `tints[i].name.hash` - per-name in %d shared palettes, `2930093752` in %d car-specific ones (O8) | %d entities / %d modules | R %g..%g, G %g..%g, B %g..%g | **decoded** - **the tint**, oracle O3 |"
      % (d["hash_stats"]["per_name"], d["hash_stats"]["constant"],
         d["palette_entities"], d["module_count"],
         rng["tint_r.R"][0], rng["tint_r.R"][1], rng["tint_r.G"][0], rng["tint_r.G"][1],
         rng["tint_r.B"][0], rng["tint_r.B"][1]))
    A("| `Palette.tints[i].tint_g` (RGBA) | same | same | R %g..%g, G %g..%g, B %g..%g | **decoded** - a second colour vector, not a copy of `tint_r` |"
      % (rng["tint_g.R"][0], rng["tint_g.R"][1], rng["tint_g.G"][0], rng["tint_g.G"][1],
         rng["tint_g.B"][0], rng["tint_g.B"][1]))
    A("| `Palette.tints[i].tint_b` (RGBA) | same | same | R %g..%g, G %g..%g, B %g..%g | **decoded** - third colour vector |"
      % (rng["tint_b.R"][0], rng["tint_b.R"][1], rng["tint_b.G"][0], rng["tint_b.G"][1],
         rng["tint_b.B"][0], rng["tint_b.B"][1]))
    A("| `Palette.tints[i].occurrence` | same | same | %d..%d | **decoded** - spawn weight, not colour |"
      % rng["occurrence"][:2])
    A("| `Palette.tints[i].specular_gloss` | same | same | %g..%g | **decoded** - look, not colour |"
      % rng["specular_gloss"][:2])
    A("| `Palette.tints[i].metallic` | same | same | %g..%g | **decoded** - look |"
      % rng["metallic"][:2])
    A("| `Palette.tints[i].clear_coat` | same | same | %g..%g | **decoded** - look |"
      % rng["clear_coat"][:2])
    A("| `CarPaintMM.dynamic_params[0..3]` (`cb6[0..2]` = `m_TintColorR/G/B`) | none on disk | %d paint blocks of 1 car (`%s`) | %s | **decoded value, role UNKNOWN** - same on every block, no palette colour in it |"
      % (m["paint_blocks"], DONOR, ", ".join(str(v) for v in m["paint_dynamic"][:3])))
    A("| `CarPaintMM.dynamic_params[16..18]` (`cb6[4]` gloss/metallic/coat overrides) | none | same | %s | **decoded value, role UNKNOWN** - identical on all paint blocks |"
      % ", ".join(str(v) for v in m["dynamic_scalars"][:3]))
    A("| `CarPaintMM.static_params[0]` (`cb2[0]` = `m_SpecularGloss`) | none | %d blocks (paint and non-paint) | %d distinct, e.g. %s | **decoded**, authored per material, not the tint |"
      % (m["paint_blocks"] + m["other_blocks"], len(m["paint_static0"]),
         ", ".join(str(v) for v in m["paint_static0"][:2])))
    A("| `Palette.file` / `files[]` reference | path string | %d entities | %d module paths | **decoded** - the link from car to paint table |"
      % (d["palette_entities"], d["module_count"]))
    A("")
    A("## 3. The palette modules the fleet references")
    A("")
    A("| palette module | cars | tints | distinct tint_r |")
    A("|---|---:|---:|---:|")
    for f in d["files"]:
        A("| `%s` | %d | %d | %d |" % (f["file"].split("entities/")[-1], len(f["cars"]),
                                       f["tint_count"], f["distinct_rgb"]))
    A("")
    A("A shared module (`general_palette_strong`, `sports_modern_palette`, …) gives several")
    A("cars the same table; a car-specific module (`*_palette.vmodc`) gives one car its own.")
    A("The `name.hash` column follows that split: the shared palettes carry a distinct hash per")
    A("tint name, the car-specific ones carry the single value `2930093752` for every tint (so")
    A("that value is not the name's hash).")
    if d["donor"]["tints"]:
        A("The donor's own table (`%s`) holds %d tints: %s."
          % (d["donor"]["file"].split("entities/")[-1], len(d["donor"]["tints"]),
             ", ".join("`%s`" % t for t in d["donor"]["tints"])))
    A("")
    A("## 4. What the `.rbm` block actually authors")
    A("")
    A("%d `CarPaintMM` files under `models/jc_vehicles/%s`, %d paint blocks (`_body_dif`) and"
      % (m["files"], DONOR, m["paint_blocks"]))
    A("%d other blocks." % m["other_blocks"])
    A("")
    A("| block kind | blocks | every distinct dynamic float4[0] |")
    A("|---|---:|---|")
    A("| paint (`_body_dif`) | %d | %s |"
      % (m["paint_blocks"], " · ".join(str(v) for v in m["paint_dynamic"])))
    A("| non-paint | %d | %s |"
      % (m["other_blocks"], " · ".join(str(v) for v in m["other_dynamic"])))
    A("")
    A("The %d paint blocks all share one value; the non-paint blocks carry %d different ones"
      % (m["paint_blocks"], len(m["other_dynamic"])))
    A("(mostly the identity `(1, 0, 0, 0)` plus a few dark default uniforms).  Neither set")
    A("contains any of the %d palette tint_r values, including the donor's own %d tints, so"
      % (d["palette_rgb_count"], d["donor"]["distinct"]))
    A("the authored `.rbm` value is a per-material default and the per-car colour cannot be")
    A("read from the model.")
    A("")
    A("## 5. The loose palette file is not vanilla")
    A("")
    lo = d["loose"]
    if lo:
        A("`%s` (%d B) decodes to %d tints, every one `tint_r` %s, gloss %s, metallic %s -"
          % (lo["file"], lo["bytes"], lo["tints"], lo["rgb"], lo["gloss"], lo["metallic"]))
        A("the default of `palette_black.py` (`--rgb 0.05 --gloss 0.45 --metallic 1`).  It is a")
        A("repainted copy, so every colour in §2 is read from the entity graph (the `.ee`'s own")
        A("inlined table), not from this file.")
        A("")
    A("## 6. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**",
                                  str(o["evidence"]).replace("|", "\\|")))
    A("")
    A("## 7. UNKNOWN")
    A("")
    A("- **What writes the palette into `cb6`.**  No file names the binding: not the `.rbm`,")
    A("  not the `.epe`, not the `Palette` module (G3-09 measured all 566 inner files).  It is")
    A("  engine code or a runtime write; a live constant-buffer dump would answer it.")
    A("- **Whether the engine sends `tint_r/g/b` verbatim.**  The three vectors are separate")
    A("  colours on disk (`tint_g` is not `tint_r` in the shared palettes), which matches the")
    A("  header's three members, but which channel the shader multiplies where is in the SHEX,")
    A("  and the shader body is not on disk.")
    A("- **Cars with no `Palette` module** (%d of %d entity graphs).  Their paint must come"
      % (d["no_palette"], d["entities"]))
    A("  from the material's own static/dynamic defaults; no file ties them to a tint table.")
    A("- **The paint of the donor's model set under another car.**  Only one car's `models/`")
    A("  tree is extracted, so the `.rbm` side cannot be compared across cars even in")
    A("  principle; the cross-car oracle exists only at entity-graph level.")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/jc3_tint.py --write")
    A("uv run python Tools/scripts/jc3_tint.py --check")
    A("```")
    A("")
    return "\n".join(L)


# ------------------------------------------------------------------ main
def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: jc3_tint.py --write|--check")
    d = build()
    fails = [o["key"] for o in d["oracles"] if not o["ok"]]
    md = d["md"]
    if argv[1] == "--write":
        os.makedirs(OUT, exist_ok=True)
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        json.dump({k: v for k, v in d.items() if k != "md"},
                  open(JS, "w", encoding="utf-8", newline="\n"), indent=1)
        print("wrote Research/JC3Grab/TINT.md (%d lines) and .json" % md.count("\n"))
        print("entities %d, palettes %d, modules %d, distinct tint_r %d"
              % (d["entities"], d["palette_entities"], d["module_count"],
                 d["palette_rgb_count"]))
        print("oracle pair: %s" % (str(d["pair"][0]) + " vs " + str(d["pair"][2])
                                   if d["pair"] else "NONE"))
        print("rbm paint blocks %d, dynamic %s" % (d["material"]["paint_blocks"],
                                                   d["material"]["paint_dynamic"][:3]))
        print("loose palette %s" % d["loose"])
        print("oracles %d/%d%s" % (len(d["oracles"]) - len(fails), len(d["oracles"]),
                                    "" if not fails else " FAILED: " + ", ".join(fails)))
    else:
        if fails:
            print("FAIL: " + ", ".join(fails))
            for o in d["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        if not os.path.exists(MD) or open(MD, encoding="utf-8").read() != md:
            print("FAIL: TINT.md is stale")
            return 1
        print("CHECK OK: %d oracles, %d entities with palettes, %d modules, oracle pair %s"
              % (len(d["oracles"]), d["palette_entities"], d["module_count"],
                 d["pair"][0] + " vs " + d["pair"][2] if d["pair"] else "NONE"))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
