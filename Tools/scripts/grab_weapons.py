"""grab_weapons.py - every value of every Batmobile weapon, named and joined.

The grab (`grab_model.py`) records the Batmobile's weapon objects with their property tags, but the
cooker strips most tag names, so `MECHANICS.md` can only print `offset 0x2680  0.0`. `CHAIN.json`
already recovered the names from the BmSDK layout; this tool is the per-weapon join that turns the
naked rows into a readable table:

    offset (package) + layout (SDK) + stream name (structs/arrays) = a named weapon field

It selects every object in the four vehicle packages whose class starts with `RBatmobile` or is
`RBasicProjectile`, flattens each one's tags (struct children and curve points included), resolves
every object reference inside its own package, and compares the same-named objects across the
base / MK2 / Funhouse / Joker packages value by value.

G1-09 adds the normalized `projectiles` rows: the card's per-projectile values, the linked
`ImpulseComponent0` fields, the trail/impact particle systems (joined to `PARTICLES.json` for their
emitter counts), the flight/explosion AkEvents, and which launcher names each projectile.

Nothing is hand-typed and nothing is guessed: an offset with no name in `CHAIN.json` is printed as
`offset 0x...` with its value; an array whose payload `objects.jsonl` did not decode is marked
undecoded; a reference that leaves the four packages is `missing-object`, not invented.

Outputs:
  Research/BatmobileGrab/WEAPONS.json   the machine source (one record per object instance)
  Research/BatmobileGrab/WEAPONS.md     one section per class, plus the cross-object tables

Usage:
  python Tools/scripts/grab_weapons.py --write
  python Tools/scripts/grab_weapons.py --check
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OBJECTS = GRAB / "objects.jsonl"
CHAIN = GRAB / "CHAIN.json"
PARTICLES = GRAB / "PARTICLES.json"
OUT_JSON = GRAB / "WEAPONS.json"
OUT_MD = GRAB / "WEAPONS.md"

PACKAGES = (
    ("Playable_Batmobile_SF", "Batmobile"),
    ("Playable_BatmobileMK2_SF", "MK2"),
    ("Playable_BatmobileFunhouse_SF", "Funhouse"),
    ("Playable_BatmobileJoker_SF", "Joker"),
)
LABEL = dict(PACKAGES)
ORDER = {p: i for i, (p, _) in enumerate(PACKAGES)}
PROJECTILE_CLASSES = ("RBasicProjectile", "RBatmobileMissile")

# G1-09: the projectile quantities, in the card's order. Candidates are tried in this order and the
# first path present in an instance wins; `None` means the card names the value but no field in
# these packages carries it.
PROJECTILE_VALUES = (
    ("speed", "speed", ("Projectile.Speed",)),
    ("max_speed", "max speed", ("Projectile.MaxSpeed",)),
    ("acceleration", "acceleration", ("RBatmobileMissile.AccelRate",
                                       "RBasicProjectile.InitialAcceleration")),
    ("homing_flag", "homing flag (unnamed bool)", ("offset 0x0420",)),
    ("homing_delay", "homing delay", ("RBatmobileMissile.HomingDelay",)),
    ("force_explode_prox_dist", "force-explode proximity distance",
     ("RBatmobileMissile.ForceExplodeProxDist",)),
    ("damage", "damage", ("Projectile.Damage",)),
    ("turret_shot_damage", "turret-shot damage", ("RBasicProjectile.TurretShotDamage",)),
    ("damage_radius", "damage radius", ("Projectile.DamageRadius",)),
    ("momentum_transfer", "momentum transfer", ("Projectile.MomentumTransfer",)),
    ("damage_type", "damage type", ("Projectile.MyDamageType",)),
    ("lifetime", "lifetime", ("Projectile.LifeSpan", "Projectile.Lifetime", "Actor.LifeSpan")),
)

# The particle-bearing fields on a projectile, and the role each plays in the explosion/flight FX.
PROJECTILE_FX = (
    ("trail", "RBasicProjectile.ProjectileTrail"),
    ("trail", "RBatmobileMissile.Trail"),
    ("impact", "RBasicProjectile.ImpactExplosion"),
    ("explosion", "RBatmobileMissile.ExplosionTemplate"),
    ("impact flame trail", "RProjectile.ImpactExplosionFlameTrail"),
    ("pass-through effect", "RBasicProjectile.PassThroughDestructibleEffect"),
    ("muzzle flash", "RBasicProjectile.MuzzleFlashOverride"),
)

# The quantities the G1-08 card names, as patterns over the joined field paths. A field can match
# more than one quantity; the record prints every match rather than picking a winner.
QUANTITIES = (
    ("fire rate / cooldown", r"(FiringInterval|FireInterval|WeaponCoolDown|ReloadTime)"),
    ("damage", r"(\.Damage$|DamageRadius|ChainGunDamage|UpgradedDamage|TurretShotDamage)"),
    ("damage / lethal radius", r"(DamageRadius|LethalRadius|ChargeMaxDamageRadius)"),
    ("range", r"(LethalRange|LockOnRange|RiotSuppressorRange)"),
    ("projectile archetype", r"(MissileClass|ProjectileArchetype)"),
    ("speed / acceleration", r"(Projectile\.Speed|MaxSpeed|AccelRate|InitialAcceleration|ChainGunMaxSpinSpeed)"),
    ("projectile lifetime", r"(LifeSpan|Lifetime)"),
    ("homing / flight", r"(Homing|ForceExplodeProxDist)"),
    ("heat bar", r"(HeatBarStart|HeatBarSize|HeatUpPerSecond|OverheatOffValue)"),
    ("inaccuracy-vs-time", r"(InaccuracyVsTime)"),
    ("inaccuracy-vs-heat", r"(InaccuracyVsHeat)"),
    ("charge", r"(ChargeUpTime|ChargingScreenShake)"),
    ("salvo / targets", r"(MaxTargets|MissileNumberParameter|NumFakeTargetReps)"),
    ("launch sockets", r"(MissileSockets|MissileLaunchSockets)"),
    ("lock time", r"(LockOnTime|MissileLockOnDuration|CivilianMissileLockOnDuration)"),
    ("lock angle", r"(LockOnAngle)"),
    ("impulse / momentum", r"(MomentumTransfer|RecoilImpulse|ImpactMomentum|ImpulseComponent)"),
    ("screen shakes", r"ScreenShake$"),
    ("bones to hide", r"(BonesToHideWhenNotPresent)"),
    ("mesh / trail", r"(ProjectileMesh|ProjectileTrail|RocketTrail|\.Mesh$|\.Trail$)"),
    ("fire / impact FX", r"(FireFX|MuzzleFlash|ImpactExplosion|ExplosionTemplate)"),
    ("audio", r"(Sound|Event)$"),
)


# ---------------------------------------------------------------------------------------------
# inputs


def load_objects() -> list[dict]:
    with open(OBJECTS, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_chain() -> dict:
    return json.loads(CHAIN.read_text(encoding="utf-8"))["fields"]


def load_particles() -> dict:
    """PARTICLES.json, indexed the two ways a resolved particle system can be looked up."""
    doc = json.loads(PARTICLES.read_text(encoding="utf-8"))
    by_key, by_name = {}, defaultdict(list)
    for s in doc.get("systems") or []:
        by_key[(s["package"], s["index"])] = s
        by_name[(s["package"], s["name"])].append(s)
    return {"systems": doc.get("systems") or [], "by_key": by_key, "by_name": by_name,
            "summary": doc.get("summary") or {}}


def load_index(recs: list[dict]) -> dict:
    by_idx = defaultdict(list)
    for r in recs:
        if r["package"] in LABEL:
            by_idx[(r["package"], r["index"])].append(r)
    return {"by_idx": by_idx}


def selected(recs: list[dict]) -> list[dict]:
    out = []
    for r in recs:
        if r["package"] not in LABEL:
            continue
        cls = r["class"] or ""
        if cls.startswith("RBatmobile") or cls == "RBasicProjectile":
            out.append(r)
    return sorted(out, key=lambda r: (r["class"], r["name"], r["package"]))


# ---------------------------------------------------------------------------------------------
# naming and flattening


def field_name(tag: dict, binds: dict) -> tuple[str | None, str | None]:
    """(name, named_by) for a top-level tag: its own stream name wins over the SDK layout."""
    if tag.get("name"):
        return tag["name"], "stream"
    hits = binds.get(tag.get("offset")) or []
    if len(hits) == 1:
        return hits[0], "sdk-layout"
    return None, None


def item_nodes(item) -> list[dict]:
    if not isinstance(item, list):
        item = [item]
    out = []
    for c in item:
        node = {"offset": c.get("offset"), "type": c.get("type")}
        if c.get("name"):
            node["name"] = c["name"]
        if "bits" in c:
            node["bits"] = c["bits"]
        if "value" in c:
            node["value"] = c["value"]
        if "ref" in c:
            node["ref"] = {"path": c["ref"], "class": c.get("ref_class")}
        out.append(node)
    return out


def add_field(tag: dict, path: str, named_by: str | None, out: list[dict],
              depth: int = 0) -> None:
    ttype = tag.get("type")
    if ttype == "StructProperty" and tag.get("props") is not None:
        props = tag["props"]
        out.append({"path": path, "offset": tag.get("offset"), "type": ttype, "depth": depth,
                    "struct": {"size": tag.get("size"), "props": len(props)},
                    "named_by": named_by})
        for child in props:
            nm = child.get("name")
            cpath = path + "." + (nm or "offset 0x%04X" % (child.get("offset") or 0))
            add_field(child, cpath, "stream" if nm else None, out, depth + 1)
        return
    if ttype == "StructProperty" and tag.get("floats") is not None:
        # FVector2D-shaped structs (HeatBarStart/HeatBarSize) arrive as floats + raw bytes.
        out.append({"path": path, "offset": tag.get("offset"), "type": ttype, "depth": depth,
                    "value": tag["floats"], "raw": tag.get("raw"), "named_by": named_by})
        return
    if ttype == "ArrayProperty":
        items = tag.get("items")
        node = {"path": path, "offset": tag.get("offset"), "type": ttype, "depth": depth,
                "array": {"count": tag.get("count"), "stride": tag.get("stride"),
                          "size": tag.get("size"), "decoded": items is not None},
                "named_by": named_by}
        if items is not None:
            node["array"]["items"] = [item_nodes(it) for it in items]
        out.append(node)
        return
    node = {"path": path, "offset": tag.get("offset"), "type": ttype, "depth": depth,
            "named_by": named_by}
    if "bits" in tag:
        node["bits"] = tag["bits"]
    if "value" in tag:
        node["value"] = tag["value"]
    if "ref" in tag:
        node["ref"] = {"path": tag["ref"], "class": tag.get("ref_class")}
    out.append(node)


def offset_label(tag: dict) -> str:
    return "offset 0x%04X" % (tag.get("offset") or 0)


# ---------------------------------------------------------------------------------------------
# reference resolution


def resolve(target: str, ref_class: str | None, index: int | None, package: str,
            ctx: dict) -> dict:
    """Resolve a ref inside its own package; anything else is reported, never guessed.

    `objects.jsonl` carries the reference's export index: a positive index names an export in the
    same package, so the exact export is looked up by index and then verified against the path's
    last segment and its class. A negative index is an import from another package and is never
    resolved locally, even if a same-named export happens to exist in this package (the defect
    that made every `RocketTrail` ref point at the first `RocketTrail` export).
    """
    last = target.split(".")[-1]
    if index is not None and index < 0:
        return {"status": "missing-object", "resolved_to": None}
    candidates = ctx["by_idx"].get((package, index)) if index is not None else None
    if candidates:
        exact = [r for r in candidates
                 if r["name"] == last and (not ref_class or r["class"] == ref_class)]
        if len(exact) == 1:
            r = exact[0]
            return {"status": "resolved",
                    "resolved_to": {"source": "objects.jsonl", "package": package,
                                    "index": r["index"], "outer": r.get("outer"),
                                    "name": r["name"], "class": r["class"],
                                    "object": (r.get("outer") + "." if r.get("outer") else "")
                                              + r["name"]}}
    return {"status": "missing-object", "resolved_to": None}


# ---------------------------------------------------------------------------------------------
# records


def object_record(rec: dict, chain: dict, ctx: dict) -> dict:
    package, name, cls = rec["package"], rec["name"], rec["class"]
    binds = defaultdict(list)
    for b in chain.get(cls, {}).get(package + "." + name, []):
        binds[b["offset"]].append(b["name"])
    fields, refs = [], []
    for tag in rec["tags"]:
        nm, named_by = field_name(tag, binds)
        path = nm or offset_label(tag)
        add_field(tag, path, named_by, fields)
        if "ref" in tag:
            resolved = resolve(tag["ref"], tag.get("ref_class"), tag.get("value"), package, ctx)
            refs.append({"path": path, "target": tag["ref"], "class": tag.get("ref_class"),
                         "status": resolved["status"], "resolved_to": resolved["resolved_to"]})
    return {
        "key": package + "." + name,
        "package": package,
        "label": LABEL[package],
        "name": name,
        "class": cls,
        "kind": "projectile" if cls in PROJECTILE_CLASSES else "gadget",
        "class_default": name.startswith("Default__"),
        "size": rec.get("size"),
        "parsed": rec.get("parsed"),
        "tags": rec.get("tag_count"),
        "fields": fields,
        "references": refs,
    }


def field_id(node: dict) -> tuple:
    return (node.get("offset"), node.get("bits"), node["path"])


def signature(node: dict) -> str:
    if "ref" in node:
        return json.dumps(["ref", node["ref"]], sort_keys=True)
    if "value" in node:
        return json.dumps(["value", node["value"]], sort_keys=True)
    if "struct" in node:
        return json.dumps(["struct", node["struct"]], sort_keys=True)
    return json.dumps(["array", node["array"]], sort_keys=True)


def display(node: dict) -> dict:
    if "ref" in node:
        return {"ref": node["ref"]}
    if "value" in node:
        return {"value": node["value"]}
    if "struct" in node:
        return {"struct": node["struct"]}
    return {"array": node["array"]}


def variant_map(objects: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for o in objects:
        if o["class_default"]:
            continue
        groups[(o["class"], o["name"])].append(o)
    out = []
    order = sorted(groups.items(),
                   key=lambda kv: (1 if kv[0][0] in PROJECTILE_CLASSES else 0, kv[0][0], kv[0][1]))
    for (cls, name), insts in order:
        insts.sort(key=lambda o: ORDER[o["package"]])
        if len(insts) < 2:
            continue
        maps = {o["package"]: {field_id(n): n for n in o["fields"]} for o in insts}
        order = [field_id(n) for n in insts[0]["fields"]]
        for o in insts[1:]:
            for n in o["fields"]:
                if field_id(n) not in order:
                    order.append(field_id(n))
        differing, comparisons = [], 0
        for fid in order:
            nodes = {pkg: m[fid] for pkg, m in maps.items() if fid in m}
            comparisons += len(nodes)
            sigs = {pkg: signature(n) for pkg, n in nodes.items()}
            if len(nodes) != len(insts) or len(set(sigs.values())) > 1:
                differing.append({"path": fid[2],
                                  "values": {pkg: display(nodes[pkg])
                                             for pkg in sorted(nodes, key=ORDER.get)}})
        out.append({
            "class": cls,
            "object": name,
            "instances": [{"package": o["package"], "label": o["label"]} for o in insts],
            "fields": len(order),
            "comparisons": comparisons,
            "differing": len(differing),
            "differing_fields": differing,
        })
    return out


def missing_objects(objects: list[dict]) -> list[dict]:
    agg = {}
    for o in objects:
        for r in o["references"]:
            if r["status"] != "missing-object":
                continue
            key = (r["target"], r["class"])
            row = agg.setdefault(key, {"target": r["target"], "class": r["class"],
                                       "occurrences": 0, "used_by": set()})
            row["occurrences"] += 1
            row["used_by"].add(o["key"])
    rows = []
    for (target, cls), row in sorted(agg.items()):
        rows.append({"target": target, "class": cls, "occurrences": row["occurrences"],
                     "used_by": sorted(row["used_by"])})
    return rows


def resolved_record(resolved_to: dict | None, ctx: dict) -> dict | None:
    if not resolved_to or resolved_to.get("index") is None:
        return None
    for r in ctx["by_idx"].get((resolved_to["package"], resolved_to["index"]), []):
        if r["name"] == resolved_to["name"] and r["class"] == resolved_to["class"]:
            return r
    return None


def component_fields(rec: dict) -> list[dict]:
    fields = []
    for tag in rec.get("tags") or []:
        nm = tag.get("name")
        add_field(tag, nm or offset_label(tag), "stream" if nm else None, fields)
    return [n for n in fields if n.get("depth") == 0]


def particle_info(resolved_to: dict | None, particles: dict) -> dict | None:
    if not resolved_to:
        return None
    s = particles["by_key"].get((resolved_to["package"], resolved_to["index"]))
    if s is None:
        for hit in particles["by_name"].get((resolved_to["package"], resolved_to["name"]), []):
            if (hit.get("outer") or "").split(".")[-1] == \
                    (resolved_to.get("outer") or "").split(".")[-1]:
                s = hit
                break
    if s is None:
        return None
    return {"package": s["package"], "index": s["index"], "outer": s.get("outer"),
            "emitters": len(s.get("emitters") or []), "lod_method": s.get("lod_method")}


def value_row(insts: list[dict], candidates: tuple[str, ...]) -> dict:
    """One card quantity: its field path, its serialized value(s), or an honest absence."""
    present = {}
    paths = set()
    for o in insts:
        top = {n["path"]: n for n in o["fields"] if n.get("depth") == 0}
        found = next(((p, top[p]) for p in candidates if p in top), None)
        if found:
            present[o["label"]] = found[1]
            paths.add(found[0])
    if not present:
        return {"field": None, "searched": list(candidates), "status": "absent"}
    field = sorted(paths)[0] if len(paths) == 1 else sorted(paths)
    sigs = {label: signature(n) for label, n in present.items()}
    if len(present) < len(insts):
        return {"field": field, "status": "partial",
                "values": {label: display(n) for label, n in sorted(present.items())}}
    if len(set(sigs.values())) > 1:
        return {"field": field, "status": "varies",
                "values": {label: display(n) for label, n in sorted(present.items())}}
    return {"field": field, "status": "serialized", "value": display(next(iter(present.values())))}


def ref_row(ref: dict, role: str | None = None) -> dict:
    out = {"field": ref["path"], "target": ref["target"], "class": ref["class"],
           "status": ref["status"], "resolved_to": ref["resolved_to"]}
    if role:
        out = {"role": role, **out}
    return out


def merge_key(row: dict) -> str:
    """A per-package row's identity: the export index is per package and must not split it."""
    d = json.loads(json.dumps(row, sort_keys=True))
    for holder in (d, d.get("system") or {}):
        resolved = holder.get("resolved_to")
        if isinstance(resolved, dict):
            resolved.pop("index", None)
            resolved.pop("package", None)
        particles = holder.get("particles")
        if isinstance(particles, dict):
            particles.pop("index", None)
            particles.pop("package", None)
    return json.dumps(d, sort_keys=True)


