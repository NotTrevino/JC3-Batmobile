"""Read-only fact chaser for the T-2 assumption challenge (Research/challenge/T2_TRANSLATION.md).

Every sub-command prints the values a claim in `Working/Translation/T2_TRANSLATION.md` rests on,
computed from files on disk. Nothing is written; no archive is opened; `D:/Games` is never read.

    python Tools/scripts/chase/ch_t2_claims.py damage
    python Tools/scripts/chase/ch_t2_claims.py lights
    python Tools/scripts/chase/ch_t2_claims.py parts
    python Tools/scripts/chase/ch_t2_claims.py physics
    python Tools/scripts/chase/ch_t2_claims.py audio
    python Tools/scripts/chase/ch_t2_claims.py build
    python Tools/scripts/chase/ch_t2_claims.py index
    python Tools/scripts/chase/ch_t2_claims.py all

Inputs: E:/Modding/_shared/gamedata/JC3grab/entities/*.json (module rows), Research/JC3Grab/PARTS_TABLE.jsonl,
Research/BatmobileGrab/{LIGHTS,PHYSICS,SLOTS,VALUES,grab}.json, Working/Translation/current.json.
"""
import collections
import glob
import json
import os
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
GRAB = "E:/Modding/_shared/gamedata/JC3grab"
ENTS = os.path.join(GRAB, "entities")
DONOR = "sportsmuscle_civilian_01"


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def entity_files():
    return sorted(glob.glob(os.path.join(ENTS, "*.json")))


def klass(path):
    n = path.lower()
    for word, k in (("_boat", "boat"), ("boat_", "boat"), ("helicopter", "heli"),
                    ("_plane", "plane"), ("plane_", "plane"), ("_jet", "plane"),
                    ("_train", "train"), ("_bike", "bike"), ("snowmobile", "bike"),
                    ("_quad", "bike"), ("_tank", "land"), ("_apc", "land")):
        if word in n:
            return k
    return "land"


def modules(path):
    d = json.load(open(path, encoding="utf-8"))
    out = {}
    for m in d.get("modules", []):
        if m.get("type") and isinstance(m.get("rows"), list):
            out.setdefault(m["type"], []).append(m)
    return out


def rows_of(mods, typ):
    rows = {}
    for m in mods.get(typ, []):
        for r in m["rows"]:
            if "path" in r:
                rows[r["path"]] = r.get("value")
    return rows


def fleet(typ):
    """(entity, class, rows) for every entity that decodes `typ`."""
    for p in entity_files():
        mods = modules(p)
        if typ in mods:
            yield p, klass(p), rows_of(mods, typ)


def fmt(x):
    if isinstance(x, float) and x == int(x):
        return int(x)
    return x


def hist(values):
    c = collections.Counter(fmt(v) for v in values)
    return dict(sorted(c.items(), key=lambda kv: (kv[0] is None, kv[0])))


def cmd_damage():
    print("## VehicleDamage over every decoded entity\n")
    per = collections.defaultdict(list)
    scales = collections.defaultdict(list)
    for p, k, r in fleet("VehicleDamage"):
        per["max_health"].append((r.get("max_health"), os.path.basename(p), k))
        per["bullet_armor_strength"].append(r.get("bullet_armor_strength"))
        per["bullet_heavy_armor_strength"].append(r.get("bullet_heavy_armor_strength"))
        per["explosion_threshold"].append(r.get("explosion_threshold"))
        per["smoke_threshold"].append(r.get("smoke_threshold"))
        per["burn_threshold"].append(r.get("burn_threshold"))
        scales[r.get("deform_scale")].append(os.path.basename(p))
    hp = [h for h, _, _ in per["max_health"] if isinstance(h, (int, float))]
    print(f"entities with VehicleDamage: {len(per['max_health'])}")
    print(f"max_health: min {min(hp)} max {max(hp)} median {statistics.median(hp)} "
          f"distinct {len(set(hp))}")
    top = sorted(per["max_health"], key=lambda t: -(t[0] or 0))[:8]
    print("max_health top rows:", [(h, e, k) for h, e, k in top])
    land = [h for h, _, k in per["max_health"] if k == "land" and isinstance(h, (int, float))]
    print(f"land-only max_health: n {len(land)} min {min(land)} max {max(land)} "
          f"median {statistics.median(land)}")
    for m in ("bullet_armor_strength", "bullet_heavy_armor_strength", "explosion_threshold",
              "smoke_threshold", "burn_threshold"):
        vals = [v for v in per[m] if isinstance(v, (int, float))]
        print(f"{m}: min {min(vals)} max {max(vals)} median {statistics.median(vals)} "
              f"at-max {sum(1 for v in vals if v == max(vals))}")
    print("\n### deform_scale")
    for v, ents in sorted(scales.items(), key=lambda kv: -len(kv[1])):
        print(f"  {fmt(v)!r}: {len(ents)} entities, e.g. {ents[:3]}")
    print("\n### part_damage_types type strings across the fleet")
    strings = collections.Counter()
    fleets = collections.Counter()
    for p in entity_files():
        mods = modules(p)
        if "VehicleDamage" not in mods:
            continue
        seen = set()
        for m in mods["VehicleDamage"]:
            for r in m["rows"]:
                key = r.get("path", "")
                if key.endswith(".type.string"):
                    seen.add(r.get("value"))
        for s in seen:
            strings[s] += 1
            fleets[s] += 0
    print(f"distinct type strings: {len(strings)}")
    for s, n in sorted(strings.items(), key=lambda kv: -kv[1]):
        print(f"  {s!r} on {n} entities")
    for probe in ("Boat_Antenna", "Land_Antenna", "Default"):
        print(f"  probe {probe!r}: {strings.get(probe, 0)} entities")
    print("\n### donor part rows (PARTS_TABLE.jsonl)")
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "Research", "JC3Grab",
                                                     "PARTS_TABLE.jsonl"), encoding="utf-8")]
    don = [r for r in rows if DONOR in r["entity"]]
    for d in don:
        dt = collections.Counter(pd["dt"] for pd in d["parts"])
        print(f"  {d['entity'].rsplit('/', 1)[-1]}: {len(d['parts'])} parts, "
              f"{len(dt)} distinct dt")
        for k, n in dt.most_common():
            print(f"    {k}: {n}")
        cm = [pd for pd in d["parts"] if "mirror" in pd["n"]]
        print("    mirror rows:", [(pd["n"], pd["dt"]) for pd in cm])
        print("    wheels:", d["wheels"], "doors:", d["doors"])


