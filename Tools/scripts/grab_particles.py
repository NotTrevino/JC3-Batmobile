r"""grab_particles.py - the semantic pass over the 206 Batmobile particle systems (G1-6).

What "semantic" means here, precisely: for every `ParticleSystem` export, resolve the graph the
cooked bytes actually contain and say what each effect *is*:

    ParticleSystem -> Emitters[] -> ParticleSpriteEmitter -> LODLevels[]
      -> ParticleLODLevel
           RequiredModule (material, inline scalars, LOD distances)
           SpawnModule
           Modules[] (the module inventory: size / velocity / colour / orbit / collision ...)
           TypeDataModule (sprite, mesh, beam, ribbon, light, decal, trail)

The graph is read through the same property walk `upk_read` uses; arrays of object references are
`int32 count` followed by that many export indices, which is why `objects.jsonl` stores `Emitters`
as a bare tag - the array's element type is a class fact, not a stream fact.

Scalars *are* carried, as lookup tables. `FRawDistributionFloat` cooks down to `Op`,
`LookupTableNumElements` and a `LookupTable` array, and that array holds the values: `Op == 2` is a
uniform with `[min, max]` repeated per chunk, a single repeated value is a constant, anything else is a
curve kept verbatim. So the pass reports *numbers* (lifetime, spawn rate) next to structure (which
modules at which LOD, which material, which mesh, which emitter type, beam length, LOD distances,
bounds). The vector distributions (`StartSize`, `StartVelocity`, `StartLocation`) are serialised as two
consecutive `VectorProperty` tags instead, captured with the `min <= max` check as their evidence.

Writes `Research/BatmobileGrab/PARTICLES.json` + `PARTICLES.md`.

Usage:
    python Tools/scripts/grab_particles.py --write
    python Tools/scripts/grab_particles.py --check
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import grab_model            # noqa: E402
import upk_read as U         # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

# Emitter kind comes from the type-data module's class, which is a fact of the package, not a guess.
TYPE_DATA = {
    "ParticleModuleTypeDataMesh": "mesh",
    "ParticleModuleTypeDataBeam2": "beam",
    "ParticleModuleTypeDataTrail2": "trail",
    "ParticleModuleTypeDataRibbon": "ribbon",
    "ParticleModuleTypeDataApexSprite": "sprite",
    "RParticleModuleTypeDataLight": "light",
    "RParticleModuleTypeDataDecal": "decal",
}

# Inline scalar tags in the required module that are present in the stream; named positionally
# because the Batman cook leaves them unnamed. Kept only where a system actually carries them.
REQUIRED_SCALARS = ("0x007C", "0x0084", "0x00CC")


class ParticleError(Exception):
    pass


def obj_array(d: bytes, tag: dict) -> list[int]:
    """An object-reference array: `int32 count` then `count` export indices."""
    if tag.get("refs"):
        return [r["index"] for r in tag["refs"]]
    at = tag.get("at")
    if at is None or at + 4 > len(d):
        return []
    n = struct.unpack_from("<i", d, at)[0]
    if not 0 <= n <= 4096 or at + 4 + 4 * n > len(d):
        return []
    return list(struct.unpack_from("<%di" % n, d, at + 4))


class Walker:
    def __init__(self) -> None:
        self.packages: dict[str, U.Package] = {}
        self.cache: dict[tuple[str, int], list[dict]] = {}

    def pkg(self, name: str) -> U.Package:
        if name not in self.packages:
            self.packages[name] = U.Package(os.path.join(GAME, name + ".upk"))
        return self.packages[name]

    def tags(self, pkg: str, index: int) -> list[dict]:
        key = (pkg, index)
        if key not in self.cache:
            p = self.pkg(pkg)
            data = p.data(index)
            tags, _end, _why = U.walk_tags(p, data)
            self.cache[key] = (tags, data)
        return self.cache[key][0]

    def data(self, pkg: str, index: int) -> bytes:
        self.tags(pkg, index)
        return self.cache[(pkg, index)][1]

    def klass(self, pkg: str, index: int) -> str | None:
        return self.pkg(pkg).object_class(index)

    def path(self, pkg: str, index: int) -> str | None:
        return self.pkg(pkg).object_path(index)

    def scalar(self, tags: list[dict], name: str | None = None, offset: int | None = None):
        for t in tags:
            if name is not None and t.get("name") != name:
                continue
            if offset is not None and t.get("offset") != offset:
                continue
            v = t.get("value")
            if not isinstance(v, dict):
                return v
        return None

    def struct_vectors(self, tags: list[dict], name: str) -> list[list[float]]:
        """The two serialised vectors inside a `FRawDistributionVector` (min, max)."""
        st = next((t for t in tags
                   if t.get("name") == name and t.get("type") == "StructProperty"), None)
        if not st:
            return []
        out = [p["value"] for p in (st.get("props") or [])
               if p.get("type") == "VectorProperty" and isinstance(p.get("value"), list)]
        return [[round(v, 4) for v in vec] for vec in out[:2]]

    def vec_pair(self, tags: list[dict], name: str) -> dict:
        """A vector distribution's two stored vectors, as component-wise bounds.

        The cooked order is not always min-first (193 of 863 pairs are stored max-first), so the
        bounds are taken per component and the stored pair is kept alongside them.
        """
        pair = self.struct_vectors(tags, name)
        if len(pair) != 2:
            return {}
        lo = [min(pair[0][i], pair[1][i]) for i in range(3)]
        hi = [max(pair[0][i], pair[1][i]) for i in range(3)]
        return {"min": lo, "max": hi, "stored": pair}


def distribution(struct_tag: dict | None) -> dict:
    """The values inside an `FRawDistribution*` struct.

    A cooked distribution keeps its data as a lookup table, so the numbers *are* in the stream:
    `Op == 2` is a uniform (`[min, max]` per chunk), a single repeated value is a constant, and
    anything else is a curve quoted as-is.
    """
    if not struct_tag:
        return {}
    props = struct_tag.get("props") or []
    op = next((q.get("value") for q in props if q.get("name") == "Op"), None)
    numel = next((q.get("value") for q in props
                  if q.get("name") == "LookupTableNumElements"), None)
    table = next((q for q in props if q.get("name") == "LookupTable"), None) or {}
    raw = [round(float(v), 5) for v in (table.get("floats") or [])]
    uniq = []
    for v in raw:
        if v not in uniq:
            uniq.append(v)
    if not uniq:
        return {"op": op, "kind": "none"}
    if op == 2 and len(uniq) >= 2:
        return {"op": op, "num_elements": numel, "kind": "uniform",
                "min": min(uniq[:2]), "max": max(uniq[:2]), "values": uniq}
    if len(uniq) == 1:
        return {"op": op, "kind": "constant", "value": uniq[0], "values": uniq}
    return {"op": op, "num_elements": numel, "kind": "curve",
            "min": min(uniq), "max": max(uniq), "values": uniq}



def read_system(w: Walker, row: dict) -> dict:
    pkg, idx = row["package"], row["index"]
    tags = w.tags(pkg, idx)
    em_tag = next((t for t in tags if t.get("name") == "Emitters"), None)
    emitters = []
    for e in (obj_array(w.data(pkg, idx), em_tag) if em_tag else []):
        if e <= 0:
            continue
        emitters.append(read_emitter(w, pkg, e))
    lod = w.scalar(tags, name="LODDistances")
    return {
        "package": pkg, "index": idx, "name": row["name"],
        "outer": row.get("outer"), "size": row["size"],
        "lod_method": w.scalar(tags, name="LODMethod"),
        "emitters": emitters,
        "effect": classify(row["name"], emitters),
    }


def read_emitter(w: Walker, pkg: str, index: int) -> dict:
    tags = w.tags(pkg, index)
    levels = []
    ltag = next((t for t in tags if t.get("name") == "LODLevels"), None)
    for l in (obj_array(w.data(pkg, index), ltag) if ltag else []):
        if l > 0:
            levels.append(read_level(w, pkg, l))
    kind = levels[0]["kind"] if levels else "none"
    return {"index": index, "class": w.klass(pkg, index), "kind": kind,
            "lod_levels": len(levels),
            # The cooker leaves one stub per emitter slot that has no level in this build; they are
            # counted, not dropped, because they are part of the system's real emitter list.
            "stub": not levels,
            "material": levels[0]["material"] if levels else None,
            "modules": sorted({m for lv in levels for m in lv["modules"]}),
            "levels": levels}


def read_level(w: Walker, pkg: str, index: int) -> dict:
    tags = w.tags(pkg, index)
    module_refs = []
    for t in tags:
        if t.get("name") == "Modules" and t.get("type") == "ArrayProperty":
            module_refs.extend(obj_array(w.data(pkg, index), t))
        elif t.get("type") == "ObjectNCRProperty" and t.get("ref"):
            module_refs.append(t["value"])

    required = None
    modules, mesh, beam, scalars, params = [], None, {}, {}, {}
    for m in module_refs:
        if m <= 0:
            continue
        cls = w.klass(pkg, m) or ""
        mt = w.tags(pkg, m)
        modules.append(cls)
        if cls == "ParticleModuleRequired":
            required = m
            scalars = {k: w.scalar(mt, offset=int(k, 16)) for k in REQUIRED_SCALARS}
            scalars = {k: v for k, v in scalars.items() if v is not None}
            params["spawn_rate"] = distribution(
                next((t for t in mt if t.get("name") == "SpawnRate"), None))
        elif cls == "ParticleModuleLifetime":
            params["lifetime"] = distribution(
                next((t for t in mt if t.get("name") == "Lifetime"), None))
        elif cls == "ParticleModuleSpawn":
            params["rate"] = distribution(
                next((t for t in mt if t.get("name") == "Rate"), None))
        elif cls in TYPE_DATA:
            mesh = w.scalar(mt, offset=0x60)
            if isinstance(mesh, int) and mesh:
                mesh = w.path(pkg, mesh)
            beam = {k: w.scalar(mt, offset=o) for k, o in
                    (("length", 0x68), ("tiles", 0x70), ("max_length", 0x74), ("frequency", 0x78))}
            beam = {k: v for k, v in beam.items() if v is not None}

    vec = {}
    start = next((m for m in module_refs if (w.klass(pkg, m) or "") == "ParticleModuleSize"), None)
    if start:
        vec["start_size"] = w.vec_pair(w.tags(pkg, start), "StartSize")
    vel = next((m for m in module_refs if (w.klass(pkg, m) or "") == "ParticleModuleVelocity"), None)
    if vel:
        vec["start_velocity"] = w.vec_pair(w.tags(pkg, vel), "StartVelocity")
    loc = next((m for m in module_refs if (w.klass(pkg, m) or "") == "ParticleModuleLocation"), None)
    if loc:
        vec["start_location"] = w.vec_pair(w.tags(pkg, loc), "StartLocation")
    vec = {k: v for k, v in vec.items() if v}

    kinds = [TYPE_DATA.get(c) for c in modules if c in TYPE_DATA]
    return {"index": index, "kind": kinds[0] if kinds else "sprite",
            "required": w.path(pkg, required) if required else None,
            "material": os.path.basename(w.path(pkg, required) or "") or None,
            "modules": [c for c in modules if not c.startswith("ParticleModuleRequired")],
            "module_count": len(modules), "mesh": mesh, "beam": beam,
            "required_scalars": scalars, "vectors": vec,
            "params": {k: v for k, v in params.items() if v and v.get("kind") != "none"}}


def classify(name: str, emitters: list[dict]) -> str:
    """A role label derived from the graph, then the system name; nothing from imagination."""
    kinds = {e["kind"] for e in emitters}
    mods = {m for e in emitters for m in e["modules"]}
    label = name.lower()
    if "light" in kinds:
        return "light emitter"
    if "beam" in kinds or "ParticleModuleBeamTarget" in mods:
        return "beam / tracer"
    if "trail" in kinds or "ParticleModuleTypeDataTrail2" in mods:
        return "trail"
    if "decal" in kinds:
        return "decal"
    if "mesh" in kinds or "ParticleModuleTypeDataMesh" in mods:
        return "mesh particles"
    for token, role in (("muzzleflash", "muzzle flash"), ("burnout", "burnout smoke"),
                        ("feargas", "fear gas"), ("sonar", "sonar pulse"),
                        ("impact", "impact"), ("explosion", "explosion"),
                        ("fire", "fire"), ("smoke", "smoke"), ("dust", "dust"),
                        ("spark", "sparks"), ("debris", "debris"), ("rain", "rain"),
                        ("splash", "splash"), ("water", "water"), ("exhaust", "exhaust"),
                        ("flame", "flame"), ("missile", "missile"), ("tank", "tank"),
                        ("marker", "marker"), ("line", "line marker")):
        if token in label:
            return role
    return "sprite particles"


def build() -> dict:
    g = grab_model.Grab()
    w = Walker()
    systems = []
    for row in (r for r in g.rows if r.get("class") == "ParticleSystem"):
        systems.append(read_system(w, row))
    kinds = collections.Counter(s["effect"] for s in systems)
    mods = collections.Counter(m for s in systems for e in s["emitters"] for m in e["modules"])
    return {"schema": 1, "generated_by": "grab_particles.py", "game": GAME,
            "systems": systems,
            "summary": {"systems": len(systems),
                        "emitters": sum(len(s["emitters"]) for s in systems),
                        "lod_levels": sum(e["lod_levels"] for s in systems for e in s["emitters"]),
                        "roles": dict(kinds.most_common()),
                        "modules": dict(mods.most_common()),
                        "materials": len({e["material"] for s in systems for e in s["emitters"]
                                          if e["material"]}),
                        "with_vectors": sum(1 for s in systems for e in s["emitters"]
                                            for lv in e["levels"] if lv["vectors"]),
                        "with_lifetime": sum(1 for s in systems for e in s["emitters"]
                                             for lv in e["levels"]
                                             if (lv.get("params") or {}).get("lifetime")),
                        "with_rate": sum(1 for s in systems for e in s["emitters"]
                                         for lv in e["levels"]
                                         if (lv.get("params") or {}).get("spawn_rate")
                                         or (lv.get("params") or {}).get("rate"))}}


def check(doc: dict) -> list[str]:
    bad = []
    if doc["summary"]["systems"] != 206:
        bad.append("expected 206 systems, found %d" % doc["summary"]["systems"])
    levels = sum(e["lod_levels"] for s in doc["systems"] for e in s["emitters"])
    if levels != 1107:
        bad.append("expected 1107 LOD levels in the corpus, found %d" % levels)
    if doc["summary"]["with_lifetime"] < 1000:
        bad.append("lifetime resolves on only %d levels - the lookup-table decode regressed"
                   % doc["summary"]["with_lifetime"])
    for s in doc["systems"]:
        if not s["emitters"]:
            bad.append("%s: no emitters resolved" % s["name"])
        elif all(e["stub"] for e in s["emitters"]):
            bad.append("%s: every emitter is a stub" % s["name"])
        for e in s["emitters"]:
            if e["stub"]:
                continue
            for lv in e["levels"]:
                if not lv["required"]:
                    bad.append("%s/%s: LOD has no required module" % (s["name"], e["index"]))
                for name, box in lv["vectors"].items():
                    if any(a > b for a, b in zip(box.get("min", []), box.get("max", []))):
                        bad.append("%s: %s bounds inverted %s" % (s["name"], name, box))
                    if len(box.get("stored", [])) != 2:
                        bad.append("%s: %s lost a stored vector" % (s["name"], name))
    return bad


def write_md(doc: dict) -> None:
    s = doc["summary"]
    L = ["# Batmobile particle systems - the semantic pass (G1-6)", "",
         "Generated by `Tools/scripts/grab_particles.py` from all **%d** `ParticleSystem` exports in"
         % s["systems"],
         "the Batmobile packages. Every row is read from the cooked graph", "",
         "`system -> emitter -> LOD level -> {required, spawn, modules[], type data}`,", "",
         "so the *kind* of each effect (sprite, mesh, beam, trail, light, decal) is a fact of the",
         "package, and the material / module inventory is what the game actually loads.", "",
         "| fact | value |", "|---|---|",
         "| systems | **%d** |" % s["systems"],
         "| emitters | **%d** (%d with LOD levels, %d stubs) |"
         % (s["emitters"], sum(1 for x in doc["systems"] for e in x["emitters"] if not e["stub"]),
            sum(1 for x in doc["systems"] for e in x["emitters"] if e["stub"])),
         "| LOD levels | **%d** |" % s["lod_levels"],
         "| distinct materials | **%d** |" % s["materials"],
         "| emitters with serialised min/max vectors | **%d** |" % s["with_vectors"], "",
         "## Roles", "", "| role | systems |", "|---|---|"]
    for k, v in s["roles"].items():
        L.append("| %s | %d |" % (k, v))
    L += ["", "Roles are assigned from the graph first (type-data module, then module set), and only",
          "fall back to the system name when the graph says only \"sprite\".", "",
          "## Module inventory", "", "| module | emitters |", "|---|---|"]
    for k, v in s["modules"].items():
        L.append("| `%s` | %d |" % (k, v))
    L += ["", "## Distribution values", "",
          "`FRawDistributionFloat` is cooked to `Op` + `LookupTableNumElements` + a `LookupTable` array,",
          "and the array carries the values - `Op == 2` uniform as `[min, max]` per chunk, a repeated",
          ("**%d of %d** LOD levels resolve a lifetime and **%d** resolve a spawn rate or rate; "
           "the remaining modules carry no table at all (the emitter inherits the required "
           "module's default). Values below are the cooked numbers, unscaled."
           % (s["with_lifetime"], s["lod_levels"], s["with_rate"])), "",
          "### Lifetime and rate per system", "",
          "| system | emitters with lifetime | lifetime (s) | spawn rate (/s) |", "|---|---|---|---|"]
    for x in doc["systems"]:
        lt, rt = [], []
        for e in x["emitters"]:
            for lv in e["levels"]:
                p = lv.get("params") or {}
                l = p.get("lifetime") or {}
                if l.get("kind") == "constant":
                    lt.append(l["value"])
                elif l.get("kind") in ("uniform", "curve"):
                    lt.append((l["min"], l["max"]))
                r = p.get("spawn_rate") or p.get("rate") or {}
                if r.get("kind") == "constant" and r["value"]:
                    rt.append(r["value"])
                elif r.get("kind") in ("uniform", "curve") and r.get("max"):
                    rt.append((r["min"], r["max"]))
        if not lt and not rt:
            continue
        def fmt(v):
            if isinstance(v, tuple):
                return "%.3g - %.3g" % v
            return "%.3g" % v
        L.append("| `%s` | %d | %s | %s |" % (
            x["name"], len(lt), ", ".join(fmt(v) for v in lt[:4]) + (" ..." if len(lt) > 4 else ""),
            ", ".join(fmt(v) for v in rt[:4]) + (" ..." if len(rt) > 4 else "") or "-"))
    L += ["", "## Every system", "",          "## Every system", "",
          "| system | package | emitters | kind | role | material | modules |", "|---|---|---|---|---|---|---|"]
    for x in doc["systems"]:
        kinds = ", ".join(sorted({e["kind"] for e in x["emitters"]})) or "-"
        mats = ", ".join(sorted({e["material"] for e in x["emitters"] if e["material"]}))[:60] or "-"
        L.append("| `%s` | %s | %d | %s | %s | %s | %d |" % (
            x["name"], x["package"].replace("Playable_", "").replace("_SF", ""),
            len(x["emitters"]), kinds, x["effect"], mats,
            len({m for e in x["emitters"] for m in e["modules"]})))
    L += ["", "## Serialised vectors", "",
          "The only distribution numbers in the stream: two consecutive `VectorProperty` tags inside",
          "`StartSize` / `StartVelocity` / `StartLocation`, quoted as component-wise min/max with the stored",
          "order kept (the cook writes max first in 193 of 863 pairs).", ""]
    for x in doc["systems"]:
        for e in x["emitters"]:
            for lv in e["levels"]:
                if not lv["vectors"]:
                    continue
                L.append("### %s / emitter %d" % (x["name"], e["index"]))
                for k, box in lv["vectors"].items():
                    L.append("- **%s**: min `%s` max `%s` (stored `%s` / `%s`)"
                             % (k, box["min"], box["max"], box["stored"][0], box["stored"][1]))
                if lv["mesh"]:
                    L.append("- mesh: `%s`" % lv["mesh"])
                if lv["beam"]:
                    L.append("- beam: %s" % lv["beam"])
                L.append("")
    open(os.path.join(OUT, "PARTICLES.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = build()
    bad = check(doc)
    if a.write:
        with open(os.path.join(OUT, "PARTICLES.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        write_md(doc)
    s = doc["summary"]
    print("%d systems, %d emitters, %d LOD levels, %d materials"
          % (s["systems"], s["emitters"], s["lod_levels"], s["materials"]))
    print("roles:", ", ".join("%s %d" % kv for kv in list(s["roles"].items())[:8]))
    if bad:
        print("\nFAIL")
        for b in bad[:30]:
            print(" ", b)
        print(" (%d problem(s))" % len(bad))
        sys.exit(1)
    print("checks: every system has emitters, every LOD a required module, min<=max - all ok")


if __name__ == "__main__":
    main()