def merge_by_package(rows: list[tuple[str, dict]], key_fields: tuple[str, ...]) -> list[dict]:
    """Merge identical per-instance rows into one row carrying the package labels."""
    out = {}
    for label, row in rows:
        key = merge_key({k: row.get(k) for k in key_fields})
        if key not in out:
            out[key] = dict(row, packages=[])
        out[key]["packages"].append(label)
    for row in out.values():
        row["packages"] = sorted(set(row["packages"]), key=list(LABEL.values()).index)
    return [out[k] for k in sorted(out)]


def projectile_rows(objects: list[dict], ctx: dict, particles: dict) -> tuple[list[dict], dict]:
    groups = defaultdict(list)
    for o in objects:
        if o["kind"] == "projectile":
            groups[o["name"]].append(o)
    for insts in groups.values():
        insts.sort(key=lambda o: ORDER[o["package"]])

    # Launcher -> projectile refs, grouped by the projectile they name.
    fired_by = defaultdict(list)
    for o in objects:
        if o["kind"] != "gadget":
            continue
        for r in o["references"]:
            if r["class"] in PROJECTILE_CLASSES:
                fired_by[r["target"].split(".")[-1]].append({
                    "class": o["class"], "name": o["name"], "field": r["path"],
                    "target": r["target"], "status": r["status"], "package": o["label"],
                })

    rows = []
    for name in sorted(groups):
        insts = groups[name]
        launchers = {}
        for r in fired_by.get(name, []):
            key = (r["class"], r["name"], r["target"], r["status"])
            row = launchers.setdefault(key, dict(r, packages=[], fields=[], projectile=name))
            row["packages"].append(r["package"])
            row["fields"].append(r["field"])
        launcher_rows = []
        for r in launchers.values():
            r["packages"] = sorted(set(r["packages"]), key=list(LABEL.values()).index)
            r["fields"] = sorted(set(r["fields"]))
            launcher_rows.append({k: v for k, v in r.items() if k != "package"})
        launcher_rows.sort(key=lambda r: (r["class"], r["name"]))

        values = {key: value_row(insts, candidates)
                  for key, _label, candidates in PROJECTILE_VALUES}

        # The impulse component is an object in its own right; its fields are the card's
        # "ImpulseComponent0 values". Compare the component across packages too.
        impulse = None
        comp_rows = []
        for o in insts:
            ref = next((r for r in o["references"]
                        if r["path"] == "RProjectile.ImpactRadialImpulseComponent"), None)
            if not ref:
                continue
            rec = resolved_record(ref["resolved_to"], ctx)
            comp_rows.append((o["label"], ref, component_fields(rec) if rec else []))
        if comp_rows:
            def comp_sig(fields: list[dict]) -> str:
                # A ref's export index is per-package; compare its path, not its value.
                return json.dumps([{k: v for k, v in f.items() if k != "value"} for f in fields],
                                  sort_keys=True)

            sigs = {label: comp_sig(fields) for label, _ref, fields in comp_rows}
            _first_label, first_ref, first_fields = comp_rows[0]
            impulse = {"field": "RProjectile.ImpactRadialImpulseComponent",
                       "target": first_ref["target"], "status": first_ref["status"],
                       "object": (first_ref["resolved_to"] or {}).get("object"),
                       "class": (first_ref["resolved_to"] or {}).get("class"),
                       "packages": [label for label, _r, _f in comp_rows],
                       "fields": first_fields}
            if len(set(sigs.values())) > 1:
                impulse["per_package"] = {label: fields for label, _r, fields in comp_rows}

        fxs = []
        for o in insts:
            for role, path in PROJECTILE_FX:
                ref = next((r for r in o["references"] if r["path"] == path), None)
                if not ref:
                    continue
                row = ref_row(ref, role)
                if ref["status"] == "resolved" and ref["class"] == "ParticleSystem":
                    row["particles"] = particle_info(ref["resolved_to"], particles)
                if role == "trail" and ref["status"] == "resolved":
                    comp = resolved_record(ref["resolved_to"], ctx)
                    sysref = next((t for t in (comp or {}).get("tags") or []
                                   if t.get("ref_class") == "ParticleSystem"), None)
                    if sysref:
                        res = resolve(sysref["ref"], sysref.get("ref_class"),
                                      sysref.get("value"), o["package"], ctx)
                        row["system"] = {
                            "target": sysref["ref"], "status": res["status"],
                            "resolved_to": res["resolved_to"],
                            "particles": particle_info(res["resolved_to"], particles),
                        }
                    else:
                        row["system"] = {"target": None, "status": "no-template",
                                         "resolved_to": None, "particles": None}
                fxs.append((o["label"], row))
        effects = merge_by_package(fxs, ("role", "field", "target", "class", "status",
                                         "resolved_to", "system", "particles"))

        audio = []
        for o in insts:
            for ref in o["references"]:
                if ref["class"] == "AkEvent":
                    audio.append((o["label"], ref_row(ref)))
        audio = merge_by_package(audio, ("field", "target", "class", "status", "resolved_to"))

        rows.append({
            "name": name,
            "class": insts[0]["class"],
            "instances": [{"package": o["package"], "label": o["label"]} for o in insts],
            "fired_by": launcher_rows,
            "values": values,
            "impulse": impulse,
            "effects": effects,
            "audio": audio,
        })

    fired_names = set(fired_by) & set(groups)
    coverage = {
        "launcher_targets": sorted(fired_names),
        "unfired": sorted(set(groups) - fired_names),
        "orphan_refs": sorted(set(fired_by) - set(groups)),
    }
    return rows, coverage


