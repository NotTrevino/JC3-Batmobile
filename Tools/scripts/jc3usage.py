#!/usr/bin/env python
"""jc3usage.py - G2-22: the effect usage vocabulary (name + hash) across the vehicle fleet.

The card: "dump every `usage` name and hash across the fleet with the vehicles using it; find the
exhaust / nitro / afterburner / boost flame usages (JC3 shows exhaust flames on nitro)."

Inputs (decoded data only, nothing under D:\\Games is written):
  * ``E:/Modding/_gamedata/JC3grab/entities/*.ee.json`` - the 232 entity caches (6,045 module rows in
    total).  `EffectAttachments` carries `usage_effects[i].usage.string/.hash` (the named
    vocabulary) but stores the nested `usage_effects[i].effect_indices[]` elements without their
    prefix, so the usage -> effect link is ambiguous there.
  * the `_effect_attachments.vmodc` inner file of every entity that declares an
    `EffectAttachments` module - re-decoded with `jc3adf` so the nested `effect_indices[]`
    elements stay attached to their usage (this is the real usage -> effect link).
  * `default_extended_effect_usages.vmodc` - the shared `ExtendedEffectUsages` module, decoded
    to prove whether `usages[]` carries anything anywhere.
  * ``E:/Modding/_gamedata/JC3grab/detail/*.ee.json`` - the `.epe` graphs: every object with a `Usage`
    int32 (SAttachedEffect / SDynamicAttachedEffect / *Table) and every
    `SValueDrivenEffectUsage` declaration (name + name_hash).
  * ``Research/JC3Grab/FX_TABLE.jsonl`` - the `.effc` census (exhaust/nitrous file families).

Names are only ever taken from the files: a hash is called by a name when the same decode that
produced the hash also produced that string (`usage.string`, `effect.string`, object `name`).
No hash is ever recomputed and no name is guessed from what the hash "probably" means.

Writes Research/JC3Grab/USAGES.md + USAGES.json. `--check` re-derives both and asserts.

Usage:
  python jc3usage.py --write
  python jc3usage.py --check
  python jc3usage.py dump usages|nitro|epe|fx
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3audio  # noqa: E402  (G2-23: the FEV/FSB5 reader, for the nitro sound event)
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = jc3detail.RAW
GAME = jc3index.DEFAULT_GAME
JSON_NAME = "USAGES.json"
MD_NAME = "USAGES.md"
FX_TABLE = os.path.join(OUT, "FX_TABLE.jsonl")
EXHAUST_DIR = "effects/jc_vehicles/exhaust/"
DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.ee")
FLAME_NAME = re.compile(r"afterburner|afterburn|boost|flame", re.I)
NITRO_NAME = re.compile(r"nitro", re.I)

# G2-23: the nitro chain. `EngineNitro` is the usage the fleet's `usage_effects` rows name (G2-22);
# the sample names are JC3's own FSB5 entry names, so the three swap targets are selected by name.
NITRO_USAGE = 4197885156
NITRO_SAMPLE = re.compile(r"^jc3_veh_land_premium_nitro_(start|loop|stop)$")
NITRO_LIKE_SAMPLE = re.compile(r"nitro|turbo", re.I)
ARCADE_BLOCKS = ("heat_boost", "nitro_boost", "nitro_boost_upgraded",
                 "turbo_jump", "turbo_jump_upgraded")
APPLY_SCRIPT = os.path.join(HERE, "_apply_audio.py")

# ---------------------------------------------------------------------- helpers
def slug(entity: str) -> str:
    """`editor/entities/.../v0300_..._civilian_01.ee` -> `v0300_..._civilian_01`."""
    return entity.rsplit("/", 1)[-1][:-3] if entity.endswith(".ee") else entity


def fnum(v) -> str:
    """Decoded float -> short text (`0.200000003` -> `0.2`); anything else is kept as-is."""
    try:
        return f"{float(v):g}"
    except (TypeError, ValueError):
        return str(v)


def rows_of(path: str) -> list[dict]:
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------- scanners
def cache_scan() -> dict:
    """Count every module in the entity caches and pull the cached usage rows."""
    ent_files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
    modules_total = ea_modules = eeu_modules = 0
    cache_rows = 0            # usage_effects[i].usage.* rows in the caches
    cache_nested = 0          # effect_indices[i] element rows in the caches
    ea_cache: dict[str, list] = {}
    ea_list: list[dict] = []   # one row per EffectAttachments module (an entity may carry two)
    eeu_files: set[str] = set()
    entities: list[str] = []
    for p in ent_files:
        d = json.load(open(p, encoding="utf-8"))
        entity = d["entity"]
        entities.append(entity)
        modules_total += len(d["modules"])
        for mi, m in enumerate(d["modules"]):
            t = m.get("type")
            if t == "EffectAttachments":
                ea_modules += 1
                module_file = m.get("file") or ""
                key = f"{entity}|{mi}"
                ea_list.append({"key": key, "entity": entity, "file": module_file})
                rows = m.get("rows") or []
                pairs, i = [], 0
                while True:
                    s = next((r["value"] for r in rows
                              if r["path"] == f"usage_effects[{i}].usage.string"), None)
                    if s is None:
                        break
                    h = next((r["value"] for r in rows
                              if r["path"] == f"usage_effects[{i}].usage.hash"), None)
                    pairs.append((s, h))
                    cache_rows += 1
                    i += 1
                ea_cache[key] = pairs
                cache_nested += sum(1 for r in rows
                                    if re.fullmatch(r"effect_indices\[\d+\]", r["path"]))
            elif t == "ExtendedEffectUsages":
                eeu_modules += 1
                if m.get("file"):
                    eeu_files.add(m["file"])
    per_entity_ea = collections.Counter(m["entity"] for m in ea_list)
    return {"entities": entities, "entity_files": ent_files, "modules_total": modules_total,
            "entities_with_ea": len(per_entity_ea),
            "entities_without_ea": sorted(set(entities) - set(per_entity_ea)),
            "entities_with_two_ea": sorted(e for e, n in per_entity_ea.items() if n > 1),
            "ea_modules": ea_modules, "eeu_modules": eeu_modules, "cache_rows": cache_rows,
            "cache_nested": cache_nested, "ea_cache": ea_cache, "ea_list": ea_list,
            "eeu_files": sorted(eeu_files)}


def redecode(cache: dict, index_rows: list[dict]) -> dict:
    """Re-decode every `_effect_attachments.vmodc` so usage -> effect_indices stays attached."""
    per_entity: dict[str, list] = {}
    effect_names: dict[int, set] = collections.defaultdict(set)
    nested = rows_count = mismatches = 0
    errors: list[str] = []
    for mod in cache["ea_list"]:
        entity, module_file = mod["entity"], mod["file"]
        try:
            raw = jc3grab.read_entry(jc3detail.pick(index_rows, entity), GAME)
            stream, entries = jc3detail.inner_files(raw)
            hit = next((e for e in entries if e[0] == module_file), None)
            if hit is None:
                errors.append(f"{entity}: {module_file} not in container")
                continue
            flat: dict = {}
            for p, _t, v in jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]])):
                flat.setdefault(p, v)
            usages, i = [], 0
            while f"usage_effects[{i}].usage.hash" in flat:
                name = flat.get(f"usage_effects[{i}].usage.string", "")
                h = flat[f"usage_effects[{i}].usage.hash"]
                idxs, j = [], 0
                while f"usage_effects[{i}].effect_indices[{j}]" in flat:
                    idxs.append(int(flat[f"usage_effects[{i}].effect_indices[{j}]"]))
                    j += 1
                nested += len(idxs)
                effs = sorted({str(flat.get(f"all_effects[{k}].effect.string", f"?{k}"))
                               for k in idxs})
                usages.append({"name": name, "hash": h, "effects": effs})
                i += 1
            k = 0
            while f"all_effects[{k}].effect.hash" in flat:
                effect_names[int(flat[f"all_effects[{k}].effect.hash"]) & 0xFFFFFFFF].add(
                    str(flat.get(f"all_effects[{k}].effect.string", "")))
                k += 1
            per_entity[mod["key"]] = {"entity": entity, "usages": usages}
            rows_count += i
        except Exception as e:                      # noqa: BLE001 - recorded, never hidden
            errors.append(f"{entity}: {e!r}")
    for key, cached in sorted(cache["ea_cache"].items()):
        got = [(u["name"], u["hash"])
               for u in (per_entity.get(key) or {"usages": []})["usages"]]
        if got != cached:
            mismatches += 1
    return {"per_entity": per_entity, "effect_names": dict(effect_names), "nested": nested,
            "rows": rows_count, "mismatches": mismatches, "errors": errors}


def decode_eeu(cache: dict, index_rows: list[dict]) -> dict:
    """Decode the shared `ExtendedEffectUsages` module out of a live container."""
    want = cache["eeu_files"]
    for entity in cache["entities"]:
        if not want:
            break
        try:
            raw = jc3grab.read_entry(jc3detail.pick(index_rows, entity), GAME)
            stream, entries = jc3detail.inner_files(raw)
        except Exception:                            # noqa: BLE001 - try the next container
            continue
        decoded, missing = [], list(want)
        for path in list(want):
            hit = next((e for e in entries if e[0] == path), None)
            if hit is None:
                continue
            rows = [{"path": p, "type": t, "value": v}
                    for p, t, v in jc3adf.walk(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]]))]
            decoded.append({"file": path, "bytes": hit[2], "rows": rows})
            missing.remove(path)
        if not missing:
            return {"decoded": sorted(decoded, key=lambda r: r["file"]),
                    "usages": sum(1 for d in decoded for r in d["rows"]
                                  if re.fullmatch(r"usages\[\d+\]\..*", r["path"])),
                    "from_entity": entity}
    return {"decoded": [], "usages": None, "from_entity": None}


def _strings(o, path: str = ""):
    """Yield (path, str) for every string value in a decoded tree."""
    if isinstance(o, dict):
        for k, v in o.items():
            yield from _strings(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def epe_scan() -> dict:
    detail_files = sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json")))
    usage_objs: dict[int, dict] = {}
    decl: dict[str, dict] = {}
    total = 0
    string_values = 0
    ext_hits: list[dict] = []
    donor_usages: dict[int, list] = collections.defaultdict(list)
    name_usages: dict[str, set] = collections.defaultdict(set)
    donor_objects: list[dict] = []
    sound_carriers: dict[str, dict] = {}
    effect_carriers: dict[int, dict] = {}
    donor_slug = slug(DONOR)
    for p in detail_files:
        d = json.load(open(p, encoding="utf-8"))
        entity = slug(d["entity"])
        for spath, s in _strings(d.get("epe") or {}):
            string_values += 1
            if ".effc" in s or ".ctunec" in s or ".trim" in s:
                ext_hits.append({"entity": entity, "path": spath, "value": s[:120]})
        for o in ((d.get("epe") or {}).get("objects") or []):
            v = o.get("values") or {}
            # G2-23: the sound GUID a graph object plays, and the effect hash it attaches.
            if v.get("Sound"):
                g = jc3audio.parse_guid_field(str(v["Sound"]))
                rec = sound_carriers.setdefault(g, {"objects": 0, "entities": set(),
                                                    "names": collections.Counter(),
                                                    "classes": collections.Counter(),
                                                    "usages": collections.Counter()})
                rec["objects"] += 1
                rec["entities"].add(entity)
                rec["names"][str(o.get("name") or "?")] += 1
                rec["classes"][str(o.get("class") or "?")] += 1
                rec["usages"][str(v.get("Usage"))] += 1
            if v.get("Effect") is not None:
                ekey = int(v["Effect"]) & 0xFFFFFFFF
                rec = effect_carriers.setdefault(ekey, {"objects": 0, "entities": set(),
                                                        "names": collections.Counter(),
                                                        "classes": collections.Counter()})
                rec["objects"] += 1
                rec["entities"].add(entity)
                rec["names"][str(o.get("name") or "?")] += 1
                rec["classes"][str(o.get("class") or "?")] += 1
            if entity == donor_slug:
                donor_objects.append({
                    "name": str(o.get("name") or "?"), "class": str(o.get("class") or "?"),
                    "usage": (int(v["Usage"]) & 0xFFFFFFFF) if v.get("Usage") is not None else None,
                    "effect": (int(v["Effect"]) & 0xFFFFFFFF)
                    if v.get("Effect") is not None else None,
                    "sound": jc3audio.parse_guid_field(str(v["Sound"])) if v.get("Sound") else None,
                })
            u = v.get("Usage")
            if u is not None:
                total += 1
                key = int(u) & 0xFFFFFFFF
                oname = str(o.get("name") or "?")
                name_usages[oname].add(key)
                if entity == donor_slug:
                    donor_usages[key].append(oname)
                rec = usage_objs.setdefault(key, {"objects": 0, "entities": set(),
                                                  "classes": collections.Counter(),
                                                  "names": collections.Counter()})
                rec["objects"] += 1
                rec["entities"].add(entity)
                rec["classes"][str(o.get("class") or "?")] += 1
                rec["names"][str(o.get("name") or "?")] += 1
            if (o.get("class") or "") == "SValueDrivenEffectUsage":
                name, h = o.get("name"), v.get("name_hash")
                if name and h is not None:
                    rec = decl.setdefault(str(name), {"hash": int(h) & 0xFFFFFFFF,
                                                      "objects": 0, "entities": set()})
                    rec["objects"] += 1
                    rec["entities"].add(entity)
    return {"files": detail_files, "total": total, "usage_objs": usage_objs, "decl": decl,
            "string_values": string_values, "ext_hits": ext_hits,
            "donor_usages": donor_usages, "name_usages": name_usages,
            "donor_objects": donor_objects, "sound_carriers": sound_carriers,
            "effect_carriers": effect_carriers}


def fx_scan() -> dict:
    exhaust: dict[str, dict] = {}
    donor: list[str] = []
    nitrous: set = set()
    total = 0
    with open(FX_TABLE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            total += 1
            path, cont = r["path"], r["container"]
            if path.startswith(EXHAUST_DIR) and path.endswith(".effc"):
                rec = exhaust.setdefault(path, {"containers": set(), "rows": 0})
                rec["containers"].add(cont)
                rec["rows"] += 1
                if cont == DONOR:
                    donor.append(path)
            if NITRO_NAME.search(path) and path.endswith(".effc"):
                nitrous.add(cont)
    return {"rows": total, "exhaust": exhaust, "donor": sorted(set(donor)),
            "nitrous_containers": sorted(nitrous)}


# ------------------------------------------------------------------ G2-23 chain
def arcade_scan() -> dict:
    """The `arcade.*` boost blocks in `CustomLandGlobal`: donor values + how many carry each."""
    donor_slug = slug(DONOR)
    donor: dict[str, dict] = {}
    carriers: dict[str, set] = collections.defaultdict(set)
    files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        ent = slug(d["entity"])
        for m in d["modules"]:
            if m.get("type") != "CustomLandGlobal":
                continue
            for r in (m.get("rows") or []):
                path = r["path"]
                if not path.startswith("arcade."):
                    continue
                block = path.split(".")[1]
                if block not in ARCADE_BLOCKS:
                    continue
                carriers[block].add(ent)
                if ent == donor_slug:
                    donor.setdefault(block, {})[path[len("arcade.") + len(block) + 1:]] = r["value"]
    return {"donor": donor, "carriers": {b: len(carriers[b]) for b in ARCADE_BLOCKS},
            "entities": len(files),
            "vehicles_with_any": len(set().union(*carriers.values())) if carriers else 0}


def nitro_chain(index_rows: list[dict], effect_names: dict[int, set], epe: dict,
                arcade: dict, nitro_row: dict | None) -> dict:
    """G2-23: usage -> effect -> sound event -> `vehicles.bank` ordinal -> FSB5 sample names."""
    objs = [o for o in epe["donor_objects"] if o["usage"] == NITRO_USAGE]
    sound = next((o["sound"] for o in objs if o["sound"]), None)
    eff = next((o["effect"] for o in objs if o["effect"] is not None), None)

    guids = jc3audio.fmod_guids(DONOR, index_rows)
    d = jc3audio.read_entry(jc3audio.BANKS["vehicles"], index_rows)
    f = jc3audio.fev(d)
    events = jc3audio.fev_events(d, f)
    fsb = jc3audio.fsb(d, f["fsb_off"], True)
    del d
    event = next((e for e in events if e["guid"] == sound), None)
    samples = [{"index": i, "name": n} for i, n in enumerate(fsb["names"])
               if NITRO_SAMPLE.match(n)]
    nitro_like = [{"index": i, "name": n} for i, n in enumerate(fsb["names"])
                  if NITRO_LIKE_SAMPLE.search(n)]

    # what test-060 actually swapped (indices, 0-based) - compared with the names above
    applied: list[int] = []
    if os.path.exists(APPLY_SCRIPT):
        with open(APPLY_SCRIPT, encoding="utf-8") as fh:
            applied = sorted(int(n) for n in re.findall(r"^    \((\d+), os\.path\.join", fh.read(),
                                                       re.M))

    carriers = epe["sound_carriers"].get(sound or "", {"objects": 0, "entities": set(),
                                                        "names": collections.Counter(),
                                                        "classes": collections.Counter(),
                                                        "usages": collections.Counter()})
    eff_carriers = epe["effect_carriers"].get(eff or 0, {"objects": 0, "entities": set(),
                                                       "names": collections.Counter(),
                                                       "classes": collections.Counter()})
    module_effects = [e for e in ((nitro_row or {}).get("effects") or [])
                      if e["effect"] != "EngineNitro"]

    return {
        "usage": {"hash": NITRO_USAGE, "name": "EngineNitro",
                  "name_source": "module usage name" if nitro_row else None,
                  "modules": (nitro_row or {}).get("modules"),
                  "objects": [{"name": o["name"], "class": o["class"],
                               "effect": o["effect"], "sound": o["sound"]} for o in objs]},
        "sound": {
            "guid": sound, "guid_fmt": jc3audio.fmt_guid(sound) if sound else None,
            "in_fmod_guids": bool(sound and sound in guids.get("guids", [])),
            "fmod_banks": guids.get("banks"), "fmod_guid_count": guids.get("count"),
            "bank": "vehicles" if event else None,
            "ordinal": event["ordinal"] if event else None,
            "bytes": event["bytes"] if event else None,
            "carriers": {"objects": carriers["objects"], "vehicles": len(carriers["entities"]),
                         "names": dict(carriers["names"].most_common(6)),
                         "classes": dict(carriers["classes"].most_common(4)),
                         "usages": dict(carriers["usages"].most_common(4))},
        },
        "effect": {
            "object_hash": eff,
            "object_carriers": {"objects": eff_carriers["objects"],
                                "vehicles": len(eff_carriers["entities"]),
                                "names": dict(eff_carriers["names"].most_common(6)),
                                "classes": dict(eff_carriers["classes"].most_common(3))},
            "named_in_module_space": bool(eff and eff in effect_names),
            "module_effects": module_effects,
        },
        "arcade": {"donor": arcade["donor"], "carriers": arcade["carriers"],
                   "vehicles_with_any": arcade["vehicles_with_any"],
                   "entities": arcade["entities"]},
        "samples": {
            "fsb_total": fsb["samples"], "fsb_version": fsb["version"],
            "by_name": samples, "nitro_like": nitro_like,
            "test060_indices": applied,
            "test060_matches_names": applied == sorted(s["index"] for s in samples),
        },
    }


# ---------------------------------------------------------------------- build
def build() -> dict:
    index_rows = jc3index.load_index(OUT)
    cache = cache_scan()
    rec = redecode(cache, index_rows)
    eeu = decode_eeu(cache, index_rows)
    epe = epe_scan()
    fx = fx_scan()
    arcade = arcade_scan()

    usage_names: dict[int, set] = collections.defaultdict(set)
    for pairs in cache["ea_cache"].values():
        for name, h in pairs:
            if h is not None:
                usage_names[int(h) & 0xFFFFFFFF].add(name)

    # ---- the named vocabulary: one row per usage hash
    usages: dict[int, dict] = {}
    for key, mod in sorted(rec["per_entity"].items()):
        entity = mod["entity"]
        for u in mod["usages"]:
            key = int(u["hash"]) & 0xFFFFFFFF
            row = usages.setdefault(key, {"hash": key, "names": set(), "vehicles": set(),
                                          "modules": 0,
                                          "effects": collections.defaultdict(set),
                                          "indices": 0})
            row["vehicles"].add(entity)
            row["modules"] += 1
            if u["name"]:
                row["names"].add(u["name"])
    for mod_key, pairs in sorted(cache["ea_cache"].items()):
        entity = mod_key.rsplit("|", 1)[0]
        for name, h in pairs:
            hk = int(h) & 0xFFFFFFFF
            row = usages.setdefault(hk, {"hash": hk, "names": set(), "vehicles": set(),
                                         "modules": 0,
                                         "effects": collections.defaultdict(set),
                                         "indices": 0})
            row["vehicles"].add(entity)
            if name:
                row["names"].add(name)
    # effect link only exists after the re-decode
    effect_rows = []
    for key, mod in sorted(rec["per_entity"].items()):
        entity = mod["entity"]
        for u in mod["usages"]:
            key = int(u["hash"]) & 0xFFFFFFFF
            for eff in u["effects"]:
                usages[key]["effects"][eff].add(entity)
    for key, row in sorted(usages.items()):
        effect_rows.append({
            "hash": key,
            "names": sorted(row["names"]) or [""],
            "modules": row["modules"],
            "vehicles": sorted(row["vehicles"]),
            "effects": [{"effect": eff, "hash": next(
                (h for h, names in rec["effect_names"].items() if eff in names), None),
                "vehicles": sorted(v)}
                for eff, v in sorted(row["effects"].items())],
        })

    # ---- the .epe Usage key space with name provenance
    prov = collections.Counter()
    epe_rows = []
    for key in sorted(epe["usage_objs"]):
        rec_o = epe["usage_objs"][key]
        un = sorted(usage_names.get(key, []))
        en = sorted(rec["effect_names"].get(key, []))
        dn = sorted(n for n, d in epe["decl"].items() if d["hash"] == key)
        if un:
            name, source = un[0], "module usage name"
        elif en:
            name, source = en[0], "module effect name"
        elif dn:
            name, source = dn[0], "SValueDrivenEffectUsage name"
        else:
            name, source = None, "UNKNOWN"
        prov[source] += 1
        epe_rows.append({
            "usage": key,
            "name": name,
            "name_source": source,
            "also": {"usage_names": un, "effect_names": en, "value_driven_names": dn},
            "objects": rec_o["objects"],
            "vehicles": sorted(rec_o["entities"]),
            "classes": dict(sorted(rec_o["classes"].items())),
            "object_names": dict(sorted(rec_o["names"].items(),
                                        key=lambda kv: (-kv[1], kv[0]))),
        })

    flame = sorted({n for names in usage_names.values() for n in names if FLAME_NAME.search(n)})
    nitro_usages = [r for r in effect_rows
                    if any(NITRO_NAME.search(n) for n in r["names"])]

    # the donor's own attachments (the card's target vehicle)
    donor_usages = []
    for mod in sorted(rec["per_entity"].values(), key=lambda m: m["entity"]):
        if mod["entity"] != DONOR:
            continue
        for u in mod["usages"]:
            donor_usages.append({"name": u["name"], "hash": int(u["hash"]) & 0xFFFFFFFF,
                                 "effects": u["effects"]})
    donor_map = []
    for key in sorted(epe["donor_usages"]):
        mod_names = sorted(usage_names.get(key, []))
        eff_names = sorted(rec["effect_names"].get(key, []))
        dn = sorted(n for n, v in epe["decl"].items() if v["hash"] == key)
        donor_map.append({
            "usage": key,
            "name": (mod_names or eff_names or dn or [None])[0],
            "name_source": ("module usage name" if mod_names else
                            "module effect name" if eff_names else
                            "SValueDrivenEffectUsage name" if dn else "UNKNOWN"),
            "objects": sorted(set(epe["donor_usages"][key])),
        })

    payload = {
        "card": "G2-22",
        "inputs": {
            "entity_cache_files": len(cache["entities"]),
            "modules_total": cache["modules_total"],
            "effect_attachments_modules": cache["ea_modules"],
            "entities_with_effect_attachments": cache["entities_with_ea"],
            "entities_without_effect_attachments": cache["entities_without_ea"],
            "entities_with_two_effect_attachments": cache["entities_with_two_ea"],
            "extended_effect_usages_modules": cache["eeu_modules"],
            "detail_files": len(epe["files"]),
            "fx_table_rows": fx["rows"],
            "fx_table_sha1": hashlib.sha1(open(FX_TABLE, "rb").read()).hexdigest()[:16],
            "index_rows": len(index_rows),
        },
        "extended_effect_usages": {
            "distinct_module_files": cache["eeu_files"],
            "decoded": eeu["decoded"],
            "usages_elements": eeu["usages"],
            "decoded_from": eeu["from_entity"],
        },
        "usage_effects": {
            "cache_rows": cache["cache_rows"],
            "redecoded_rows": rec["rows"],
            "cache_nested_indices": cache["cache_nested"],
            "redecoded_nested_indices": rec["nested"],
            "cache_vs_redecode_mismatches": rec["mismatches"],
            "errors": rec["errors"],
        },
        "usages": effect_rows,
        "epe": {
            "detail_files": len(epe["files"]),
            "objects_with_usage": epe["total"],
            "distinct_values": len(epe_rows),
            "name_provenance": dict(sorted(prov.items())),
            "classes": dict(sorted(collections.Counter(
                c for r in epe_rows for c, n in r["classes"].items()
                for _ in range(n)).items())),
            "string_values": epe["string_values"],
            "effect_file_references": epe["ext_hits"],
            "names_with_multiple_usages": [
                {"name": n, "usages": sorted(u)} for n, u in sorted(epe["name_usages"].items())
                if len(u) > 1],
            "values": epe_rows,
        },
        "value_driven_usages": [
            {"name": n, "name_hash": d["hash"], "objects": d["objects"],
             "vehicles": sorted(d["entities"])}
            for n, d in sorted(epe["decl"].items())],
        "flame": {
            "usage_names_matching_flame_words": flame,
            "nitro_usages": nitro_usages,
            "exhaust_effect_files": [
                {"path": p, "containers": len(v["containers"]), "rows": v["rows"]}
                for p, v in sorted(fx["exhaust"].items())],
            "donor_exhaust_files": fx["donor"],
            "donor_usages": donor_usages,
            "donor_usage_map": donor_map,
            "containers_with_nitrous_effect": len(fx["nitrous_containers"]),
        },
        "nitro": nitro_chain(index_rows, rec["effect_names"], epe, arcade,
                             next((r for r in effect_rows if "EngineNitro" in r["names"]), None)),
    }
    payload["digest"] = hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]
    return payload


# ---------------------------------------------------------------------- md
def md_vehicles(vehicles: list[str], per_line: int = 4) -> str:
    lines = []
    for i in range(0, len(vehicles), per_line):
        lines.append("  " + " · ".join(vehicles[i:i + per_line]))
    return "\n".join(lines) if lines else "  (none)"


def render_md(d: dict) -> str:
    inp = d["inputs"]
    eeu = d["extended_effect_usages"]
    ue = d["usage_effects"]
    epe = d["epe"]
    L: list[str] = []
    a = L.append
    a("# Effect usage vocabulary (G2-22)")
    a("")
    a("Every `usage` name and hash the vehicle fleet carries, which vehicles use each one, and")
    a("the exhaust / nitro / turbo-jump flame usages the card asks for. Generated by")
    a("`Tools/scripts/jc3usage.py --write` from the decoded caches plus a re-decode of the")
    a("`_effect_attachments.vmodc` inner files; `--check` rebuilds both files and compares.")
    a("Names come only from strings decoded next to their hash in the same file - no hash is")
    a("recomputed, no name is inferred from what a number looks like.")
    a("")
    a("## Scope")
    a("")
    a("| input | value |")
    a("|---|---|")
    a(f"| entity caches (`entities/*.ee.json`) | **{inp['entity_cache_files']}** |")
    a(f"| modules in those caches | **{inp['modules_total']:,}** |")
    a(f"| `EffectAttachments` modules | {inp['effect_attachments_modules']} |")
    a(f"| vehicles carrying one | {inp['entities_with_effect_attachments']} |")
    a(f"| vehicles carrying none | {len(inp['entities_without_effect_attachments'])} |")
    a(f"| `ExtendedEffectUsages` modules | {inp['extended_effect_usages_modules']} |")
    a(f"| `.epe` graphs (`detail/*.ee.json`) | {inp['detail_files']} |")
    a(f"| `FX_TABLE.jsonl` rows | {inp['fx_table_rows']:,} |")
    a(f"| `INDEX.jsonl` rows | {inp['index_rows']} |")
    a("")
    a("## 1. `ExtendedEffectUsages` is empty everywhere")
    a("")
    a(f"All {inp['extended_effect_usages_modules']} modules point at one shared file:")
    for f in eeu["decoded"] or []:
        a(f"`{f['file']}` - {f['bytes']} bytes, decoded from `{eeu['decoded_from']}`:")
        for r in f["rows"]:
            a(f"  * `{r['path']}` : {r['type']} = {r['value']!r}")
    a("")
    a(f"`usages[]` elements found: **{eeu['usages_elements']}**. The vocabulary therefore lives")
    a("only in `EffectAttachments.usage_effects[]` (and in the `.epe` graphs, section 3).")
    a("")
    a(f"The {len(inp['entities_without_effect_attachments'])} vehicles with no")
    a("`EffectAttachments` module (they carry no usage at all):")
    a("")
    for e in inp["entities_without_effect_attachments"]:
        a(f"  * `{slug(e)}`")
    a("")
    if inp["entities_with_two_effect_attachments"]:
        a("Vehicles carrying **two** modules (each row counted once per module): "
          + ", ".join(f"`{slug(e)}`" for e in inp["entities_with_two_effect_attachments"]))
        a("")
    a("## 2. The named usage vocabulary (`usage_effects[]`)")
    a("")
    a(f"{ue['cache_rows']} `usage_effects` rows in the caches, {ue['redecoded_rows']} after the")
    a(f"re-decode ({ue['cache_vs_redecode_mismatches']} mismatches, {len(ue['errors'])} decode")
    a(f"errors), carrying {ue['redecoded_nested_indices']} nested `effect_indices` elements.")
    a("The caches store those elements without their `usage_effects[i].` prefix")
    a(f"({ue['cache_nested_indices']} `effect_indices[i]` rows), so the usage -> effect link in")
    a("this section exists only after re-decoding the `.vmodc`.")
    a("")
    a("| usage name | hash | modules | vehicles | effects (vehicles) |")
    a("|---|---|---|---|---|")
    for r in d["usages"]:
        name = r["names"][0] if r["names"] and r["names"][0] else "(empty string)"
        effs = ", ".join(f"`{e['effect']}` ({len(e['vehicles'])})" for e in r["effects"]) or "-"
        a(f"| `{name}` | {r['hash']} | {r['modules']} | {len(r['vehicles'])} | {effs} |")
    a("")
    empty = [r for r in d["usages"] if not (r["names"] and r["names"][0])]
    for r in empty:
        a(f"`{r['hash']}` (`0x{r['hash']:08X}`) carries the **empty string** as its usage name on")
        a(f"{r['modules']} modules / {len(r['vehicles'])} vehicles, and its effect name is empty")
        a("too - the two sides agree, so nothing is being dropped in decoding. What the number")
        a("means is not in any file: recorded as `0xDEADBEEF`-valued, not interpreted.")
        a("")
    a("Every row's full vehicle list:")
    a("")
    for r in d["usages"]:
        name = r["names"][0] if r["names"] and r["names"][0] else "(empty string)"
        a(f"- `{name}` ({r['hash']}) - {len(r['vehicles'])} vehicles:")
        a("")
        a(md_vehicles(r["vehicles"]))
        a("")
    a("## 3. The `.epe` `Usage` key space")
    a("")
    a(f"{epe['objects_with_usage']:,} objects in {epe['detail_files']} graphs carry a `Usage`")
    a("int32, on the classes " + ", ".join(f"`{k}` x{v}" for k, v in
                                          sorted(epe["classes"].items()))
      + f". {epe['distinct_values']} distinct values.")
    a("Name provenance (a hash is only named when the same decode produced the string):")
    a("")
    a("| name source | values |")
    a("|---|---|")
    for k, v in sorted(epe["name_provenance"].items()):
        a(f"| {k} | {v} |")
    a("")
    a("| usage (uint32) | name | name source | objects | vehicles | classes | object names |")
    a("|---|---|---|---|---|---|---|")
    for r in epe["values"]:
        name = f"`{r['name']}`" if r["name"] is not None else "UNKNOWN"
        classes = ", ".join(f"{k} x{v}" for k, v in sorted(r["classes"].items()))
        names = ", ".join(f"{k} x{v}" for k, v in
                          sorted(r["object_names"].items(), key=lambda kv: (-kv[1], kv[0]))[:4])
        a(f"| {r['usage']} | {name} | {r['name_source']} | {r['objects']} | "
          f"{len(r['vehicles'])} | {classes} | {names} |")
    a("")
    a("## 4. Value-driven usage declarations (`SValueDrivenEffectUsage`)")
    a("")
    a("| name | name_hash | objects | vehicles |")
    a("|---|---|---|---|")
    for r in d["value_driven_usages"]:
        a(f"| `{r['name']}` | {r['name_hash']} | {r['objects']} | {len(r['vehicles'])} |")
    a("")
    vdu_hashes = {r["name_hash"] for r in d["value_driven_usages"]}
    epe_hashes = {r["usage"] for r in epe["values"]}
    a("These are the usages the `.epe` declares as driven by a named value. "
      f"{len(vdu_hashes & epe_hashes)} of them appear as a `Usage` int above"
      + (" (" + ", ".join(f"`{n}`" for n, h in
                          sorted((r["name"], r["name_hash"])
                                 for r in d["value_driven_usages"])
                          if h in epe_hashes) + ")" if vdu_hashes & epe_hashes else "") + ".")
    a("")
    a("## 5. Exhaust / nitro / turbo-jump flame (the card's question)")
    a("")
    nitro = d["flame"]["nitro_usages"]
    a("| usage | hash | modules | vehicles | effects (vehicles) |")
    a("|---|---|---|---|---|")
    for r in nitro:
        name = r["names"][0] if r["names"] and r["names"][0] else "(empty string)"
        effs = ", ".join(f"`{e['effect']}` ({len(e['vehicles'])})" for e in r["effects"]) or "-"
        a(f"| `{name}` | {r['hash']} | {r['modules']} | {len(r['vehicles'])} | {effs} |")
    a("")
    for nrow in nitro:
        nname = nrow["names"][0]
        same = [r for r in epe["values"] if r["name"] == nname]
        if not same:
            continue
        row = same[0]
        exhaust_names = {k: v for k, v in row["object_names"].items()
                         if re.search(r"exhaust|nitrous|flame|fire", k, re.I)}
        effect_names = sorted({e["effect"] for e in nrow["effects"]})
        a(f"**Named candidate for \"flame during nitro\": usage `{nname}`")
        a(f"({nrow['hash']})** - the only usage whose name carries *nitro*. It is declared by")
        a(f"{nrow['modules']} `EffectAttachments` modules and its effects are "
          + ", ".join(f"`{e}`" for e in effect_names) + ". Its `Usage` int sits on")
        a(f"**{row['objects']} objects** ({', '.join(f'{k} x{v}' for k, v in sorted(row['classes'].items()))})"
          f" in **{len(row['vehicles'])} of {epe['detail_files']}** `.epe` graphs, under these")
        a("object names (all of them, count x objects):")
        a("")
        for k, v in sorted(exhaust_names.items(), key=lambda kv: (-kv[1], kv[0])):
            a(f"  * `{k}` x{v}")
        a("")
        a("Those are the objects the usage is attached to; the most common flame-looking ones")
        a("are the `exhaust_upgrade_nitrous*` emitters and the `dynamic_exhaust_nitrous`")
        a("SDynamicAttachedEffect. Whether the engine draws a flame when nitro fires is code, not")
        a("data - a Q-1 probe, never claimed here.")
        a("")
    a("Flame words in usage names: "
      + (", ".join(f"`{n}`" for n in d["flame"]["usage_names_matching_flame_words"])
         or "**none** - no usage anywhere in the fleet vocabulary is named afterburner,"
            " boost, flame or fire. The flame is carried by *effect* names")
      + ".")
    a("")
    for want in ("EngineRunning", "EngineTurboJump"):
        row = next((r for r in d["usages"] if want in r["names"]), None)
        if row is None:
            continue
        a(f"`{want}` ({row['hash']}, {row['modules']} modules) attaches "
          + ", ".join(f"`{e['effect']}` on {len(e['vehicles'])}" for e in row["effects"]) + ".")
    a("")
    a(f"The `.effc` files under `{EXHAUST_DIR}` ({len(d['flame']['exhaust_effect_files'])}"
      " distinct paths, one row per embedding container):")
    a("")
    a("| effect file | containers | rows |")
    a("|---|---|---|")
    for r in d["flame"]["exhaust_effect_files"]:
        a(f"| `{r['path'].rsplit('/', 1)[-1]}` | {r['containers']} | {r['rows']} |")
    a("")
    a(f"- distinct containers embedding any `*nitrous*.effc`: "
      f"**{d['flame']['containers_with_nitrous_effect']}**")
    a(f"- the donor (`{DONOR.rsplit('/', 1)[-1]}`) embeds:")
    for p in d["flame"]["donor_exhaust_files"]:
        a(f"  * `{p}`")
    a("")
    dup = next((r for r in d["usages"] if "EngineRunning" in r["names"]), None)
    en = next((e for e in (dup or {"effects": []})["effects"] if e["effect"] == "EngineNitro"),
              None)
    if en:
        a(f"One trap: the *effect* named `EngineNitro` is also attached by the `EngineRunning`")
        a(f"usage on {len(en['vehicles'])} vehicles, so an effect name equal to a usage name is not")
        a("a unique binding - only the `usage_effects[]` row says which usage owns which effect.")
        a("")
    a("### The donor's own attachments")
    a("")
    a(f"Module level: `{DONOR.rsplit('/', 1)[-1]}` carries {len(d['flame']['donor_usages'])}"
      " `usage_effects[]` rows:")
    a("")
    a("| usage name | hash | effects |")
    a("|---|---|---|")
    for u in d["flame"]["donor_usages"]:
        a(f"| `{u['name'] or '(empty string)'}` | {u['hash']} | "
          + (", ".join(f"`{e}`" for e in u["effects"]) or "-") + " |")
    a("")
    a("Its `.epe` graph attaches far more: every `Usage` value in the graph with the objects")
    a("that carry it. **This is the list FX-1/T-17 has to work from** - the module row alone")
    a("does not mention most of these.")
    a("")
    a("| usage (uint32) | name (source) | objects carrying it |")
    a("|---|---|---|")
    for r in d["flame"]["donor_usage_map"]:
        nm = f"`{r['name']}` ({r['name_source']})" if r["name"] else "UNKNOWN"
        a(f"| {r['usage']} | {nm} | " + ", ".join(f"`{o}`" for o in r["objects"]) + " |")
    a("")
    nrow = next((r for r in d["flame"]["donor_usage_map"] if r["usage"] == 4197885156), None)
    if nrow:
        a("The donor's nitro chain reads straight off that table: "
          + ", ".join(f"`{o}`" for o in nrow["objects"])
          + " carry `Usage` = `EngineNitro` (4197885156), which the module vocabulary binds to")
        a("the effect `dynamic_nitrous`. So the donor **does** attach its nitrous exhaust - the")
        a("module row alone would have been a false negative.")
        a("")
    same = [r for r in d["flame"]["donor_usage_map"] if r["name"] is None]
    a(f"Of the {len(d['flame']['donor_usage_map'])} usage values on the donor,"
      f" **{len(same)} cannot be named from any table** ("
      + ", ".join(str(r["usage"]) for r in same)
      + "): the effects are attached but the name behind those hashes is in no decoded")
    a("file. The rest are labelled by the only string the decode produced for that hash, and the")
    a("source column says which space it came from - a `module effect name` is the string of an")
    a("effect that shares the hash, not proof that the trigger is called that.")
    a("")
    a(f"Fleet-wide caveat: **{len(epe['names_with_multiple_usages'])}** effect names attach to")
    a("more than one `Usage` value (e.g. "
      + ", ".join(f"`{r['name']}` x{len(r['usages'])}"
                  for r in epe["names_with_multiple_usages"][:3])
      + "), so an effect name alone never identifies its trigger.")
    a("")
    a("## 6. The nitro chain: input -> effect -> sound event -> sample (G2-23)")
    a("")
    a("The card's chain, one step per row; the last column names the file the value was read from.")
    a("")
    n = d["nitro"]
    snd, eff = n["sound"], n["effect"]
    nb = n["arcade"]["donor"].get("nitro_boost", {})
    up = n["arcade"]["donor"].get("nitro_boost_upgraded", {})
    a("| step | value | read from |")
    a("|---|---|---|")
    a(f"| input (physics) | `arcade.nitro_boost`: torque x{fnum(nb.get('torque_multiplier'))}, "
      f"grip x{fnum(nb.get('grip_multiplier'))}, `push_force` {fnum(nb.get('push_force'))}, "
      f"`boost_blend_time` {fnum(nb.get('boost_blend_time'))} s, `extra_top_speed` "
      f"+{fnum(nb.get('extra_top_speed'))} km/h; `nitro_boost_upgraded`: push "
      f"{fnum(up.get('push_force'))}, +{fnum(up.get('extra_top_speed'))} km/h | "
      "donor `custom_land_global.vmodc` |")
    a(f"| usage | `EngineNitro` ({n['usage']['hash']}) on "
      + ", ".join(f"`{o['name']}`" for o in n["usage"]["objects"])
      + " | donor `.epe` (name from the module usage vocabulary) |")
    for me in eff["module_effects"]:
        a(f"| effect (module) | `{me['effect']}` ({me['hash']}) on {len(me['vehicles'])} vehicles"
          " | `usage_effects[]` re-decode |")
    a(f"| effect (object) | {eff['object_hash']} (0x{eff['object_hash'] & 0xFFFFFFFF:08X}) | "
      "donor `.epe` `Effect` |")
    a(f"| sound event | `{snd['guid_fmt']}` | donor `.epe` `Sound` |")
    a(f"| ... in the donor's `.ee.fmod_guids` | "
      f"{'yes - 1 of' if snd['in_fmod_guids'] else 'no -'} {snd['fmod_guid_count']} events "
      f"(banks {', '.join(snd['fmod_banks'] or [])}) | donor `.fmod_guids` |")
    a(f"| ... in a bank | `{snd['bank']}` `EVTS` ordinal {snd['ordinal']}, {snd['bytes']} B "
      "| FEV reader (`jc3audio.py`) |")
    a("| ... the samples | "
      + ", ".join(f"{x['index']} `{x['name']}`" for x in n["samples"]["by_name"])
      + f" | FSB5 name table ({n['samples']['fsb_total']} samples) |")
    a("")
    c = snd["carriers"]
    arc = n["arcade"]
    a(f"**The input half is module data, not code.** `CustomLandGlobal` carries five `arcade.*` blocks")
    a(f"- `heat_boost`, `nitro_boost`, `nitro_boost_upgraded`, `turbo_jump`, `turbo_jump_upgraded` - "
      f"on **{arc['carriers']['nitro_boost']} of the {arc['entities']} decoded vehicles**. `nitro_boost`")
    a("is the nitro one by name and by what it does to the car: torque x2, grip x2, a 15,000 N push,")
    a("0.2 s blend, +40 km/h top speed, with an `_upgraded` twin at 20,000 N and +80 km/h. `heat_boost`")
    a("is a separate block (`push_force` 0, +80 km/h) and `turbo_jump*` is the jump, which pairs with the")
    a("`EngineTurboJump` usage (11 vehicles). **Which control fires any of them is in no file here** -")
    a("the button lives in code / controls data this census does not carry, so that edge is UNKNOWN.")
    a("")
    a("**The effect half has two hash spaces, and only one is named.** The object's `Effect` field is")
    a(f"{eff['object_hash']} (0x{eff['object_hash'] & 0xFFFFFFFF:08X}), carried by "
      f"**{eff['object_carriers']['objects']} objects on {eff['object_carriers']['vehicles']} vehicles**")
    a("- again all nitrous exhaust: "
      + ", ".join(f"`{k}` {v}" for k, v in eff["object_carriers"]["names"].items()) + ".")
    a("That value appears in **none** of the `all_effects[].effect.hash` lists of the decoded")
    a(f"`_effect_attachments` modules; the module space names {eff['module_effects'][0]['hash'] if eff['module_effects'] else 'UNKNOWN'}"
      " `" + (eff["module_effects"][0]["effect"] if eff["module_effects"] else "UNKNOWN") + "` as the effect the")
    a("`EngineNitro` usage selects (and `EngineNitro` itself on 4 planes). So the module picks")
    a("`dynamic_nitrous`, the object carries a second, unnamed effect hash, and the 9 `*nitrous*.effc`")
    a("files are a candidate family matched by **name only** - the object hash -> `.effc` edge is")
    a("UNKNOWN (section 7).")
    a("")
    a("**The sound step is data to the sample name.** That GUID is carried by")
    a(f"**{c['objects']} objects on {c['vehicles']} of the {inp['entity_cache_files']} decoded vehicles**, "
      "and every carrier is a nitrous exhaust object -")
    a(", ".join(f"`{k}` {v}" for k, v in c["names"].items()) + ", classes "
      + ", ".join(f"`{k}` {v}" for k, v in c["classes"].items())
      + ", so the event is identified by the objects that")
    a(f"play it rather than by a guess. It is one of the donor's {snd['fmod_guid_count']} pinned events and")
    a(f"resolves to a real `EVTS` entry, `{snd['bank']}` ordinal {snd['ordinal']} ({snd['bytes']} B) - not a")
    a("dangling GUID.")
    a("")
    a("**Which samples? By name.** `vehicles.bank` does not link an event to a sample index (that is")
    a("proven in `JC3_AUDIO.md` section 5 - five independent probes, all negative), so the samples are")
    a("the ones JC3 named for this event: "
      + ", ".join(f"{x['index']} `{x['name']}`" for x in n["samples"]["by_name"]) + ".")
    a(f"test-060 swapped exactly those: `_apply_audio.py` replaces 0-based indices")
    a(f"{', '.join(str(i) for i in n['samples']['test060_indices'])}, and "
      f"**{'that is the same set' if n['samples']['test060_matches_names'] else 'that is NOT the same set'}**")
    a(f"as the three indices the names select (checked at build time, not by hand). The bank's other")
    a("nitro-named samples are a different set, and only 165 is a fourth nitrous clip (a flame loop")
    a("test-060 left alone) - the rest are turbo-jump whooshes and the tank's turbowhistle: "
      + ", ".join(f"{x['index']} `{x['name']}`" for x in n["samples"]["nitro_like"]
                  if x["index"] not in {y["index"] for y in n["samples"]["by_name"]}) + ".")
    a("")
    a("**What a build does with this.** Copy `vehicles.bank`, keep all")
    a(f"{n['samples']['fsb_total']} FSB5 samples and every header, and overwrite the PCM16 payload of")
    a("those three indices with the BmAK afterburner start / loop / stop at the same length and rate -")
    a("the swap `_apply_audio.py` already performs for test-060, i.e. route (a) of `JC3_AUDIO.md`.")
    a("No `.ee`, `.epe` or `.fmod_guids` edit is needed: the usage, the attachment and the event")
    a("already exist on the donor, so the mod only changes what the event plays.")
    a("")
    a("## 7. What the files do not say (UNKNOWN)")
    a("")
    a("- **effect name -> `.effc` path.** `all_effects[].effect.string` gives names like")
    a("  `dynamic_nitrous`, and `FX_TABLE.jsonl` gives paths like")
    a("  `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc`, but no decoded file")
    a(f"  maps one to the other: of {epe['string_values']:,} string values in the")
    a(f"  {epe['detail_files']} `.epe` graphs, exactly **{len(epe['effect_file_references'])}**")
    a("  name an `.effc` / `.ctunec` / `.trim`. UNKNOWN - it is a lookup the engine holds, not")
    a("  data in these files.")
    a("- **what drives each usage.** Which variable or event turns a usage on is code; the")
    a("  `.epe` declares only the value-driven set in section 4.")
    a("- **hash function.** UNKNOWN; hashes are read from the files where the string sits next")
    a("  to them, never recomputed, so no identification is needed.")
    a("- **which control fires nitro.** `arcade.nitro_boost` says what happens, no decoded file")
    a("  says which button, key or AI state calls it (see section 6).")
    a("- **the nitro event -> sample edge.** `JC3_AUDIO.md` shows five ways the banks could link an")
    a("  event to a sample and the event->sample index is none of them; the three samples are")
    a("  picked by name. If a future build hears a wrong clip, a different event on the same bank is")
    a("  the likely cause, and only auditioning tells them apart.")
    a("- **in-game behaviour.** No game was launched (R6); the nitro flame rendering is a Q")
    a("  probe.")
    a("")
    a("## 8. Validation")
    a("")
    a("`python Tools/scripts/jc3usage.py --check` re-decodes every input, rebuilds both files in")
    a("memory, compares them byte-for-byte, then asserts (generated from `assertions()`):")
    a("")
    a("| assertion | measured | expected |")
    a("|---|---|---|")
    for label, got, want in assertions(d):
        a(f"| {label} | {got} | {want} |")
    a("")
    return "\n".join(L)


# ---------------------------------------------------------------------- checks
def assertions(d: dict) -> list[tuple[str, object, object]]:
    """(label, measured, expected) - the one table both `--check` and the doc use."""
    inp, eeu, ue, epe = (d["inputs"], d["extended_effect_usages"], d["usage_effects"],
                         d["epe"])
    nitro = next((r for r in d["usages"] if "EngineNitro" in r["names"]), None)
    return [
        ("entity caches read", inp["entity_cache_files"], 232),
        ("modules in those caches", inp["modules_total"], 6045),
        ("`EffectAttachments` modules", inp["effect_attachments_modules"], 225),
        ("vehicles with >=1 `EffectAttachments`", inp["entities_with_effect_attachments"], 224),
        ("`ExtendedEffectUsages` modules", inp["extended_effect_usages_modules"], 232),
        ("distinct `ExtendedEffectUsages` files", len(eeu["distinct_module_files"]), 1),
        ("`ExtendedEffectUsages.usages[]` elements", eeu["usages_elements"], 0),
        ("usage rows in the cache", ue["cache_rows"], 346),
        ("usage rows after re-decode", ue["redecoded_rows"], 346),
        ("nested effect indices in the cache", ue["cache_nested_indices"], 885),
        ("nested effect indices after re-decode", ue["redecoded_nested_indices"], 885),
        ("cache/re-decode mismatches", ue["cache_vs_redecode_mismatches"], 0),
        ("module decode errors", len(ue["errors"]), 0),
        ("distinct usage names", len(d["usages"]), 12),
        ("`EngineNitro` links effect `dynamic_nitrous`",
         bool(nitro and any(e["effect"] == "dynamic_nitrous" for e in nitro["effects"])), True),
        ("usage names matching afterburner/boost/flame",
         len(d["flame"]["usage_names_matching_flame_words"]), 0),
        (".epe objects carrying a `Usage`", epe["objects_with_usage"], 12576),
        (".epe distinct `Usage` values", epe["distinct_values"], 155),
        (".epe references to a `.effc`/`.ctunec`/`.trim`", len(epe["effect_file_references"]), 0),
        ("`FX_TABLE.jsonl` rows", inp["fx_table_rows"], 57187),
        # ---- G2-23: the nitro chain
        ("nitro `.epe` objects (donor)", len(d["nitro"]["usage"]["objects"]), 2),
        ("nitro sound GUID in the donor `.ee.fmod_guids`",
         d["nitro"]["sound"]["in_fmod_guids"], True),
        ("nitro sound -> `vehicles.bank` `EVTS` ordinal", d["nitro"]["sound"]["ordinal"], 249),
        ("objects carrying the nitro sound GUID", d["nitro"]["sound"]["carriers"]["objects"], 202),
        ("vehicles carrying it", d["nitro"]["sound"]["carriers"]["vehicles"], 172),
        ("objects carrying the nitro object `Effect` hash",
         d["nitro"]["effect"]["object_carriers"]["objects"], 28),
        ("nitro object `Effect` hash named in a module `all_effects[]`",
         d["nitro"]["effect"]["named_in_module_space"], False),
        ("nitro sample indices by name",
         [x["index"] for x in d["nitro"]["samples"]["by_name"]], [56, 150, 355]),
        ("test-060 swap indices == the three named samples",
         d["nitro"]["samples"]["test060_matches_names"], True),
        ("vehicles with an `arcade.nitro_boost` block",
         d["nitro"]["arcade"]["carriers"]["nitro_boost"], 145),
    ]


def invariants(d: dict) -> list[str]:
    bad: list[str] = []
    for label, got, want in assertions(d):
        if got != want:
            bad.append(f"{label} {got} != {want}")
    return bad


def summary(d: dict) -> str:
    nitro = next((r for r in d["usages"] if "EngineNitro" in r["names"]), None)
    effs = "/".join(e["effect"] for e in (nitro or {"effects": []})["effects"])
    return (f"{d['inputs']['modules_total']} modules in {d['inputs']['entity_cache_files']} "
            f"caches, {d['inputs']['effect_attachments_modules']} EffectAttachments on "
            f"{d['inputs']['entities_with_effect_attachments']} vehicles, {len(d['usages'])} "
            f"named usages ({d['usage_effects']['redecoded_rows']} rows, "
            f"{d['usage_effects']['redecoded_nested_indices']} effect links re-decoded), "
            f"ExtendedEffectUsages {d['extended_effect_usages']['usages_elements']} usages, "
            f"EngineNitro -> {effs}, "
            f"{d['epe']['distinct_values']} .epe Usage values / "
            f"{d['epe']['objects_with_usage']} objects, "
            f"{len(d['epe']['effect_file_references'])} .effc refs in graphs, "
            f"FX rows {d['inputs']['fx_table_rows']}")


# ---------------------------------------------------------------------- cmds
def cmd_write() -> int:
    d = build()
    bad = invariants(d)
    if bad:
        print("REFUSED: " + "; ".join(bad))
        return 1
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {summary(d)}, {len(md.splitlines())} md lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = invariants(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write")
        return 1
    if json.load(open(jp, encoding="utf-8")) != d:
        bad.append(f"{JSON_NAME} stale")
    md = render_md(d)
    have = open(mp, encoding="utf-8").read()
    if md != have:
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file",
                                         "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {summary(d)}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what == "usages":
        print(json.dumps(d["usages"], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    if what == "nitro":
        print(json.dumps(d["flame"], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    if what == "epe":
        print(json.dumps(d["epe"], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
        return 0
    if what == "fx":
        print(json.dumps({"exhaust_effect_files": d["flame"]["exhaust_effect_files"],
                          "donor": d["flame"]["donor_exhaust_files"],
                          "nitrous_containers": d["flame"]["containers_with_nitrous_effect"]},
                         indent=1, ensure_ascii=False)[:12000])
        return 0
    print("one of: usages, nitro, epe, fx")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="usages")
    a = p.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