def cmd_lights():
    print("## BmAK LIGHTS.json")
    d = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.json"),
                       encoding="utf-8"))
    print("keys:", list(d))
    print("summary:", json.dumps(d.get("summary"), indent=1)[:1200])
    print("by_part:", json.dumps(d.get("by_part") or d.get("parts"), indent=1)[:600])
    rigs = d.get("rigs") or d.get("packages") or {}
    if isinstance(rigs, dict):
        for k, v in rigs.items():
            n = len(v.get("entries", [])) if isinstance(v, dict) else len(v)
            print(f"  rig {k}: {n}")
    print("\n## fleet light rows from the entity cache")
    rng, ang, mult = [], [], []
    beh = collections.Counter()
    for p in entity_files():
        mods = modules(p)
        if "VehicleDynamicLights" not in mods:
            continue
        for m in mods["VehicleDynamicLights"]:
            for r in m["rows"]:
                key = r.get("path", "")
                if key.endswith(".range"):
                    rng.append(r.get("value"))
                elif key.endswith(".angle"):
                    ang.append(r.get("value"))
                elif key.endswith(".multiplier"):
                    mult.append(r.get("value"))
                elif key.endswith(".behavior"):
                    beh[r.get("value")] += 1
    for name, vals in (("range", rng), ("angle", ang), ("multiplier", mult)):
        v = [x for x in vals if isinstance(x, (int, float))]
        print(f"{name}: n {len(v)} min {min(v)} max {max(v)} median {statistics.median(v)}")
    print("behavior:", dict(beh))


def cmd_parts():
    print("## donor .epe graph objects (detail cache)")
    p = glob.glob(os.path.join(GRAB, "detail", f"*{DONOR}.ee.json"))
    print("detail file:", p)
    if p:
        d = json.load(open(p[0], encoding="utf-8"))
        print("keys:", list(d)[:12])
        objs = d.get("objects") or d.get("graph") or []
        if isinstance(objs, dict):
            objs = objs.get("objects", [])
        cls = collections.Counter(o.get("_class") or o.get("class") for o in objs
                                  if isinstance(o, dict))
        print("object classes:", dict(cls))
        print("CPartProp:", cls.get("CPartProp"))
        print("SVehicleLight:", cls.get("SVehicleLight"))
    print("\n## donor part rows vs the graph")
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "Research", "JC3Grab",
                                                     "PARTS_TABLE.jsonl"), encoding="utf-8")]
    don = [r for r in rows if DONOR in r["entity"]][0]
    parts = don["parts"]
    print(f"parts module rows: {len(parts)}")
    print(f"has_world_collision_shape=1: {sum(1 for x in parts if x['body'] not in (-1, None))}")
    print(f"world_collision_body_id -1: {sum(1 for x in parts if x['body'] == -1)}")
    print("wheels:", don["wheels"])
    print("doors:", don["doors"])
    print("parts with lights (deform flag):",
          [(x["i"], x["n"]) for x in parts if x.get("lights") == 1][:30])
    print("parts with deform=1:", sum(1 for x in parts if x.get("deform") == 1))
    print("\n## DeformPoints of the donor")
    p = glob.glob(os.path.join(ENTS, f"*{DONOR}.ee.json"))[0]
    mods = modules(p)
    dp = rows_of(mods, "DeformPoints")
    print("DeformPoints members:", len(dp))
    for k in sorted(dp):
        if "constraint" in k or "non_deformable" in k or "light" in k or "part" in k:
            v = dp[k]
            print(f"  {k}: {len(v) if isinstance(v, list) else v}")