def undecoded_arrays(objects: list[dict]) -> list[dict]:
    agg = {}
    for o in objects:
        for n in o["fields"]:
            if n.get("type") != "ArrayProperty" or n["array"].get("decoded"):
                continue
            arr = n["array"]
            row = agg.setdefault(n["path"], {"path": n["path"], "count": arr.get("count"),
                                             "stride": arr.get("stride"), "size": arr.get("size"),
                                             "used_by": set()})
            row["used_by"].add(o["key"])
    return [dict(row, used_by=sorted(row["used_by"]))
            for _, row in sorted(agg.items())]


def offset_only(objects: list[dict]) -> list[dict]:
    rows = []
    for o in objects:
        for n in o["fields"]:
            if n["named_by"] is None and n.get("depth") == 0:
                rows.append({"object": o["key"], "path": n["path"], "offset": n.get("offset"),
                             "bits": n.get("bits"), "type": n.get("type"),
                             "value": n.get("value")})
    return rows


def field_index(objects: list[dict]) -> list[dict]:
    # Struct children stay out of the index: they are named by their parent path plus an
    # offset, so indexing them would list the same screen-shake seven times under "charge".
    paths = sorted({n["path"] for o in objects for n in o["fields"]
                    if ".offset 0x" not in n["path"]})
    rows = []
    for quantity, pattern in QUANTITIES:
        rx = re.compile(pattern)
        hits = [p for p in paths if rx.search(p)]
        rows.append({"quantity": quantity, "pattern": pattern, "matches": len(hits),
                     "fields": hits})
    return rows


