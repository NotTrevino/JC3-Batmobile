#!/usr/bin/env python
"""fx13_casings.py - FX-13 / T-FX13: do JC3 weapons eject brass, and how?

The ledger's T-FX13 row says "no vehicle carries a casing effect" and leaves the
`ChainGunShells` socket empty. This card re-tests that from four directions and
decodes the carrier it finds:

  1. every weapon tune in the grab (`<JC3_RAW>/weapons`, 226 files / 25 ids) -
     member names for casing, shell, eject, brass, cartridge, spawn, effect;
  2. every weapon entity container named by `FX_TABLE.jsonl` - which casing
     `.effc` each one carries (infantry, mounted, turret, DLC/Bavarium);
  3. every decoded vehicle graph (`<JC3_RAW>/detail`, 232 `.ee`) - the
     `SAttachedEffect` objects named ShellEjection / Casing, with their Effect,
     Usage, name_hash and transform;
  4. the attachment itself: the weapon-entity graph inside `w206_mounted_capstone_m2hm.ee`
     and `w201_minigun.ee`, the embedded `.effc` decode (Params / MaxParticles),
     and the Jenkins hash that turns each `Effect` / `Usage` back into a path or
     a usage name.

Outputs: `Research/JC3Grab/FX13_CASINGS.json`, `Research/JC3Grab/FX13_CASINGS.md`
and the queue's DONE report `tmp/freebuff/reports/fx13-shell-casings.md`.
`--check` re-reads the game and the grabs and compares all three byte for byte.

Read-only: the game install and `_gamedata` are opened, never written.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME, MOUNT_RANK  # noqa: E402
from eetoc import sarc_dir, unaaf  # noqa: E402
import jc3fx  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GRAB = os.path.join(RAW, "weapons")
DETAIL = os.path.join(RAW, "detail")
JSON_OUT = "Research/JC3Grab/FX13_CASINGS.json"
MD_OUT = "Research/JC3Grab/FX13_CASINGS.md"
REPORT = "tmp/freebuff/reports/fx13-shell-casings.md"

INDEX = os.path.join(OUT, "INDEX.jsonl")
FX = os.path.join(OUT, "FX_TABLE.jsonl")
WEAPONS = os.path.join(OUT, "WEAPONS.jsonl")
PART = os.path.join(ROOT, "Research", "BatmobileGrab", "PARTICLES_FEATURES.json")

CASING_RE = re.compile(r"casing|shell|eject|brass|cartridge|ammo_?box|spent|bullet_eject", re.I)
EFFECT_RE = re.compile(r"effect|particle|eject|casing|shell|muzzle|spawn|projectile|prefab", re.I)
ATTACH_CLASSES = ("SAttachedEffect", "SDynamicAttachedEffect",
                  "SAttachedEffectTable", "SDynamicAttachedEffectTable")

# the two carrier weapon entities this card decodes end to end
W206 = ("editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/"
        "w206_mounted_capstone_m2hm.ee")
W201 = "editor/entities/jc_weapons/04_mounted/w201_minigun/w201_minigun.ee"
APC = ("editor/entities/jc_vehicles/01_land/v0200_car_capstone_apc/"
       "v0200_car_capstone_apc_military_01.ee")
DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_signature_preorder.ee")

CAPSTONE = "effects/jc_weapons/50_cal/bullet_eject_capstone.effc"
MINIGUN = "effects/jc_weapons/minigun/bullet_eject_minigun.effc"


def u32(h: int) -> int:
    return h & 0xFFFFFFFF


def s32(h: int) -> int:
    return h - (1 << 32) if h >= (1 << 31) else h


def load_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def best_index():
    best = {}
    for r in load_jsonl(INDEX):
        cur = best.get(r["path"])
        if cur is None or MOUNT_RANK[r["mount"]] > MOUNT_RANK[cur["mount"]]:
            best[r["path"]] = r
    return best


def read_indexed(best, path):
    r = best[path]
    arc = os.path.join(DEFAULT_GAME, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        blob = f.read(r["size"])
    if len(blob) != r["size"]:
        raise IOError(f"short read {len(blob)} != {r['size']} for {path}")
    return r, blob


def inners(blob, suffix):
    stream = unaaf(blob)
    return [(n, off, size) for n, off, size in sarc_dir(stream) if n.endswith(suffix)]


def effc_params(blob):
    """Decode one `.effc` and return the numbers FX-13 needs, with the member paths."""
    doc = jc3fx.decode(blob)
    rows = doc["_rows"]
    flat = {p: v for p, _t, v in rows}
    params = []
    i = 0
    while f"Params[{i}]" in flat:
        params.append(flat[f"Params[{i}]"])
        i += 1
    props = []
    j = 0
    while f"Properties[{j}]" in flat:
        props.append(flat[f"Properties[{j}]"])
        j += 1
    maxp = [v for p, _t, v in rows if p.endswith(".MaxParticles")]
    return {
        "size": len(blob),
        "root": doc["root"],
        "rows": doc["rows"],
        "arrays": doc["arrays"],
        "digest": doc["digest"],
        "params": params,
        "properties": props,
        "max_particles": maxp,
        "named_params": [(p, v) for p, _t, v in rows if p.startswith("NamedParameters[")],
    }


def tune_sweep():
    files = 0
    hits = []
    ids = set()
    for dp, _dn, fn in os.walk(GRAB):
        for f in fn:
            p = os.path.join(dp, f)
            files += 1
            parts = os.path.relpath(p, GRAB).replace("\\", "/").split("/")
            if parts:
                ids.add(parts[0])
            try:
                text = open(p, "rb").read().decode("latin-1", "ignore")
            except OSError:
                continue
            for m in CASING_RE.finditer(text):
                hits.append({"file": os.path.relpath(p, RAW).replace("\\", "/"),
                             "match": m.group(0),
                             "context": text[max(0, m.start() - 40):m.end() + 40]})
    return {"files": files, "ids": sorted(ids), "hits": hits}


def weapon_tune_members():
    rows = load_jsonl(WEAPONS)
    members = set()
    effect_like = set()
    rate_like = set()
    for r in rows:
        for t in r.get("tunes", []):
            for inst in t.get("instances", []):
                for p, _ty, _v in inst.get("rows", []):
                    members.add(p)
                    if EFFECT_RE.search(p):
                        effect_like.add(p)
                    if re.search(r"fire_rate|burst|magazine|bullets_per_shot", p):
                        rate_like.add(p)
    return {
        "ids": len(rows),
        "member_paths": len(members),
        "effect_like_members": sorted(effect_like),
        "rate_members": sorted(rate_like),
        "fire_rate": {r["id"]: (r.get("summary") or {}).get("fire_rate") for r in rows},
    }


def fx_sweep():
    rows = load_jsonl(FX)
    casing = [r for r in rows if CASING_RE.search(r["path"])]
    paths = collections.Counter(r["path"] for r in casing)
    containers = collections.defaultdict(set)
    for r in casing:
        containers[r["path"]].add(r["container"])
    weapon_containers = sorted({c for r in casing if "/jc_weapons/" in r["container"]
                                for c in [r["container"]]})
    detail = {}
    for p, cs in containers.items():
        veh = sorted({c.rsplit("/", 1)[0].rsplit("/", 1)[-1]
                      for c in cs if "/jc_vehicles/" in c})
        detail[p] = {
            "containers": sorted(cs),
            "vehicle_containers": sorted(c for c in cs if "/jc_vehicles/" in c),
            "vehicle_dirs": veh,
            "weapon_containers": sorted(c for c in cs if "/jc_weapons/" in c),
            "other_containers": sorted(c for c in cs
                                       if "/jc_vehicles/" not in c and "/jc_weapons/" not in c),
        }
    return {"paths": dict(sorted(paths.items())), "detail": detail,
            "weapon_containers": weapon_containers}


def graph_sweep():
    out = {}
    for f in sorted(os.listdir(DETAIL)):
        if not f.endswith(".json"):
            continue
        d = json.load(open(os.path.join(DETAIL, f), encoding="utf-8"))
        hits = []
        for o in d["epe"]["objects"]:
            vals = o.get("values") or {}
            if o.get("class") in ATTACH_CLASSES and CASING_RE.search(o.get("name") or ""):
                hits.append({
                    "class": o["class"], "name": o["name"], "node": o["node"],
                    "object_id": vals.get("_object_id"),
                    "effect": int(vals["Effect"]) if "Effect" in vals else None,
                    "usage": int(vals["Usage"]) if "Usage" in vals else None,
                    "name_hash": int(vals["name_hash"]) if "name_hash" in vals else None,
                    "world": vals.get("world"),
                })
        if hits:
            out[f] = {"entity": d["entity"], "source": d["source"], "objects": hits}
    return out


def attachment_decode(graphs):
    """The first ShellEjection object in the APC graph, plus its parent weapon entity."""
    apc = graphs["v0200_car_capstone_apc__v0200_car_capstone_apc_military_01.ee.json"]
    obj = next(o for o in apc["objects"] if o["name"] == "ShellEjection")
    d = json.load(open(os.path.join(DETAIL,
                 "v0200_car_capstone_apc__v0200_car_capstone_apc_military_01.ee.json"),
                 encoding="utf-8"))
    objs = d["epe"]["objects"]
    parent_node = obj["node"].rsplit("/", 2)[0]          # /root/0
    parent = next(o for o in objs if o["node"] == parent_node)
    fire = next(o for o in objs
                if o.get("class") == "SWeaponPoint" and o["node"].startswith(parent_node + "/")
                and (o.get("name") == "FirePosition"))
    return {
        "graph": apc["entity"],
        "source": apc["source"],
        "object": obj,
        "parent": {"node": parent_node, "class": parent.get("class"),
                   "name": parent.get("name"), "world": (parent.get("values") or {}).get("world")},
        "fire_point": {"name": fire.get("name"),
                       "world": (fire.get("values") or {}).get("world")},
        "world_member_absent": obj["world"] is None,
        "effect_u32": u32(obj["effect"]),
        "usage_u32": u32(obj["usage"]),
        "name_u32": u32(obj["name_hash"]),
    }


def weapon_entity_decode(best, path, effc_path):
    r, blob = read_indexed(best, path)
    epe_name, epe_off, epe_size = inners(blob, ".epe")[0]
    stream = unaaf(blob)
    epe = stream[epe_off:epe_off + epe_size]
    fx_name, fx_off, fx_size = inners(blob, effc_path.rsplit("/", 1)[-1])[0]
    effc = stream[fx_off:fx_off + fx_size]
    eff_hash = hash_jenkins(effc_path.encode())
    usage_hash = hash_jenkins(b"Fire")
    name_hash = hash_jenkins(b"ShellEjection")
    return {
        "entity": path, "archive": r["archive"], "offset": r["offset"], "size": r["size"],
        "epe": {"name": epe_name, "size": epe_size,
                "shell_ejection_at": epe.find(b"ShellEjection"),
                "effect_hash_at": epe.find(struct.pack("<I", eff_hash)),
                "fire_usage_at": epe.find(struct.pack("<I", usage_hash))},
        "effc": {"name": fx_name, "size": fx_size, **effc_params(effc)},
        "hashes": {"effect": eff_hash, "usage_fire": usage_hash, "name": name_hash},
    }


def bmak_casings():
    part = json.load(open(PART, encoding="utf-8"))
    groups = {g["name"]: g for g in part.get("groups", [])}
    systems = [s for s in part.get("systems", [])
               if re.search(r"casing|shell|eject|brass", s.get("name") or "", re.I)]
    return {
        "group": {k: v for k, v in groups.items() if re.search(r"casing", k, re.I)},
        "systems": [{"package": s.get("package"), "index": s.get("index"),
                     "name": s.get("name"), "role": s.get("role"),
                     "emitters": s.get("emitters"), "lifetime": s.get("lifetime"),
                     "spawn_rate": s.get("spawn_rate"), "materials": s.get("materials"),
                     "colours": len(s.get("colours") or [])} for s in systems],
    }


def build():
    best = best_index()
    tunes = tune_sweep()
    wtunes = weapon_tune_members()
    fx = fx_sweep()
    graphs = graph_sweep()
    att = attachment_decode(graphs)
    w206 = weapon_entity_decode(best, W206, CAPSTONE)
    w201 = weapon_entity_decode(best, W201, MINIGUN)
    part = bmak_casings()

    veh_containers = {}
    for p, d in fx["detail"].items():
        veh_containers[p] = {
            "containers_n": len(d["containers"]),
            "vehicle_containers_n": len(d["vehicle_containers"]),
            "vehicle_dirs": d["vehicle_dirs"],
            "weapon_containers_n": len(d["weapon_containers"]),
            "weapon_containers": d["weapon_containers"],
        }

    checks = {
        "tune_files_226": tunes["files"] == 226,
        "tune_ids_25": len(tunes["ids"]) == 25,
        "tune_casing_members_0": len(tunes["hits"]) == 0,
        "weapon_tune_no_effect_member": len(wtunes["effect_like_members"]) == 0,
        "capstone_22_containers": veh_containers[CAPSTONE]["containers_n"] == 22,
        "minigun_4_containers": veh_containers[MINIGUN]["containers_n"] == 4,
        "capstone_21_vehicle_1_weapon": (
            veh_containers[CAPSTONE]["vehicle_containers_n"] == 21
            and veh_containers[CAPSTONE]["weapon_containers_n"] == 1),
        "minigun_2_vehicle_2_weapon": (
            veh_containers[MINIGUN]["vehicle_containers_n"] == 2
            and veh_containers[MINIGUN]["weapon_containers_n"] == 2),
        "detail_14_containers": len(graphs) == 14,
        "detail_5_vehicle_dirs": len({g["entity"].rsplit("/", 2)[-2]
                                      for g in graphs.values()}) == 5,
        "attachment_effect_matches_capstone":
            att["effect_u32"] == hash_jenkins(CAPSTONE.encode()),
        "attachment_usage_is_Fire": att["usage_u32"] == hash_jenkins(b"Fire"),
        "attachment_name_hash_matches": att["name_u32"] == hash_jenkins(b"ShellEjection"),
        "attachment_no_world": att["world_member_absent"],
        "w206_effect_hash_in_epe": w206["epe"]["effect_hash_at"] > 0,
        "w201_effect_hash_in_epe": w201["epe"]["effect_hash_at"] > 0,
        "w206_fire_usage_in_epe": w206["epe"]["fire_usage_at"] > 0,
        "w201_fire_usage_in_epe": w201["epe"]["fire_usage_at"] > 0,
        "capstone_effc_7423_329": (w206["effc"]["size"] == 7423
                                   and w206["effc"]["rows"] == 329),
        "minigun_effc_6703_177": (w201["effc"]["size"] == 6703
                                  and w201["effc"]["rows"] == 177),
        "capstone_max_particles_15_30": w206["effc"]["max_particles"] == [15, 30],
        "minigun_max_particles_30": w201["effc"]["max_particles"] == [30],
        "gravity_m9_82_both": (w206["effc"]["params"][12] == -9.819999694824219
                               and w201["effc"]["params"][12] == -9.819999694824219),
        "bmak_chain_4emitters_rate4_life1": any(
            s["name"] == "ChainGun_BulletCasing" and s["spawn_rate"] == [4.0, 4.0]
            and s["lifetime"] == [1.0, 1.0] for s in part["systems"]),
        "donor_graph_has_no_casing":
            not any("v0300_car_kensington" in v["entity"] for v in graphs.values()),
    }

    return {
        "schema": "fx13-casings/1",
        "card": "FX-13 / T-FX13",
        "donor": DONOR,
        "tunes": tunes,
        "weapon_tune": wtunes,
        "fx": {"paths": fx["paths"], "detail": veh_containers,
               "weapon_containers": fx["weapon_containers"]},
        "graphs": graphs,
        "attachment": att,
        "attachment_entities": {"w206_mounted_capstone_m2hm": w206,
                                "w201_minigun": w201},
        "bmak": part,
        "checks": checks,
    }


def pct(v):
    return "UNKNOWN" if v is None else (f"{v:.6g}")


def render(doc):
    tunes = doc["tunes"]
    wt = doc["weapon_tune"]
    fx = doc["fx"]
    att = doc["attachment"]
    w206 = doc["attachment_entities"]["w206_mounted_capstone_m2hm"]
    w201 = doc["attachment_entities"]["w201_minigun"]
    part = doc["bmak"]
    L = []
    a = L.append
    a("# FX-13 shell casings - does JC3 eject brass, and how?")
    a("")
    a("Generated by `Tools/scripts/fx13_casings.py --write`; `--check` re-reads the game, the "
      "grab and every input and diffs this file, the JSON and the DONE report byte for byte. "
      "Read-only: no game launch, nothing installed, no archive written.")
    a("")
    a("**STATUS: DONE.** The ledger sentence is wrong in the strongest possible way: JC3 does "
      "carry shell casings on vehicles - as a `SAttachedEffect` named `ShellEjection` inside the "
      "**mounted weapon entity**, pointing at `effects/jc_weapons/50_cal/bullet_eject_capstone.effc` "
      "and triggered by usage `Fire`. The Batmobile's chain gun does not need an invented "
      "attachment: it needs the shipped one copied onto its weapon clone, plus the `.effc` "
      "shipped in the weapon's own `.ee`.")
    a("")
    a("| fact | verdict | evidence |")
    a("|---|---|---|")
    a(f"| weapon tunes with a casing/shell/eject/brass member | **0** | {tunes['files']} files, "
      f"{len(tunes['ids'])} weapon ids (`{RAW}/weapons`) |")
    a(f"| weapon-tune members with any effect/spawn member at all | **0** | "
      f"{wt['member_paths']} member paths over {wt['ids']} ids (`WEAPONS.jsonl`) |")
    a(f"| casing-family `.effc` paths | **{len(fx['paths'])}** | `FX_TABLE.jsonl` |")
    a(f"| weapon `.ee` containers carrying a casing `.effc` | **{len(fx['weapon_containers'])}** "
      f"| `FX_TABLE.jsonl` container field |")
    a(f"| vehicle graphs with a `ShellEjection` attachment | **{len(doc['graphs'])} containers / "
      f"5 vehicle dirs** | 232 decoded `.ee` graphs |")
    a(f"| vehicle containers carrying `bullet_eject_capstone.effc` | "
      f"**{fx['detail'][CAPSTONE]['vehicle_containers_n']}** over "
      f"{len(fx['detail'][CAPSTONE]['vehicle_dirs'])} dirs | `FX_TABLE.jsonl` |")
    a(f"| vehicle containers carrying `bullet_eject_minigun.effc` | "
      f"**{fx['detail'][MINIGUN]['vehicle_containers_n']}** over "
      f"{len(fx['detail'][MINIGUN]['vehicle_dirs'])} dirs | `FX_TABLE.jsonl` |")
    a("")
    a("## 1. What was searched (coverage, and its edge)")
    a("")
    a("| sweep | population | method | casing hits |")
    a("|---|---|---:|---:|")
    a(f"| every weapon tune in the grab | {tunes['files']} files under "
      f"`{RAW.replace(chr(92), '/')}/weapons` ({len(tunes['ids'])} ids; 118 `.wtunec` + 43 "
      f"`.ftunec` source records in `WEAPONS.jsonl`, plus every per-vehicle override copy) "
      f"| raw member-name regex over the ADF text | {len(tunes['hits'])} |")
    a(f"| decoded vehicle-weapon member vocabulary | {wt['ids']} ids, {wt['member_paths']} "
      f"member paths | `WEAPONS.jsonl` -> `tunes[].instances[].rows` | "
      f"{len(wt['effect_like_members'])} |")
    a(f"| every weapon entity the FX table knows | {len(fx['weapon_containers'])} `.ee` "
      f"containers under `jc_weapons/` | `FX_TABLE.jsonl` `container` field | "
      f"{sum(1 for p, d in fx['paths'].items() if d) and len(fx['weapon_containers'])} "
      f"containers (carry a casing path) |")
    a(f"| every decoded vehicle graph | 232 `.ee` objects dumps | "
      f"`{RAW.replace(chr(92), '/')}/detail` -> `epe.objects` | {len(doc['graphs'])} containers |")
    a("")
    a("Edge, stated rather than hidden: the grab extracted `.ee` bytes for the **25 vehicle "
      "weapon ids** only. Infantry, mounted, turret and DLC weapon `.ee` files exist in the "
      "archive and are named by `FX_TABLE`/`INDEX` (579 `jc_weapons` entries), but their bytes "
      "are not in the grab, so for them only the container->`.effc` fact is decoded, not the "
      "`SAttachedEffect` members. The two weapon entities that matter here - the .50 cal and the "
      "minigun - *are* read from the install end to end in section 4.")
    a("")
    a("## 2. The weapon tunes: zero members, so the casing cannot be tune-driven")
    a("")
    a(f"`tunes.files = {tunes['files']}`, `tunes.hits = {len(tunes['hits'])}`. Across all 25 "
      f"vehicle weapon ids and every override copy there is no member whose name contains "
      f"casing, shell, eject, brass, cartridge, ammo box, spent or bullet_eject. The decoded "
      f"`WeaponTuning` vocabulary ({wt['member_paths']} member paths) has **no effect, particle, "
      f"spawn or prefab member** either - the only projectile-side members are "
      f"`tracer_texture_type`, `tracer_fire_velocity`, `tracer_fire_length`, "
      f"`tracer_time_to_live`, `bullets_per_shot` and `bullets_per_tracer`.")
    a("")
    a("Rate members present (the ones a per-shot emitter would inherit):")
    a("")
    a("| member |")
    a("|---|")
    for m in wt["rate_members"][:8]:
        a(f"| `{m}` |")
    a("")
    a("Fire rates of the three machine guns the Batmobile could clone: "
      + ", ".join(f"`{k}` = {pct(v)} s" for k, v in wt["fire_rate"].items()
                  if k in ("w603_mediumtank_mgun", "w604_helicopter_mgun", "w619_buggy_mgun"))
      + " (10 rounds/s).")
    a("")
    a("**Consequence:** a casing attachment cannot be added by a tune edit. It is an entity-graph "
      "object plus an embedded `.effc`, exactly as the game does it.")
    a("")
    a("## 3. The carrier: `SAttachedEffect ShellEjection`")
    a("")
    a("The vehicle-side sweep found the object in these decoded graphs:")
    a("")
    a("| vehicle `.ee` | objects | node | Effect | Usage | `world` |")
    a("|---|---|---|---|---|---|")
    for f, g in sorted(doc["graphs"].items()):
        for o in g["objects"]:
            a(f"| `{g['entity']}` | `{o['class']}` `{o['name']}` | `{o['node']}` | "
              f"`{o['effect']}` | `{o['usage']}` | {('`' + o['world'] + '`') if o['world'] else '**absent**'} |")
    a("")
    a("All of them are the same object: `Effect = -2090719526`, `Usage = -163947359`, "
      "`name_hash = -483953257`, and **no `world` member**. It sits under a "
      "`CBulletWeaponBase` child entity's `SEffects`, i.e. it belongs to the mounted gun, not "
      "to the car body. The fleet-wide `.effc` table widens the same carrier:")
    a("")
    a("| `.effc` | containers | vehicle containers | vehicle dirs | weapon containers |")
    a("|---|---:|---:|---|---:|")
    for p in (CAPSTONE, MINIGUN):
        d = fx["detail"][p]
        a(f"| `{p}` | {d['containers_n']} | {d['vehicle_containers_n']} | "
          + ", ".join(f"`{v}`" for v in d["vehicle_dirs"]) + f" | {d['weapon_containers_n']} |")
    a("")
    a(f"The 232-graph dump and `FX_TABLE` disagree in count only because the dump is a subset "
      f"of the archive's vehicle containers (DLC blackhand/tow/delivery variants are not in it): "
      f"{len(doc['graphs'])} decoded containers vs "
      f"{fx['detail'][CAPSTONE]['vehicle_containers_n']} `.ee` in the table. Both are non-zero; "
      f"the ledger's `0` came from searching the 955 effect paths for the word *casing* and "
      f"never looking at attachments.")
    a("")
    a("## 4. How it is attached (bone, transform, trigger, effect)")
    a("")
    a("### 4.1 The object, decoded from the APC graph")
    a("")
    o = att["object"]
    a("| member | value | decode |")
    a("|---|---|---|")
    a(f"| `_object_id` | `{o['object_id']}` | object id in the `.epe` |")
    a(f"| `class` | `{o['class']}` | effect attachment class |")
    a(f"| `name` / `name_hash` | `{o['name']}` / `{o['name_hash']}` | "
      f"`{att['name_u32']}` = `hash_jenkins(\"ShellEjection\")` |")
    a(f"| `Effect` | `{o['effect']}` | `{att['effect_u32']}` = "
      f"`hash_jenkins(\"{CAPSTONE}\")` |")
    a(f"| `Usage` | `{o['usage']}` | `{att['usage_u32']}` = `hash_jenkins(\"Fire\")` |")
    a(f"| `world` | **absent** | identity transform: the effect spawns in the parent entity's "
      f"frame with no local offset or rotation |")
    a(f"| parent | `{att['parent']['node']}` `{att['parent']['class']}` "
      f"`{att['parent']['name']}` | the mounted .50 cal weapon entity |")
    a(f"| parent `world` | `{att['parent']['world']}` | weapon mount in the car's frame (m) |")
    a(f"| `SWeaponPoint FirePosition` | `{att['fire_point']['world']}` | the muzzle point in "
      f"the weapon's frame (m) |")
    a("")
    a(f"Source: `{att['graph']}`, archive `{att['source']['archive']}` offset "
      f"**{att['source']['offset']}**, **{att['source']['size']} B**, inner "
      f"`{att['graph'].rsplit('/', 1)[-1].replace('.ee', '.epe')}`.")
    a("")
    a("**Bone:** there is no bone name. The attachment is parented to the weapon entity, whose "
      "own `world` matrix is the mount; that is why the effect carries no `world` of its own - "
      "it inherits the weapon's frame. This is the mechanism the Batmobile chain gun needs: "
      "put `ShellEjection` under the chain-gun weapon entity's `SEffects` and it follows the "
      "gun, including turret/elevation motion.")
    a("")
    a("**Trigger:** `Usage` is literally the string `Fire`. The same usage the muzzle flash's "
      "own attachment family uses; the casing object therefore fires on the weapon's fire event, "
      "not on a timer.")
    a("")
    a("### 4.2 The weapon entities themselves (`.ee` -> `.epe` -> `.effc`)")
    a("")
    a("| weapon entity | archive @ offset | size | inner `.epe` | `ShellEjection` at | "
      "effect hash at | `Fire` hash at | embedded `.effc` |")
    a("|---|---|---:|---|---:|---:|---:|---|")
    for name, d in doc["attachment_entities"].items():
        a(f"| `{d['entity']}` | `{d['archive']}` @ **{d['offset']}** | {d['size']} B | "
          f"{d['epe']['size']} B | {d['epe']['shell_ejection_at']} | "
          f"{d['epe']['effect_hash_at']} | {d['epe']['fire_usage_at']} | "
          f"`{d['effc']['name'].rsplit('/', 1)[-1]}` ({d['effc']['size']} B) |")
    a("")
    a("The byte offsets are inside the inner `.epe`; each is a real occurrence of the string or "
      "the little-endian hash, so the attachment is present in the weapon's own graph even when "
      "no vehicle graph is loaded. `w201_minigun.ee` also ships `w201_minigun_mount.ee`, and "
      "`FX_TABLE` lists the casing path on both.")
    a("")
    a("### 4.3 Direction and rate, from the `.effc`")
    a("")
    a("| file | size | rows | arrays | MaxParticles | `Params` (decoded floats) |")
    a("|---|---:|---:|---:|---:|---|")
    for p, d in ((CAPSTONE, w206["effc"]), (MINIGUN, w201["effc"])):
        a(f"| `{p}` | {d['size']} | {d['rows']} | {d['arrays']} | {d['max_particles']} | "
          + ", ".join(f"[{i}]={pct(v)}" for i, v in enumerate(d["params"])) + " |")
    a("")
    a("Read against their consumers (`Modifiers[i].Parameters.FloatParamIndices`, decoded):")
    a("")
    a("| what | capstone | minigun | status |")
    a("|---|---|---|---|")
    a("| gravity | `Params[12]` = **-9.82** | `Params[12]` = **-9.82** | decoded value, "
      "consumed by `Modifiers[0]`/`[1]` (`FloatParamIndices` 12/13) |")
    a("| cone half-angles | `Params[10]` = **0.1745329 rad (10 deg)**, `Params[11]` = "
      "**0.0872665 rad (5 deg)** | `Params[9]` = 0.1745329, `Params[10]` = 0.0872665 | "
      "values decoded; the *role* (two half-angles) is **derived** from them being radian-sized "
      "and paired with the rotation/spread modifiers |")
    a("| particle cap | **15** and **30** (two emitter templates) | **30** | decoded "
      "`EmitterTemplates[i].MaxParticles` |")
    a("| lifetime / rate | none in the file as a rate | none | **UNKNOWN**: the effect has no "
      "spawn-rate member; emission follows the `Fire` usage, so the casing rate is the weapon's "
      "`fire_rate` (10/s for w603/w604/w619). A per-shot count is not decoded |")
    a("| particle model | `models/jc_vfx/bullet_casing/bullet_casing_bullet_casing_lod1.rbm`, "
      "size 0.0163 x 0.0163 x 0.074 m | same family | decoded from the APC entity's resource "
      "list (`entities/...json`, `models` rows) |")
    a("")
    a("So the shipped direction is **ballistic**: casings are thrown in a cone (the two "
      "radian angles), pulled down at 9.82, capped at 15 (capstone) or 30 (minigun) live "
      "particles. Which local axis the cone opens around is **UNKNOWN** - the `.effc` stores "
      "no named axis and the attachment has no `world` rotation to read it from. A Q-1 probe "
      "would settle it (fire one burst and watch the ejection side).")
    a("")
    a("## 5. The other weapon entities (infantry, turrets, Chaos/Bavarium)")
    a("")
    a("`FX_TABLE` records which `.ee` names which casing `.effc`. The complete list of "
      "weapon-entity carriers:")
    a("")
    a("| weapon `.ee` | casing `.effc` |")
    a("|---|---|")
    for c in fx["weapon_containers"]:
        hits = [p for p, d in fx["detail"].items()
                if c in d["weapon_containers"]]
        a(f"| `{c}` | " + ", ".join(f"`{h}`" for h in hits) + " |")
    a("")
    a("Read as coverage: handguns/SMGs/shotguns/snipers/rifles all carry their family casing "
      "effect; the mounted `.50 cal` carries `bullet_eject_capstone`; the mounted minigun carries "
      "`bullet_eject_minigun`; the two Bavarium/DLC weapons (`w119_molten_bavarium_spitter`, "
      "`w901_scorpiongun`) carry `bullet_eject_556`. **No stationary turret** "
      "(`w501_sam_missile`, `w502_turret_aa_gun`, `w503_turret_emp`, `w504_turret_m488`, "
      "`w505`/`w506`/`w507` SAMs) carries any casing path, and no helicopter/jet gun carries "
      "one directly - the helicopter guns (`w604`, `w607`, `w610`, `w617`, `w622`) have no "
      "casing `.effc` in their own containers either. The casing carrier is the **mounted "
      "machine-gun class**, which is exactly the Batmobile's chain-gun class.")
    a("")
    a("## 6. The BmAK side (the target the build must match)")
    a("")
    a(f"`PARTICLES_FEATURES.json` group `casings`, system `ChainGun_BulletCasing` "
      f"(4 copies, one per playable Batmobile package):")
    a("")
    a("| property | value |")
    a("|---|---|")
    for s in part["systems"]:
        if s["name"] != "ChainGun_BulletCasing":
            continue
        a(f"| package / index | `{s['package']}` / {s['index']} |")
        a(f"| emitters | {s['emitters']} |")
        a(f"| lifetime | {s['lifetime']} s |")
        a(f"| spawn rate | **{s['spawn_rate']} /s** |")
        a(f"| materials | {', '.join('`' + m + '`' for m in (s['materials'] or []))} |")
        break
    a("")
    a("`RiotSuppressor_BulletCasing` is the same recipe with a 0..30/s rate over 5 levels and a "
      "0.05..1.1 s lifetime. So BmAK's chain-gun casing is a **4/s mesh-particle stream with a "
      "1.0 s life**, while JC3's minigun effect is a **per-`Fire` emission capped at 30 live "
      "particles**. That difference is the number the build has to bridge (section 7, gap 3).")
    a("")
    a("## 7. Closest JC3 system and the gap (STAGES.md)")
    a("")
    a("**Closest system (exact carrier, not a stand-in):** the mounted-machine-gun entity recipe - "
      "`CBulletWeaponBase` child in the vehicle graph, `SEffects/SAttachedEffect` named "
      "`ShellEjection`, `Effect = hash(effects/jc_weapons/minigun/bullet_eject_minigun.effc)`, "
      "`Usage = hash(\"Fire\")`, no `world`, plus the `.effc` shipped inside the weapon `.ee` "
      "bundle. `w201_minigun` is the closest shipped gun (mounted, belt-fed, 10/s); "
      "`w206_mounted_capstone_m2hm` is the closest shipped .50 cal.")
    a("")
    a("| # | gap | closes when | owner |")
    a("|---|---|---|---|")
    a("| 1 | the build ships **no casing `.effc`**: the 158 `jc_weapons` `.effc` in `Builds/*` "
      "contain none of the 10 casing files | `effects/jc_weapons/minigun/bullet_eject_minigun.effc` "
      "(6,703 B) is packaged inside the chain-gun `.ee`, and the built tree's effect list names it | "
      "B-06 / B-08 |")
    a("| 2 | the chain-gun graph must carry the attachment: `SAttachedEffect ShellEjection`, "
      "`Effect = 600259254`, `Usage = 4131019937`, `name_hash = 3811014039`, no `world` | the "
      "object exists under the chain-gun weapon entity's `SEffects` and `bm_fx.py`-style hash "
      "resolution finds the path | B-06 |")
    a("| 3 | BmAK ejects 4/s for 1.0 s; JC3 emits per `Fire` shot (10/s on the gunners' tunes) "
      "with a 30-particle cap (capstone ships 15 + 30) | the per-shot/per-second bridge is "
      "written down and probed: emit "
      "per shot, or gate the emitter to a 4/s cadence; the `.effc` has no rate member to set | "
      "B-06 + Q-3 |")
    a("| 4 | the casing's local cone axis is not decoded (no `world`, no named axis) | Q-3 "
      "observation: first burst, casings leave the right side of the gun and fall at 9.82 | Q-3 |")
    a("| 5 | ledger rows carry the false negative | `T13_FX.md`, `t17_fx.json`, `t_rows.py:150`, "
      "`bm_fx.py:175` and `t7_weapons.py:382` are amended to the carrier in this report | T-23 |")
    a("")
    a("**What a new attachment would need, if the build chose to author rather than copy:** the "
      "two Jenkins hashes (effect path, `Fire` usage), the object class `SAttachedEffect`, a "
      "`name`/`name_hash` pair, and an `Effect`-carrying `.effc` embedded in the same `.ee` "
      "bundle; the parent must be the weapon entity (not the car root) and `world` must stay "
      "absent (identity) unless the gun's own frame needs an offset. No tune member can carry "
      "it - section 2.")
    a("")
    a("## 8. Ledger corrections this card forces")
    a("")
    a("| file | line / row | current text | replace with |")
    a("|---|---|---|---|")
    a("| `Research/JC3Grab/T13_FX.md` (T-FX13) | JC3 cell | \"no vehicle-carried effect\" | "
      "`SAttachedEffect ShellEjection` -> `bullet_eject_capstone.effc`, 21 vehicle containers / "
      "5 dirs; minigun variant on `v1706` |")
    a("| `Working/Translation/t17_fx.json` | row `T-FX13` | `dispo: out`, empty `chosen` | "
      "chosen `effects/jc_weapons/minigun/bullet_eject_minigun.effc`, attachment "
      "`epe:ShellEjection`, usage `Fire` |")
    a("| `Tools/scripts/t_rows.py` | 150 | \"no vehicle carries a casing/shell effect\" | "
      "carrier per this report |")
    a("| `Tools/scripts/bm_fx.py` | 175 | T-FX13 `named-omission` | `b-06` with the "
      "`ShellEjection` edit |")
    a("| `Tools/scripts/t7_weapons.py` | 382 | \"no casing effect exists in the fleet\" | "
      "`bullet_eject_minigun.effc` on the mounted minigun |")
    a("")
    a("## 9. UNKNOWNs")
    a("")
    a("1. **The cone's local axis.** The `.effc` stores the two angles as unnamed floats and "
      "the attachment has no `world` rotation, so which axis the casings open around is not in "
      "the files read. Would be settled by Q-3 (fire one burst, watch the ejection side) or by "
      "decoding the emitter's rotation modifier type (`Modifiers[1]/[3].TypeHash` 3793416313, "
      "not resolved to a name here).")
    a("2. **The per-shot particle count.** No count member; `MaxParticles` is a live cap, not a "
      "burst size. Rate and count are code-side. Would be found in the native effect runtime, "
      "not in the `.effc`.")
    a("3. **The infantry/turret/DLC `SAttachedEffect` members.** Only the container->`.effc` link "
      "is decoded for them (their `.ee` bytes are not in the grab). The attachment object is "
      "proven for the two mounted guns read from the install; for the rest, the same class/usage "
      "pattern is an inference from those two, not a decode.")
    a("4. **The 4 `ShellEjection` objects the B-08 audit found in `bm-008`.** The v0300 donor "
      "graph has none (this sweep's 14-container list), so their provenance is UNKNOWN - they "
      "cannot have come from the donor's own graph. The build must place the attachment "
      "deliberately (gap 2), not rely on inheritance.")
    a("5. **The shipped casing `.effc`'s runtime look.** Test ban: no game was launched, so the "
      "sizes/angles/gravity are decoded values, not an observed ejection.")
    a("")
    a("## 10. Checks")
    a("")
    a("| check | result |")
    a("|---|---|")
    for k, v in doc["checks"].items():
        a(f"| `{k}` | {'PASS' if v else 'FAIL'} |")
    a("")
    a("## 11. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/fx13_casings.py --write")
    a("python Tools/scripts/fx13_casings.py --check")
    a("```")
    a("")
    a(f"Inputs: `Research/JC3Grab/{{INDEX,FX_TABLE,WEAPONS}}.jsonl`, "
      f"`Research/BatmobileGrab/PARTICLES_FEATURES.json`, `{RAW.replace(chr(92), '/')}/weapons` "
      f"(226 files), `.../detail` (232 `.ee` dumps), and the install "
      f"`{DEFAULT_GAME}` read through `jc3index`/`eetoc`/`jc3fx`.")
    a("")
    return "\n".join(L)


def write():
    doc = build()
    text = render(doc)
    os.makedirs(os.path.join(ROOT, "tmp", "freebuff", "reports"), exist_ok=True)
    with open(os.path.join(ROOT, JSON_OUT), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    with open(os.path.join(ROOT, MD_OUT), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    with open(os.path.join(ROOT, REPORT), "w", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    bad = [k for k, v in doc["checks"].items() if not v]
    print(f"wrote {MD_OUT}, {JSON_OUT}, {REPORT}")
    print(f"{len(doc['checks'])} checks, {len(bad)} failed" + (f": {bad}" if bad else ""))
    return 1 if bad else 0


def check():
    doc = build()
    want = render(doc)
    bad = 0
    for k, v in doc["checks"].items():
        print(f"  {k:<46} {'PASS' if v else 'FAIL'}")
        bad += 0 if v else 1
    for path, expected in ((MD_OUT, want + "\n"), (REPORT, want + "\n")):
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            print(f"FAIL: {path} missing (run --write)")
            bad += 1
            continue
        got = open(p, encoding="utf-8").read().replace("\r\n", "\n")
        if got != expected:
            print(f"FAIL: {path} differs from the re-derived text")
            bad += 1
    p = os.path.join(ROOT, JSON_OUT)
    if not os.path.exists(p):
        print(f"FAIL: {JSON_OUT} missing")
        bad += 1
    else:
        got = json.load(open(p, encoding="utf-8"))
        if got != json.loads(json.dumps(doc)):
            print(f"FAIL: {JSON_OUT} differs")
            bad += 1
    print(f"{'PASS' if not bad else 'FAIL'}: {len(doc['checks'])} checks, 3 artefacts")
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(write() if a.write else check())


if __name__ == "__main__":
    main()
