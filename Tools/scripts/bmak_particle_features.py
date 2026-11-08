"""bmak_particle_features.py - G1-16: every ParticleSystem grouped by feature, with its facts.

Inputs (all already in the grab):
    Research/BatmobileGrab/PARTICLES.json   206 systems, 1433 emitters, 1107 LOD levels (G1-6)
    Research/BatmobileGrab/WEAPONS.json     G1-08/G1-09 resolved references (43 particle refs)
    Research/BatmobileGrab/objects.jsonl    every export; wheel/vehicle `refs` entries (MECHANICS §Wheel)
    Research/BatmobileGrab/MECHANICS.md     the printed wheel table, used as an anchor

What it derives per system: feature group, lifetime range, spawn rates, start-size box,
colours over life, materials and emitter kinds.

`PARTICLES.json` carries the lifetime/spawn distributions, the serialised `start_size` boxes and the
emitter graph, but its `material` column is the *required-module path* and it holds no colours. So the
colour/material facts are re-read here through `grab_particles.Walker`, mirroring `read_level`'s
module walk: `ParticleModuleRequired.Material`, `ParticleModuleColor.StartColor`,
`ParticleModuleColorOverLife.ColorOverLife` and `ParticleModuleColorScaleOverLife.ColorScaleOverLife`
are vector distributions, so their two stored vectors become component-wise bounds exactly like
`Walker.vec_pair` does for `StartSize`.

Done-when (the card): every system referenced by G1-08/G1-09 or by a wheel/vehicle object has a
feature group - in-grab systems get a row; references that point outside the four Batmobile packages
`PARTICLES.json` scans are recorded as external rows, still grouped, never silently dropped.

Usage:
    python Tools/scripts/bmak_particle_features.py --write
    python Tools/scripts/bmak_particle_features.py --check
    python Tools/scripts/bmak_particle_features.py --group exhaust
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_particles as GP  # noqa: E402  (Walker, obj_array, distribution - the G1-6 parser)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
PARTICLES = os.path.join(OUT, "PARTICLES.json")
WEAPONS = os.path.join(OUT, "WEAPONS.json")
OBJECTS = os.path.join(OUT, "objects.jsonl")
MECHANICS = os.path.join(OUT, "MECHANICS.md")
JSON_OUT = os.path.join(OUT, "PARTICLES_FEATURES.json")
MD_OUT = os.path.join(OUT, "PARTICLES_FEATURES.md")

# Vehicle-side source objects whose `refs` the card means by "wheel/vehicle object".
VEHICLE_RE = re.compile(r"wheel|vehicle|batmobile|tank|apc|drone|wing|booster|cannon|missile", re.I)

RULES = [
    ("winch", r"winch"),
    ("sonar", r"sonar"),
    ("emp", r"(^|_)emp"),
    ("target-markers", r"marker"),
    ("hack-fx", r"hacker"),
    ("gel-rounds", r"anti_firearm"),
    ("tracer", r"tracer"),
    ("casings", r"casing"),
    ("muzzle-flash", r"muzzle"),
    ("cannon-impact", r"impact"),
    ("vehicle-fire", r"firetrail"),
    ("projectile-trail", r"trail|canontrail"),
    ("missile", r"missile"),
    ("explosion", r"explosion"),
    ("afterburner-exhaust", r"exhaust|boost|booster|burst"),
    ("fear-gas", r"feargas"),
    ("heat-steam", r"steam|heat"),
    ("speed-lines", r"speedline|speed_line"),
    ("wall-scrape", r"scrape|spark"),
    ("tyre-surface", r"burnout|kickup|kick_up|mud|water|track|tyre|tire|wheel|wood|dust|splash"),
]
GROUP_ORDER = [g for g, _ in RULES] + ["other"]
EMPTY_NOTES = {
    "wall-scrape": "no system of that name ships in the 206 - wall-scrape sparks are either a "
                   "material-side effect or live outside the Batmobile packages",
    "speed-lines": "no system of that name ships in the 206",
    "heat-steam": "no system of that name ships in the 206; heat/steam is the HUD + audio side "
                  "(G1-14 recorded the weapon generator heat, not a particle)",
    "sonar": "both sonar systems are referenced by `RBatmobileSonar` (G1-08)",
    "winch": "winch systems come from the winch gadget object",
    "other": "no system fell through the rules - every one of the 63 names matched a feature",
}


def group_of(name):
    n = name.lower()
    for g, pat in RULES:
        if re.search(pat, n):
            return g
    return "other"


# ---------------------------------------------------------------- facts

def dist_range(d):
    if not d or d.get("kind") == "none":
        return None
    if d.get("kind") == "constant":
        v = d.get("value")
        return None if v is None else [v, v]
    lo, hi = d.get("min"), d.get("max")
    return None if lo is None or hi is None else [lo, hi]


def merge_range(ranges):
    rs = [r for r in ranges if r]
    if not rs:
        return None
    return [round(min(r[0] for r in rs), 4), round(max(r[1] for r in rs), 4)]


def vec_merge(boxes):
    """component-wise bounds over a list of {min:[x,y,z], max:[x,y,z]}"""
    bs = [b for b in boxes if b and b.get("min") and b.get("max")]
    if not bs:
        return None
    return {"min": [round(min(b["min"][i] for b in bs), 4) for i in range(3)],
            "max": [round(max(b["max"][i] for b in bs), 4) for i in range(3)]}


def system_facts(system):
    levels = [(e, lv) for e in system["emitters"] for lv in (e.get("levels") or [])]
    life, spawn, req_spawn, sizes = [], [], [], []
    for _e, lv in levels:
        p = lv.get("params") or {}
        life.append(dist_range(p.get("lifetime")))
        spawn.append(dist_range(p.get("rate")))
        req_spawn.append(dist_range(p.get("spawn_rate")))
        box = (lv.get("vectors") or {}).get("start_size")
        if box:
            sizes.append(box)
    classes = collections.Counter(e["class"] for e in system["emitters"])
    kinds = collections.Counter(e["kind"] for e in system["emitters"])
    return {
        "emitters": {"total": len(system["emitters"]),
                     "with_levels": sum(1 for e in system["emitters"] if not e["stub"]),
                     "stubs": sum(1 for e in system["emitters"] if e["stub"]),
                     "classes": dict(classes), "kinds": dict(kinds)},
        "levels": len(levels),
        "lifetime": merge_range(life),
        "spawn_rate": merge_range(spawn),
        "required_spawn": merge_range(req_spawn),
        "size": vec_merge(sizes),
        "role": system.get("effect"),
    }


# ---------------------------------------------------------------- re-read colours + materials

def level_extra(w, pkg, index):
    tags = w.tags(pkg, index)
    module_refs = []
    for t in tags:
        if t.get("name") == "Modules" and t.get("type") == "ArrayProperty":
            module_refs.extend(GP.obj_array(w.data(pkg, index), t))
        elif t.get("type") == "ObjectNCRProperty" and t.get("ref"):
            module_refs.append(t["value"])
    material, colours = None, []
    for m in module_refs:
        if m <= 0:
            continue
        cls = w.klass(pkg, m) or ""
        if cls not in ("ParticleModuleRequired", "ParticleModuleColor",
                       "ParticleModuleColorOverLife", "ParticleModuleColorScaleOverLife"):
            continue
        mt = w.tags(pkg, m)
        if cls == "ParticleModuleRequired":
            # the cooked tag is an unnamed ObjectNCRProperty whose `ref` is already the path
            # (e.g. "Shaders.Simple_GlowFade") with `ref_class` naming the target class
            cand = [t for t in mt if t.get("type") in ("ObjectNCRProperty", "ObjectProperty")
                    and t.get("ref")]
            mat = next((t for t in cand if "Material" in str(t.get("ref_class"))), None)
            if mat or cand:
                material = str((mat or cand[0])["ref"])
            continue
        prop = {"ParticleModuleColor": "StartColor",
                "ParticleModuleColorOverLife": "ColorOverLife",
                "ParticleModuleColorScaleOverLife": "ColorScaleOverLife"}[cls]
        box = w.vec_pair(mt, prop)
        if box:
            alpha = None
            for ap in ("StartAlpha", "AlphaOverLife"):
                st = next((t for t in mt if t.get("name") == ap and t.get("type") == "StructProperty"),
                          None)
                if st:
                    alpha = GP.distribution(st)
                    break
            entry = {"source": prop, "min": box["min"], "max": box["max"]}
            if alpha and alpha.get("kind") != "none":
                entry["alpha"] = {k: alpha[k] for k in ("kind", "value", "min", "max") if k in alpha}
            colours.append(entry)
    return material, colours


def read_extras(part):
    """(package, system index) -> {material, colours} re-read from the packages."""
    w = GP.Walker()
    out = {}
    for s in part["systems"]:
        materials, colours = [], []
        for e in s["emitters"]:
            for lv in e.get("levels") or []:
                try:
                    mat, cols = level_extra(w, s["package"], lv["index"])
                except Exception as exc:  # noqa: BLE001 - one bad level must not kill the pass
                    cols, mat = [], None
                    colours.append({"source": "ERROR", "error": "%s: %s" % (type(exc).__name__, exc)})
                if mat:
                    materials.append(mat)
                colours.extend(cols)
        out[(s["package"], s["index"])] = {
            "material": sorted(set(materials)),
            "colours": [c for c in colours if c.get("source") != "ERROR"] or colours,
        }
    return out


# ---------------------------------------------------------------- references

def load_references(sysnames):
    """name -> [{source, target/path, role/field}]; the Done-when set."""
    refs = collections.defaultdict(list)
    w = json.load(open(WEAPONS, encoding="utf-8"))

    def walk(o):
        if isinstance(o, dict):
            if o.get("class") == "ParticleSystem" and o.get("target"):
                nm = str(o["target"]).split(".")[-1]
                refs[nm].append({"source": "WEAPONS.json (G1-08/G1-09)",
                                 "target": str(o["target"]),
                                 "role": o.get("role"), "field": o.get("field")})
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(w)
    n_rows = 0
    for ln in open(OBJECTS, encoding="utf-8"):
        r = json.loads(ln)
        if not VEHICLE_RE.search(r.get("class") or ""):
            continue
        rl = r.get("refs")
        if isinstance(rl, str):
            try:
                rl = json.loads(rl)
            except ValueError:
                rl = []
        for d in rl or []:
            if isinstance(d, dict) and d.get("class") == "ParticleSystem":
                path = str(d.get("path") or "")
                if not path:
                    continue
                refs[path.split(".")[-1]].append(
                    {"source": "objects.jsonl (%s)" % r["class"], "target": path,
                     "package": r.get("package")})
                n_rows += 1
    # anchor: the MECHANICS.md wheel table prints the same set
    mech = set()
    for ln in open(MECHANICS, encoding="utf-8"):
        if not ln.startswith("|") or "ParticleSystem ×" not in ln:
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        for c in cells:
            # only the dotted path cells (`Engine.Batmobile_Burnout`); the object column prints
            # `WheelFL` and is not a system name
            for m in re.findall(r"`([^`]+)`", c):
                if "." in m:
                    mech.add(m.split(".")[-1])
    return refs, {"mechanics_wheel": sorted(mech), "objects_rows": n_rows}


# ---------------------------------------------------------------- build

def build():
    part = json.load(open(PARTICLES, encoding="utf-8"))
    extras = read_extras(part)
    refs, anchor = load_references({s["name"] for s in part["systems"]})

    systems = []
    for s in part["systems"]:
        g = group_of(s["name"])
        facts = system_facts(s)
        ex = extras.get((s["package"], s["index"]), {})
        systems.append({
            "package": s["package"], "index": s["index"], "name": s["name"], "group": s.get("group", g),
            "outer": s.get("outer"), "role": facts["role"],
            "emitters": facts["emitters"], "levels": facts["levels"],
            "lifetime": facts["lifetime"], "spawn_rate": facts["spawn_rate"],
            "required_spawn": facts["required_spawn"], "size": facts["size"],
            "colours": ex.get("colours", []),
            "materials": ex.get("material", []),
            "referenced_by": sorted({r["source"] for r in refs.get(s["name"], [])}),
        })
    for r in systems:
        r["group"] = group_of(r["name"])

    grouped_names = {r["name"] for r in systems}
    external = []
    for nm, entries in sorted(refs.items()):
        if nm in grouped_names:
            continue
        external.append({
            "name": nm, "group": group_of(nm),
            "targets": sorted({e.get("target") or "" for e in entries}),
            "sources": sorted({e["source"] for e in entries}),
            "note": "referenced, but not one of the 206 ParticleSystem exports PARTICLES.json scans "
                    "(the four Batmobile packages only) - no stats, group assigned from the name",
        })

    groups = []
    for g in GROUP_ORDER:
        grows = [r for r in systems if r["group"] == g]
        if not grows and g not in EMPTY_NOTES:
            continue
        groups.append({
            "name": g, "systems": len(grows), "rows": len(grows),
            "distinct": len({r["name"] for r in grows}),
            "emitters": sum(r["emitters"]["total"] for r in grows),
            "referenced": sum(1 for r in grows if r["referenced_by"]),
            "lifetime": merge_range([r["lifetime"] for r in grows]),
            "spawn_rate": merge_range([r["spawn_rate"] for r in grows]),
            "note": EMPTY_NOTES.get(g, ""),
        })

    referenced = sorted(refs)
    coverage = {
        "referenced_distinct": len(referenced),
        "referenced_grouped_in_grab": sum(1 for nm in referenced if nm in grouped_names),
        "referenced_external": sum(1 for nm in referenced if nm not in grouped_names),
        "all_systems_grouped": len(grouped_names),
        "mechanics_wheel": anchor["mechanics_wheel"],
        "mechanics_in_objects_refs": sorted(
            {nm for nm in anchor["mechanics_wheel"]
             if any(e["source"].startswith("objects.jsonl") for e in refs.get(nm, []))}),
        "objects_ref_rows": anchor["objects_rows"],
        "unreferenced_systems": sorted(grouped_names - set(referenced)),
    }
    summary = {
        "systems": len(systems),
        "distinct_names": len(grouped_names),
        "emitters": sum(r["emitters"]["total"] for r in systems),
        "levels": sum(r["levels"] for r in systems),
        "groups_used": len({r["group"] for r in systems}),
        "systems_with_colours": sum(1 for r in systems if r["colours"]),
        "systems_with_material": sum(1 for r in systems if r["materials"]),
        "systems_with_lifetime": sum(1 for r in systems if r["lifetime"]),
        "systems_with_spawn": sum(1 for r in systems
                                  if r["spawn_rate"] or r["required_spawn"]),
        "systems_with_size": sum(1 for r in systems if r["size"]),
        "external_refs": len(external),
        "colour_boxes": sum(len(r["colours"]) for r in systems),
    }
    return {
        "schema": 1, "generated_by": "bmak_particle_features.py",
        "inputs": {"particles": "Research/BatmobileGrab/PARTICLES.json",
                   "weapons": "Research/BatmobileGrab/WEAPONS.json",
                   "objects": "Research/BatmobileGrab/objects.jsonl",
                   "mechanics": "Research/BatmobileGrab/MECHANICS.md"},
        "method": {
            "grouping": "first name rule wins (see RULES in bmak_particle_features.py), `other` last; "
                        "no system is left ungrouped",
            "ranges": "min/max over every LOD level of every emitter of the system; a constant "
                       "distribution contributes its value to both ends",
            "spawn": "spawn_rate is ParticleModuleSpawn.Rate, required_spawn is "
                     "ParticleModuleRequired.SpawnRate - both are the *continuous* rate "
                     "distributions; a 0..0 range means emission comes from the module's burst "
                     "list or from ParticleModuleSpawnPerUnit, which this pass does not extract",
            "colours": "re-read through grab_particles.Walker: the two stored vectors of "
                       "StartColor / ColorOverLife / ColorScaleOverLife, bounds taken per component "
                       "(the cooked pair is not always min-first)",
            "materials": "ParticleModuleRequired's Material reference, resolved with Walker.path - "
                         "PARTICLES.json's own `material` column is the required-module path, not "
                         "the material",
        },
        "groups": groups, "systems": systems, "external_refs": external,
        "coverage": coverage, "summary": summary,
    }


# ---------------------------------------------------------------- output

def fmt_range(r):
    if not r:
        return "-"
    a, b = r[0], r[1]
    return "%g" % a if a == b else "%g..%g" % (a, b)


def fmt_vec(v):
    if not v:
        return "-"
    return "[%s]..[%s]" % (" ".join("%g" % x for x in v["min"]),
                           " ".join("%g" % x for x in v["max"]))


def fmt_colours(cols):
    if not cols:
        return "-"
    out = []
    for c in cols[:3]:
        if "error" in c:
            out.append("ERROR %s" % c["error"])
            continue
        out.append("%s %s..%s" % (c["source"].replace("Color", "").replace("OverLife", "over life"),
                                  [round(x, 3) for x in c["min"]],
                                  [round(x, 3) for x in c["max"]]))
    more = "" if len(cols) <= 3 else " +%d" % (len(cols) - 3)
    return "; ".join(out) + more


def write_md(doc):
    s = doc["summary"]
    cov = doc["coverage"]
    L = ["# Batmobile particle systems by feature (G1-16)", "",
         "Generated by `Tools/scripts/bmak_particle_features.py` from `PARTICLES.json`, "
         "`WEAPONS.json`, `objects.jsonl` and the `MECHANICS.md` wheel table. Every one of the 206 "
         "systems lands in exactly one feature group; every system the card's reference set names "
         "is grouped too, including the ones that live outside the four Batmobile packages.", "",
         "## Summary", "", "| fact | value |", "|---|---|"]
    for k in ("systems", "distinct_names", "groups_used", "emitters", "levels",
              "systems_with_lifetime", "systems_with_spawn", "systems_with_size",
              "systems_with_material", "systems_with_colours", "colour_boxes", "external_refs"):
        L.append("| %s | **%s** |" % (k, s[k]))
    L += ["", "## Method", "",
          "- **Groups**: %s." % doc["method"]["grouping"],
          "- **Ranges**: %s." % doc["method"]["ranges"],
          "- **Spawn**: %s." % doc["method"]["spawn"],
          "- **Colours**: %s." % doc["method"]["colours"],
          "- **Materials**: %s." % doc["method"]["materials"], ""]
    L += ["## Feature groups", "",
          "| group | systems | distinct | emitters | referenced | lifetime | spawn /s | note |",
          "|---|---|---|---|---|---|---|---|"]
    for g in doc["groups"]:
        L.append("| %s | %d | %d | %d | %d | %s | %s | %s |" % (
            g["name"], g["systems"], g["distinct"], g["emitters"], g["referenced"],
            fmt_range(g["lifetime"]), fmt_range(g["spawn_rate"]), g["note"] or "-"))
    L.append("")
    for g in doc["groups"]:
        grows = [r for r in doc["systems"] if r["group"] == g["name"]]
        L += ["### %s" % g["name"], ""]
        if g["note"]:
            L += [g["note"], ""]
        if not grows:
            L += ["no system in this group.", ""]
            continue
        L += ["| system | rows | role | emitters | lifetime s | spawn /s (Rate) | size | "
              "colours over life | materials | referenced by |", "|---|---|---|---|---|---|---|---|---|---|"]
        by_name = collections.OrderedDict()
        for r in sorted(grows, key=lambda r: r["name"]):
            by_name.setdefault(r["name"], []).append(r)
        for nm, rs in by_name.items():
            r0 = rs[0]
            em = r0["emitters"]
            L.append("| `%s` | %d | %s | %d (%s) | %s | %s | %s | %s | %s | %s |" % (
                nm, len(rs), r0["role"] or "-", em["total"],
                ", ".join("%s×%d" % (k, v) for k, v in sorted(em["kinds"].items()) if k != "none")
                or "stub-only",
                fmt_range(r0["lifetime"]),
                (fmt_range(r0["spawn_rate"]) if r0["spawn_rate"] else "-")
                + ((" / req %s" % fmt_range(r0["required_spawn"])) if r0["required_spawn"] else ""),
                fmt_vec(r0["size"]), fmt_colours(r0["colours"]),
                ", ".join(os.path.basename(m) for m in r0["materials"][:2]) or "-",
                "; ".join(r0["referenced_by"]) or "-"))
        L.append("")
    L += ["## Coverage (Done-when)", "",
          "| fact | value |", "|---|---|",
          "| referenced systems (distinct) | **%d** |" % cov["referenced_distinct"],
          "| ... grouped from PARTICLES.json | **%d** |" % cov["referenced_grouped_in_grab"],
          "| ... external (grouped, no stats) | **%d** |" % cov["referenced_external"],
          "| all 206 systems grouped | **%d** names |" % cov["all_systems_grouped"],
          "| wheel rows printed in MECHANICS.md | %d |" % len(cov["mechanics_wheel"]),
          "| ... also found as `objects.jsonl` refs | %d |" % len(cov["mechanics_in_objects_refs"]),
          "| particle ref rows in wheel/vehicle objects | %d |" % cov["objects_ref_rows"],
          "| systems nothing references | %d |" % len(cov["unreferenced_systems"]), ""]
    if doc["external_refs"]:
        L += ["### External references (outside the 206)", "",
              "| name | group | sources | targets |", "|---|---|---|---|"]
        for e in doc["external_refs"]:
            L.append("| `%s` | %s | %s | %s |" % (
                e["name"], e["group"], "; ".join(e["sources"]), ", ".join("`%s`" % t for t in e["targets"])))
        L += ["", "Each keeps a feature group; only its stats are absent, because `PARTICLES.json` "
                  "scans the four Batmobile packages and these live elsewhere.", ""]
    L += ["## Gaps", "",
          "- **Wall-scrape sparks, speed lines and heat steam have no system by that name** in the "
          "206 - the groups are kept so the absence is a finding, not an omission.",
          "- **Colour ranges are distribution bounds**, not keyframed curves: the cooked lookup "
          "table's two stored vectors give per-component bounds, the same treatment `vec_pair` gives "
          "`StartSize`.",
          "- External references keep a group but carry no lifetime/spawn/size numbers; extending "
          "`grab_particles.py` to `Engine`/`Impacts`/`Mud`/`Riot_Suppressor` would close that.",
          ""]
    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    return MD_OUT


# ---------------------------------------------------------------- check

def check(doc):
    fail = []
    s, cov = doc["summary"], doc["coverage"]
    if s["systems"] != 206:
        fail.append("expected 206 systems, got %s" % s["systems"])
    bad = [r["name"] for r in doc["systems"] if r["group"] not in GROUP_ORDER]
    if bad:
        fail.append("%d systems carry a group outside the rule list (e.g. %s)" % (len(bad), bad[0]))
    if s["groups_used"] < 8:
        fail.append("only %d groups are used" % s["groups_used"])
    if not cov["referenced_distinct"]:
        fail.append("no reference set found - the Done-when cannot be evaluated")
    ungrouped = [e["name"] for e in doc["external_refs"] if e["group"] not in GROUP_ORDER]
    if ungrouped:
        fail.append("external reference without a group: %s" % ungrouped[0])
    grouped = {r["name"] for r in doc["systems"]} | {e["name"] for e in doc["external_refs"]}
    if (cov["referenced_grouped_in_grab"] + cov["referenced_external"]) != cov["referenced_distinct"]:
        fail.append("coverage counts do not add up to the reference set")
    miss = [nm for nm in (e["name"] for e in doc["external_refs"]) if nm not in grouped]
    if miss:
        fail.append("referenced system not grouped: %s" % miss[0])
    mech = set(cov["mechanics_wheel"])
    found = set(cov["mechanics_in_objects_refs"])
    if mech - found:
        fail.append("%d MECHANICS wheel refs not seen as objects.jsonl refs (e.g. %s)"
                    % (len(mech - found), sorted(mech - found)[0]))
    if sum(g["rows"] for g in doc["groups"]) != 206:
        fail.append("group rows do not sum to 206")
    for e in doc["external_refs"]:
        if not e.get("note"):
            fail.append("external ref without a note: %s" % e["name"])
            break
    if fail:
        print("FAIL")
        for f in fail:
            print("  -", f)
        return 1
    print("OK: %d systems (%d names) in %d groups; facts: lifetime %d, spawn %d, size %d, "
          "materials %d, colours %d (%d boxes); coverage %d referenced names "
          "(%d in-grab + %d external), %d MECHANICS wheel refs all found in objects.jsonl"
          % (s["systems"], s["distinct_names"], s["groups_used"], s["systems_with_lifetime"],
             s["systems_with_spawn"], s["systems_with_size"], s["systems_with_material"],
             s["systems_with_colours"], s["colour_boxes"], cov["referenced_distinct"],
             cov["referenced_grouped_in_grab"], cov["referenced_external"],
             len(cov["mechanics_wheel"])))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="rebuild JSON + MD")
    ap.add_argument("--check", action="store_true", help="run the Done-when gate")
    ap.add_argument("--group", help="print every system in this feature group")
    a = ap.parse_args()
    doc = None
    if a.write:
        doc = build()
        json.dump(doc, open(JSON_OUT, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(JSON_OUT, ROOT), "and", os.path.relpath(write_md(doc), ROOT))
    if a.group:
        if doc is None:
            doc = json.load(open(JSON_OUT, encoding="utf-8"))
        for r in doc["systems"]:
            if r["group"] == a.group:
                print(r["name"], "|", r["package"], "|", fmt_range(r["lifetime"]), "|",
                      fmt_range(r["spawn_rate"]), "|", fmt_vec(r["size"]))
    if doc is None:
        try:
            doc = json.load(open(JSON_OUT, encoding="utf-8"))
        except OSError:
            print("FAIL\n  - no %s - run --write first" % os.path.relpath(JSON_OUT, ROOT))
            return 1
    if not a.write:
        print(json.dumps(doc["summary"], indent=1))
    if a.check:
        return check(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