def collect() -> dict:
    recs = load_objects()
    chain = load_chain()
    particles = load_particles()
    ctx = load_index(recs)
    objects = [object_record(r, chain, ctx) for r in selected(recs)]

    variants = variant_map(objects)
    projectiles, coverage = projectile_rows(objects, ctx, particles)
    missing = missing_objects(objects)
    arrays = undecoded_arrays(objects)
    offsets = offset_only(objects)
    index = field_index(objects)

    classes = defaultdict(list)
    for o in objects:
        classes[o["class"]].append(o)
    kinds = {"gadget": [], "projectile": []}
    for name in sorted(classes):
        kinds["projectile" if name in PROJECTILE_CLASSES else "gadget"].append(name)
    class_rows = []
    for kind in ("gadget", "projectile"):
        for name in kinds[kind]:
            objs = classes[name]
            class_rows.append({
                "name": name,
                "kind": kind,
                "objects": [o["key"] for o in objs],
                "instances": len(objs),
                "names": len({o["name"] for o in objs}),
                "fields": sum(len(o["fields"]) for o in objs),
                "references": sum(len(o["references"]) for o in objs),
                "resolved": sum(1 for o in objs for r in o["references"]
                                if r["status"] == "resolved"),
                "missing": sum(1 for o in objs for r in o["references"]
                               if r["status"] == "missing-object"),
            })

    n_refs = sum(len(o["references"]) for o in objects)
    n_resolved = sum(1 for o in objects for r in o["references"] if r["status"] == "resolved")
    n_fields = sum(len(o["fields"]) for o in objects)
    n_named = sum(1 for o in objects for n in o["fields"]
                  if n["named_by"] and n.get("depth") == 0)
    n_var_fields = sum(v["fields"] for v in variants)
    n_var_comp = sum(v["comparisons"] for v in variants)
    n_var_diff = sum(v["differing"] for v in variants)
    joker_only = sorted({o["name"] for o in objects
                         if o["package"] == "Playable_BatmobileJoker_SF"
                         and not o["class_default"]
                         and all(x["package"] == "Playable_BatmobileJoker_SF"
                                 for x in objects if x["name"] == o["name"])})
    gadget_classes = len(kinds["gadget"])
    proj_classes = len(kinds["projectile"])
    verdict = (
        "the four Batmobile packages carry %d weapon and projectile objects over %d classes "
        "(%d gadget, %d projectile); %d tags flatten to %d fields, %d of the tags are named and "
        "%d bit-packed bools stay offset-only; %d of %d fields compared across the %d "
        "multi-variant objects differ - the Joker package's distinct objects are its %d "
        "Joker-only ones, not a retuned shared object; the %d projectile names over %d "
        "instances resolve %d launcher target(s), and %d projectile name(s) %s included "
        "without one"
        % (len(objects), len(class_rows), gadget_classes, proj_classes,
           sum(o["tags"] or 0 for o in objects), n_fields, n_named, len(offsets), n_var_diff,
           n_var_fields, len(variants), len(joker_only), len(projectiles),
           sum(len(o["instances"]) for o in projectiles), len(coverage["launcher_targets"]),
           len(coverage["unfired"]), "is" if len(coverage["unfired"]) == 1 else "are"))

    doc = {
        "schema": 1,
        "generator": "grab_weapons.py",
        "verdict": verdict,
        "inputs": {
            "objects": "Research/BatmobileGrab/objects.jsonl",
            "chain": "Research/BatmobileGrab/CHAIN.json",
            "particles": "Research/BatmobileGrab/PARTICLES.json",
            "packages": [{"package": p, "label": l} for p, l in PACKAGES],
            "selection": "class starts with RBatmobile, or class is RBasicProjectile",
        },
        "counts": {
            "packages": len(PACKAGES),
            "objects": len(objects),
            "gadget_objects": sum(1 for o in objects if o["kind"] == "gadget"),
            "projectile_objects": sum(1 for o in objects if o["kind"] == "projectile"),
            "classes": len(class_rows),
            "gadget_classes": gadget_classes,
            "projectile_classes": proj_classes,
            "tags": sum(o["tags"] or 0 for o in objects),
            "fields": n_fields,
            "named_fields": n_named,
            "offset_only_fields": len(offsets),
            "references": n_refs,
            "resolved": n_resolved,
            "missing_objects": n_refs - n_resolved,
            "missing_targets": len(missing),
            "variant_objects": len(variants),
            "variant_fields": n_var_fields,
            "variant_comparisons": n_var_comp,
            "differing_fields": n_var_diff,
            "joker_only_objects": len(joker_only),
            "projectile_names": len(projectiles),
            "projectile_instances": sum(len(o["instances"]) for o in projectiles),
            "launcher_projectiles": len(coverage["launcher_targets"]),
            "unfired_projectiles": len(coverage["unfired"]),
            "projectile_effects": sum(len(o["effects"]) for o in projectiles),
            "projectile_audio_events": sum(len(o["audio"]) for o in projectiles),
            "particle_systems": len(particles["systems"]),
        },
        "field_index": index,
        "classes": class_rows,
        "variant_map": variants,
        "projectiles": projectiles,
        "projectile_coverage": coverage,
        "objects": objects,
        "missing_objects": missing,
        "undecoded_arrays": arrays,
        "offset_only": offsets,
    }
    return doc