def cmd_physics():
    print("## PHYSICS.json")
    d = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "PHYSICS.json"),
                       encoding="utf-8"))
    for pkg, v in d.items():
        if not isinstance(v, dict):
            print(pkg, type(v))
            continue
        bodies = v.get("bodies") or v.get("body_setups") or []
        shapes = collections.Counter(b.get("shape") or b.get("type") for b in bodies
                                     if isinstance(b, dict))
        print(f"{pkg}: {len(bodies)} bodies shapes {dict(shapes)}")
        boxes = [b.get("extents") or b.get("size") for b in bodies
                 if isinstance(b, dict) and (b.get("extents") or b.get("size"))]
        if boxes:
            big = max(boxes, key=lambda e: max(e))
            print(f"  largest extents by max axis: {big}")
            print(f"  largest by volume: {max(boxes, key=lambda e: e[0]*e[1]*e[2])}")
        root = [b for b in bodies if isinstance(b, dict) and
                (b.get("bone") in ("Root", 0) or b.get("name") == "Root")]
        if root:
            print("  root body:", json.dumps(root[0])[:300])


def cmd_audio():
    print("## AUDIO_MAP.json")
    d = json.load(open(os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json"),
                       encoding="utf-8"))
    print("keys:", list(d)[:14])
    for k, v in d.items():
        if isinstance(v, (int, float)) or isinstance(v, str):
            print(f"  {k}: {v}")
        elif isinstance(v, list):
            print(f"  {k}: list[{len(v)}]")
        elif isinstance(v, dict):
            print(f"  {k}: dict[{len(v)}]")
    banks = d.get("banks")
    if isinstance(banks, dict):
        sizes = [(k, (v.get("bytes") if isinstance(v, dict) else None))
                 for k, v in banks.items()]
        print("banks with missing file:", [k for k, b in sizes if b in (None, 0)])
    print("\n## vehicles.bank on disk (decoded game data, outside the repo)")
    for base in (os.path.join(GRAB, "sound", "fmod_banks"),
                 os.path.join(GRAB, "sound")):
        f = os.path.join(base, "vehicles.bank")
        print(f"  {f}: {os.path.getsize(f) if os.path.exists(f) else 'absent'}")
    print("\n## LandAudio / LandEngine in the donor")
    p = glob.glob(os.path.join(ENTS, f"*{DONOR}.ee.json"))[0]
    mods = modules(p)
    print("  LandAudio:", rows_of(mods, "LandAudio"))
    eng = rows_of(mods, "LandEngine")
    print("  LandEngine max_rpm:", eng.get("max_rpm"))
    print("  LandEngine idle_rpm:", eng.get("idle_rpm"))


def cmd_build():
    print("## Working/Translation/current.json (the build snapshot)")
    c = json.load(open(os.path.join(ROOT, "Working", "Translation", "current.json"),
                       encoding="utf-8"))
    print("build:", c.get("build"))
    print("files:", c.get("files"))
    mods = c.get("modules", {})
    print("modules:", {k: (len(v) if hasattr(v, "__len__") else v) for k, v in mods.items()})
    for name in ("VehicleDynamicLights", "VehicleDamage", "Palette", "LandAudio",
                 "EffectAttachments"):
        v = mods.get(name)
        if v is None:
            continue
        print(f"  {name}: {json.dumps(v, default=str)[:300]}")
    lights = mods.get("VehicleDynamicLights")
    if isinstance(lights, dict):
        rows = lights.get("lights") or lights.get("rows") or []
        beh = collections.Counter(r.get("behavior") for r in rows if isinstance(r, dict))
        print("  light behaviors:", dict(beh), "rows", len(rows))
        print("  spots range 30:", sum(1 for r in rows if isinstance(r, dict) and
                                       r.get("range") == 30))
    eff = mods.get("EffectAttachments")
    if isinstance(eff, dict):
        ae = eff.get("all_effects") or []
        print("  all_effects rows:", len(ae))
        pts = {r.get("deform_point") or r.get("point_index") for r in ae if isinstance(r, dict)}
        print("  distinct deform points:", len(pts))
        print("  part_effects:", len(eff.get("part_effects") or []))
        print("  usages:", [u.get("usage") for u in (eff.get("usage_effects") or [])
                            if isinstance(u, dict)])


def cmd_index():
    print("## INDEX.jsonl counts of the classes §8 quotes")
    idx = [json.loads(l) for l in open(os.path.join(ROOT, "Research", "JC3Grab",
                                                    "INDEX.jsonl"), encoding="utf-8")]
    print("index rows:", len(idx))
    for pat in ("sweaponpoint", "ccameramodifier", "ccameratransition", "cforcepulse",
                "cpartprop"):
        n = sum(1 for r in idx if pat in r["path"].lower())
        print(f"  paths containing {pat!r}: {n}")


def main(argv):
    cmds = {"damage": cmd_damage, "lights": cmd_lights, "parts": cmd_parts,
            "physics": cmd_physics, "audio": cmd_audio, "build": cmd_build,
            "index": cmd_index}
    what = argv[1] if len(argv) > 1 else "all"
    if what == "all":
        for name, fn in cmds.items():
            print(f"\n===== {name} =====")
            fn()
    elif what in cmds:
        cmds[what]()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