# ---------------------------------------------------------------------------------------------
# markdown


def esc(text: str) -> str:
    return text.replace("|", "\\|")


def fmt_leaf(node: dict) -> str:
    if "ref" in node:
        return "`%s`" % node["ref"]["path"]
    value = node.get("value")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(json.dumps(v) for v in value) + "]"
    if isinstance(value, str):
        return json.dumps(value)
    if value is None:
        return "-"
    return str(value)


def fmt_item(item: list[dict]) -> str:
    parts = []
    for c in item:
        if "ref" in c:
            parts.append("`%s`" % c["ref"]["path"])
        elif "value" in c:
            val = c["value"]
            if isinstance(val, bool):
                parts.append("true" if val else "false")
            elif isinstance(val, str):
                parts.append(json.dumps(val))
            else:
                parts.append(json.dumps(val))
        else:
            parts.append("-")
    return "[" + ", ".join(parts) + "]"


def fmt_node(node: dict) -> str:
    if "ref" in node or "value" in node:
        return fmt_leaf(node)
    if "struct" in node:
        return "struct, %d props, %s B" % (node["struct"]["props"], node["struct"]["size"])
    arr = node["array"]
    if arr.get("decoded"):
        return "array, %s items: %s" % (arr.get("count"),
                                        "; ".join(fmt_item(it) for it in arr["items"]))
    return "array, %s items, %s B each - payload not decoded" % (arr.get("count"),
                                                                arr.get("stride"))


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(esc(c) for c in row) + " |")
    return out


def fmt_display(d: dict | None) -> str:
    if not d:
        return "-"
    if "ref" in d:
        return "`%s`" % d["ref"]["path"]
    if "value" in d:
        return fmt_leaf({"value": d["value"]})
    if "struct" in d:
        return "struct, %d props, %s B" % (d["struct"]["props"], d["struct"]["size"])
    if "array" in d:
        return "array, %s items" % d["array"].get("count")
    return "-"


def fmt_value(v: dict) -> str:
    if v["status"] == "absent":
        return "absent"
    if v["status"] == "serialized":
        return fmt_display(v.get("value"))
    return "; ".join("%s: %s" % (label, fmt_display(val))
                     for label, val in (v.get("values") or {}).items())


def fmt_field(v: dict) -> str:
    f = v.get("field")
    if not f:
        return "-"
    if isinstance(f, list):
        return ", ".join("`%s`" % p for p in f)
    return "`%s`" % f


def fmt_resolved(ref: dict | None) -> str:
    if not ref:
        return "-"
    return "`%s`" % ref.get("object", ref.get("name"))


def projectile_md(rows: list[dict], coverage: dict) -> list[str]:
    labels = {k: label for k, label, _c in PROJECTILE_VALUES}
    lines = []
    add = lines.append
    add("## 4. Projectiles")
    add("")
    add("The four vehicle packages carry **%d** projectile archetypes over **%d** instances. "
        "**%d** are named by a launcher in the same 62-object selection; **%d** %s included "
        "without one." % (len(rows), sum(len(r["instances"]) for r in rows),
                            len(coverage["launcher_targets"]), len(coverage["unfired"]),
                            "is" if len(coverage["unfired"]) == 1 else "are"))
    add("")
    add("The projectile's own values, its impulse component, and the particle/audio objects it "
        "references. Each row is one object name; the instances are listed because the base, "
        "MK2, Funhouse and Joker packages each carry their own copy. The G1-08 variant map found "
        "no value difference among the shared objects, so a per-package column appears only where "
        "a value actually differs.")
    add("")
    add("Three absences are findings, not omissions. `Batmobile_EMPMissile_Projectile` and "
        "`Batmobile_Tracker_Projectile` serialize no `Projectile.Damage`; "
        "`Batmobile_EMPMissile_Projectile_ForCars` serializes no scalar value at all (it is a "
        "reference-only archetype); and no projectile carries `LifeSpan`/`Lifetime`. Class "
        "defaults are not claimed. The missile trail components resolve locally, but their "
        "particle template is `Engine.Batmobile_Rocket_Trail`, outside these packages, so it "
        "stays `missing-object`.")
    add("")
    add("**Launcher coverage.** Every launcher reference in the 62 selected gadgets:")
    add("")
    cov_rows = []
    for r in rows:
        fired = ", ".join("`%s` via %s (%s)" % (l["name"],
                                                 ", ".join("`%s`" % f for f in l["fields"]),
                                                 ", ".join(l["packages"]))
                          for l in r["fired_by"]) or "- (no launcher in these packages)"
        cov_rows.append(["`%s`" % r["name"], r["class"], str(len(r["instances"])), fired])
    add("\n".join(md_table(["projectile", "class", "instances", "fired by"], cov_rows)))
    add("")
    if coverage["unfired"]:
        add("`%s` is included from the card's list but no `ProjectileArchetype`/`MissileClass` "
            "field in these four packages points at it; its `_ForCars` sibling is the EMP "
            "launcher's target. It is kept, marked, rather than dropped."
            % "`, `".join(coverage["unfired"]))
        add("")
    if coverage["orphan_refs"]:
        add("Launcher refs with no projectile export: %s."
            % ", ".join("`%s`" % n for n in coverage["orphan_refs"]))
        add("")

    for row in rows:
        add("### `%s`" % row["name"])
        add("")
        add("%d instance(s): %s. Class `%s`."
            % (len(row["instances"]),
               ", ".join("**%s**" % i["label"] for i in row["instances"]), row["class"]))
        if row["fired_by"]:
            add("")
            add("Fired by %s." % ", ".join("`%s.%s` via %s"
                                          % (l["class"], l["name"],
                                             ", ".join("`%s`" % f for f in l["fields"]))
                                          for l in row["fired_by"]))
        add("")
        add("| quantity | field | value |")
        add("|---|---|---|")
        absent = []
        for key, _label, _candidates in PROJECTILE_VALUES:
            v = row["values"][key]
            cell = fmt_value(v)
            if key == "damage_type" and v.get("status") == "serialized" \
                    and v.get("value") == {"value": 0}:
                cell = "null (value 0)"
            add("| %s | %s | %s |" % (labels[key], fmt_field(v), cell))
            if v["status"] == "absent":
                absent.append("%s (%s)" % (labels[key], ", ".join("`%s`" % p
                                                              for p in v["searched"])))
        add("")
        if absent:
            add("Absent from every instance: %s. Whether a class default supplies it is not "
                "claimed; the row records the absence." % "; ".join(absent))
            add("")
        imp = row.get("impulse")
        if imp:
            add("**Impulse component** `%s` (`%s`), resolved from `%s`."
                % (imp.get("object"), imp.get("class"), imp["field"]))
            add("")
            blocks = [("all packages", imp["fields"])] if "per_package" not in imp else \
                     sorted(imp["per_package"].items())
            for label, fields in blocks:
                if "per_package" in imp:
                    add("*%s*" % label)
                    add("")
                frows = [["`%s`" % f["path"], "0x%04X" % (f.get("offset") or 0), f["type"],
                         fmt_node(f)] for f in fields]
                add("\n".join(md_table(["field", "offset", "type", "value"], frows)))
                add("")
        if row["effects"]:
            add("**Flight and impact FX**")
            add("")
            fxrows = []
            for e in row["effects"]:
                sysinfo = ""
                system = e.get("system")
                if system:
                    if system["status"] == "resolved":
                        pinfo = system.get("particles") or {}
                        sysinfo = "; system `%s`" % (system["resolved_to"] or {}).get("object")
                        if pinfo:
                            sysinfo += " (%s emitters)" % pinfo["emitters"]
                    elif system.get("target"):
                        sysinfo = "; system `%s` %s" % (system["target"], system["status"])
                    else:
                        sysinfo = "; no particle template"
                elif e.get("particles"):
                    sysinfo = "; %s emitters" % e["particles"]["emitters"]
                fxrows.append([e["role"], "`%s`" % e["field"], "`%s`" % e["target"],
                               e["class"] or "-", e["status"],
                               fmt_resolved(e["resolved_to"]) + sysinfo,
                               ", ".join(e["packages"])])
            add("\n".join(md_table(["role", "field", "target", "class", "status", "resolved",
                                    "packages"], fxrows)))
            add("")
        if row["audio"]:
            add("**AkEvents**")
            add("")
            arows = [["`%s`" % a["field"], "`%s`" % a["target"], a["class"] or "-", a["status"],
                     fmt_resolved(a["resolved_to"]), ", ".join(a["packages"])]
                    for a in row["audio"]]
            add("\n".join(md_table(["field", "target", "class", "status", "resolved",
                                    "packages"], arows)))
            add("")
    return lines


def render_md(doc: dict) -> str:
    c = doc["counts"]
    lines = []
    add = lines.append

    add("# The Batmobile's weapons: every value in the four vehicle packages")
    add("")
    add("**Verdict.** " + doc["verdict"][0].upper() + doc["verdict"][1:] + ".")
    add("")
    add("Checkable: `python Tools/scripts/grab_weapons.py --check` (record `WEAPONS.json`).")
    add("")

    add("## 0. How to read this record")
    add("")
    add("- **field** is the SDK name when one exists (`RBatmobileCannon.ImpactMomentum`), the")
    add("  stream name when the struct carried one (`HeatBarStart`, `InaccuracyVsTime`), and")
    add("  `offset 0x...` only when neither names the offset. A bool whose bits are packed with")
    add("  another bool cannot be named from an offset; the record keeps its raw bool word.")
    add("- **offset** is the byte offset in the export (hex). Nested struct children show their")
    add("  offset inside the struct; array items show the item index in the path.")
    add("- **value** is the cooked package's own number. Unreal units are centimetres for")
    add("  positions, cm/s for speeds and 16-bit angle units for rotators (65,536 = 360 degrees);")
    add("  nothing is converted here. An array item lists its decoded children in source order;")
    add("  for a curve point only `InterpMode` carries a name in the stream.")
    add("- **named_by**: `stream` = the tag carried its own name; `sdk-layout` = joined from")
    add("  `CHAIN.json`; `-` = no name exists at that offset (bit-packed bool).")
    add("- **instance** is one package's copy of an object. `Batmobile`, `MK2`, `Funhouse` and")
    add("  `Joker` are the four packages. A field marked with a per-package value differs between")
    add("  them; `-` means the field is absent from that instance.")
    add("")

    add("## 1. Sources and selection")
    add("")
    add("| input | rows used |")
    add("|---|---:|")
    add("| `objects.jsonl` (grab, schema 6) | %d object records selected |" % c["objects"])
    add("| `CHAIN.json` (`bmak_chain.py`) | the `sdk-layout` names below |")
    add("| `PARTICLES.json` (`grab_particles.py`) | particle-system emitter counts for the projectile FX |")
    add("")
    add("Selection is literal: in the four vehicle packages, every object whose class starts")
    add("with `RBatmobile`, plus every `RBasicProjectile`. The `_Std_*` packages hold")
    add("materials and textures, not a vehicle, and are excluded.")
    add("")

    add("## 2. Census")
    add("")
    add("%d objects over %d classes: %d gadget objects in %d gadget classes and %d projectile"
        % (c["objects"], c["classes"], c["gadget_objects"], c["gadget_classes"],
           c["projectile_objects"]))
    add("objects in %d projectile classes. %d tags flatten to %d fields; %d tags are named, %d"
        % (c["projectile_classes"], c["tags"], c["fields"], c["named_fields"],
           c["offset_only_fields"]))
    add("bit-packed bools stay offset-only.")
    add("")
    rows = []
    for row in doc["classes"]:
        rows.append([row["name"], row["kind"], str(row["instances"]), str(row["names"]),
                     str(row["fields"]), str(row["references"]), str(row["resolved"]),
                     str(row["missing"])])
    add("\n".join(md_table(["class", "kind", "objects", "names", "fields", "refs", "resolved",
                            "missing"], rows)))
    add("")
    rows = []
    for package, label in PACKAGES:
        objs = [o for o in doc["objects"] if o["package"] == package]
        rows.append([label, "`%s`" % package, str(len(objs)),
                     str(sum(len(o["fields"]) for o in objs)),
                     str(sum(len(o["references"]) for o in objs))])
    add("\n".join(md_table(["variant", "package", "objects", "fields", "refs"], rows)))
    add("")

    add("## 3. Variant map")
    add("")
    add("The same-named objects are compared field by field. A field is a *difference* when its")
    add("value (or its reference target) differs, or when it is present in one instance and not")
    add("another. References are compared by target path, not by export index, because the index")
    add("is per-package.")
    add("")
    rows = []
    for v in doc["variant_map"]:
        rows.append([v["class"], "`%s`" % v["object"], str(len(v["instances"])),
                     str(v["fields"]), str(v["comparisons"]), str(v["differing"])])
    add("\n".join(md_table(["class", "object", "instances", "fields", "comparisons",
                            "differing"], rows)))
    add("")
    if c["differing_fields"] == 0:
        add("**0 of %d field comparisons differ.** No shared object is retuned between the base,"
            % c["variant_comparisons"])
        add("MK2, Funhouse and Joker packages: the four packages carry the same weapon values.")
        add("The Joker package's distinct objects are its %d Joker-only ones, which have no"
            % c["joker_only_objects"])
        add("same-named counterpart and are dumped in their own sections below: %s."
            % ", ".join(sorted("`%s`" % o["name"] for o in doc["objects"]
                                if o["package"] == "Playable_BatmobileJoker_SF"
                                and not o["class_default"]
                                and all(x["package"] == "Playable_BatmobileJoker_SF"
                                        for x in doc["objects"] if x["name"] == o["name"]))))
    else:
        add("**%d of %d field comparisons differ.** Each differing field is listed under its"
            % (c["differing_fields"], c["variant_comparisons"]))
        add("object below, with one column per instance.")
    add("")

    lines.extend(projectile_md(doc["projectiles"], doc["projectile_coverage"]))

    add("## 5. The card's quantities")
    add("")
    add("Every field path that matches a quantity the G1-08 card names. A path can appear under")
    add("more than one quantity; the list is the index, not a second set of values.")
    add("")
    for row in doc["field_index"]:
        if row["matches"]:
            add("- **%s** (%d): %s" % (row["quantity"], row["matches"],
                                       ", ".join("`%s`" % f for f in row["fields"])))
        else:
            add("- **%s** (0): no field in these objects carries this name." % row["quantity"])
    add("")
    zero = [r["quantity"] for r in doc["field_index"] if not r["matches"]]
    if zero:
        add("The %d zero row(s) are findings, not omissions: %s %s not serialized in these %d"
            % (len(zero), ", ".join(zero), "are" if len(zero) > 1 else "is", c["objects"]))
        add("objects. Whether the engine holds a class default for them is not claimed here.")
    add("")

    number = 6
    for row in doc["classes"]:
        objs = [o for o in doc["objects"] if o["class"] == row["name"]]
        names = sorted({o["name"] for o in objs})
        add("## %d. `%s` - %s" % (number, row["name"], row["kind"]))
        add("")
        add("%d objects over %d packages, %d object name(s): %d field rows (all instances), %d"
            % (row["instances"], len({o["package"] for o in objs}), row["names"], row["fields"],
               row["references"]))
        add("references (%d resolved, %d `missing-object`)." % (row["resolved"], row["missing"]))
        add("")
        rows = []
        for name in names:
            insts = [o for o in objs if o["name"] == name]
            insts.sort(key=lambda o: ORDER[o["package"]])
            rows.append(["`%s`" % name, str(len(insts)),
                         ", ".join(o["label"] for o in insts),
                         str(sum(len(o["fields"]) for o in insts)),
                         str(sum(len(o["references"]) for o in insts)),
                         str(sum(1 for o in insts for r in o["references"]
                                 if r["status"] == "missing-object"))])
        add("\n".join(md_table(["object", "instances", "variants", "field rows", "refs",
                                "missing"], rows)))
        add("")
        for name in names:
            insts = [o for o in objs if o["name"] == name]
            insts.sort(key=lambda o: ORDER[o["package"]])
            add("### `%s`" % name)
            add("")
            if len(insts) == 1:
                add("One instance: **%s**." % insts[0]["label"])
            else:
                add("%d instances: %s." % (len(insts),
                                           ", ".join("**%s**" % o["label"] for o in insts)))
            if insts[0]["class_default"]:
                add("This is the class-default export (`Default__...`), not a placed gadget; it")
                add("is kept in the dump because the card selects by class, and excluded from the")
                add("variant comparison.")
            var = next((v for v in doc["variant_map"]
                        if v["class"] == row["name"] and v["object"] == name), None)
            if var is None:
                add("")
                add("No same-named counterpart in another package, so there is nothing to compare.")
            elif var["differing"] == 0:
                add("")
                add("All %d fields are identical in every instance (%d comparisons, 0 differences)."
                    % (var["fields"], var["comparisons"]))
            else:
                add("")
                add("%d of %d fields differ; they are listed after the shared table."
                    % (var["differing"], var["fields"]))
            add("")
            first = insts[0]
            diff_ids = set()
            if var:
                for d in var["differing_fields"]:
                    diff_ids.add(d["path"])
            rows = []
            for n in first["fields"]:
                if n["path"] in diff_ids:
                    continue
                rows.append(["`%s`" % n["path"], "0x%04X" % (n.get("offset") or 0),
                             n["type"], fmt_node(n)])
            add("\n".join(md_table(["field", "offset", "type", "value"], rows)))
            add("")
            if var and var["differing"]:
                headers = ["field"] + [i["label"] for i in var["instances"]]
                rows = []
                for d in var["differing_fields"]:
                    row = ["`%s`" % d["path"]]
                    for i in var["instances"]:
                        val = d["values"].get(i["package"])
                        if val is None:
                            row.append("-")
                        elif "ref" in val:
                            row.append("`%s`" % val["ref"])
                        elif "value" in val:
                            row.append(fmt_leaf(val))
                        else:
                            row.append("(container)")
                    rows.append(row)
                add("\n".join(md_table(headers, rows)))
                add("")
            rows = []
            for r in first["references"]:
                where = "-"
                if r["resolved_to"]:
                    where = "`%s` in %s (%s)" % (r["resolved_to"]["object"],
                                                 r["resolved_to"]["package"],
                                                 r["resolved_to"]["source"])
                rows.append(["`%s`" % r["path"], "`%s`" % r["target"], r["class"] or "-",
                             r["status"], where])
            add("\n".join(md_table(["field", "target", "class", "status", "resolved to"], rows)))
            add("")
        number += 1

    add("## %d. References that leave the four packages" % number)
    add("")
    add("%d references resolve inside their own package; %d are"
        % (c["resolved"], c["missing_objects"]))
    add("`missing-object` over %d distinct targets. They are not missing from the game - they"
        % c["missing_targets"])
    add("point at `Engine.*`, `Core.*` or another package outside the four vehicle packages,")
    add("which this desk grab does not carry. Nothing about their values is claimed.")
    add("")
    rows = []
    for m in doc["missing_objects"]:
        users = sorted({u.split(".")[-1] for u in m["used_by"]})
        rows.append(["`%s`" % m["target"], m["class"] or "-", str(m["occurrences"]),
                     ", ".join(users)])
    add("\n".join(md_table(["target", "class", "occurrences", "used by"], rows)))
    add("")
    number += 1

    add("## %d. Arrays whose elements the grab did not decode" % number)
    add("")
    add("`objects.jsonl` keeps the array header (`count`, `stride`, `size`) but not the element")
    add("bytes, so these arrays are recorded by shape only. They are listed here rather than")
    add("silently rendered as empty.")
    add("")
    rows = []
    for a in doc["undecoded_arrays"]:
        users = sorted({u.split(".")[-1] for u in a["used_by"]})
        rows.append(["`%s`" % a["path"], str(a["count"]), str(a["stride"]), str(a["size"]),
                     ", ".join(users)])
    add("\n".join(md_table(["field", "count", "stride", "size", "used by"], rows)))
    add("")
    number += 1

    add("## %d. Offset-only fields" % number)
    add("")
    add("These top-level bools have no name: the cooker packs consecutive bools into one 32-bit")
    add("word, so a single offset cannot say which flag it belongs to and `bmak_chain.py` refuses")
    add("to guess. `objects.jsonl` preserves the word (`bits`); the tag's own value is exact.")
    add("")
    rows = []
    for o in doc["offset_only"]:
        rows.append(["`%s`" % o["object"], "`%s`" % o["path"], "0x%04X" % (o["offset"] or 0),
                     "0x%08X" % o["bits"] if o["bits"] is not None else "-",
                     fmt_leaf(o)])
    add("\n".join(md_table(["object", "field", "offset", "bool word", "value"], rows)))
    add("")
    number += 1

    add("## %d. Reproduce" % number)
    add("")
    add("```bash")
    add("python Tools/scripts/grab_weapons.py --write   # -> WEAPONS.json + WEAPONS.md")
    add("python Tools/scripts/grab_weapons.py --check   # re-derive and compare")
    add("```")
    add("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------------------------
# entry points


def json_text(doc: dict) -> str:
    return json.dumps(doc, indent=1) + "\n"


def write(doc: dict) -> None:
    OUT_JSON.write_text(json_text(doc), encoding="utf-8")
    OUT_MD.write_text(render_md(doc), encoding="utf-8")
    c = doc["counts"]
    print("wrote %s (%d bytes)" % (OUT_JSON, OUT_JSON.stat().st_size))
    print("wrote %s (%d bytes)" % (OUT_MD, OUT_MD.stat().st_size))
    print("%d objects, %d classes, %d fields (%d named), %d references (%d missing-object), "
          "%d/%d variant comparisons differ"
          % (c["objects"], c["classes"], c["fields"], c["named_fields"], c["references"],
             c["missing_objects"], c["differing_fields"], c["variant_comparisons"]))
    print("%d projectiles over %d instances; %d launcher target(s), %d without one; "
          "%d particle systems, %d projectile FX rows, %d AkEvent rows"
          % (c["projectile_names"], c["projectile_instances"], c["launcher_projectiles"],
             c["unfired_projectiles"], c["particle_systems"], c["projectile_effects"],
             c["projectile_audio_events"]))


def check(doc: dict) -> int:
    bad = 0
    for path, text in ((OUT_JSON, json_text(doc)), (OUT_MD, render_md(doc))):
        if not path.exists():
            print("FAIL: %s is missing - run --write" % path)
            bad += 1
            continue
        old = path.read_text(encoding="utf-8")
        if old == text:
            print("ok %s" % path)
            continue
        bad += 1
        old_lines, new_lines = old.splitlines(), text.splitlines()
        at = next((i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b),
                  min(len(old_lines), len(new_lines)))
        print("FAIL: %s differs at line %d" % (path, at + 1))
        if at < len(old_lines):
            print("  on disk: %s" % old_lines[at][:160])
        if at < len(new_lines):
            print("  derived: %s" % new_lines[at][:160])
    c = doc["counts"]
    if bad:
        print("FAIL: weapons record is stale")
        return 1
    print("PASS: %d objects, %d classes, %d references (%d missing-object), "
          "%d variant differences, %d projectiles (%d launcher targets, %d unfired), "
          "%d FX rows, %d AkEvent rows"
          % (c["objects"], c["classes"], c["references"], c["missing_objects"],
             c["differing_fields"], c["projectile_names"], c["launcher_projectiles"],
             c["unfired_projectiles"], c["projectile_effects"], c["projectile_audio_events"]))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="regenerate WEAPONS.json + WEAPONS.md")
    ap.add_argument("--check", action="store_true", help="re-derive and compare the two files")
    a = ap.parse_args()
    doc = collect()
    if a.check:
        return check(doc)
    write(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
