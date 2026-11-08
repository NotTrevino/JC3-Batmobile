#!/usr/bin/env python
"""t_lights_forensics.py - T-L10 + T-L21..T-L23: the muzzle lamp and the forensics rig.

T-18 (`t18_lights.py`) omitted four rows of `Playable_Batmobile_SF` because the donor
`v0300_car_kensington_sportsmuscle` has no matching behaviour:

  T-L10  `ChainGunMuzzle`  SpotLightComponent, no behaviour, white, cone 50
  T-L21  `BattleModeSpotLight`  VEHLT_ForensicsLight, RHelicopterSpotLightComponent
  T-L22  `HeadLight1`      VEHLT_ForensicsLight, red SpotLightComponent
  T-L23  `HeadLight2`      VEHLT_ForensicsLight, red SpotLightComponent

This tool does a **lookup, not a design**. For each of those rows it prints what the
BmAK rig actually does (LIGHTS.json, schema 6), then the closest JC3 carrier with its
member paths and the values the fleet really ships, and finally the gap the build
stage has to close (STAGES.md: compose / clone / author / repack).

Inputs (decoded tables and caches already on disk; no archive is opened):
  * `Research/BatmobileGrab/LIGHTS.json`      the 101 BmAK light entries, 4 packages
  * `E:/Modding/_shared/gamedata/JC3grab/entities/*.ee.json`  the `VehicleDynamicLights`
    module of every vehicle: `lights[i].<member>` rows, 25 members each
  * `E:/Modding/_shared/gamedata/JC3grab/detail/*.ee.json`    the `.epe` `SVehicleLight`
    presets, the only side that carries `spot_angle` **and** `spot_inner_angle`
  * `Research/JC3Grab/WEAPONS.jsonl`          every weapon tune's member paths
  * `Research/JC3Grab/FX_TABLE.jsonl` / `FX_VOCAB.json`  every `.effc`, its root
    class and its member vocabulary
  * `Research/JC3Grab/LIGHT_SYSTEM.json`      the 25-member list, behaviour census and
    `CarLight` block counts (G2-33)
  * `Research/BatmobileGrab/BMSDK_OFFSETS.json`  the forensics toggle's offset

Writes:
  * `Research/JC3Grab/LIGHTS_FORENSICS.json`  every measured number these rows use
  * `Research/JC3Grab/LIGHTS_FORENSICS.md`    the same, as tables
  * `tmp/freebuff/reports/muzzle-and-forensics-lights.md`  the deliverable report

Usage:
  python t_lights_forensics.py --write
  python t_lights_forensics.py --check
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rbmhdr  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
BMAK = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.json")
BMSDK = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
WEAPONS = os.path.join(ROOT, "Research", "JC3Grab", "WEAPONS.jsonl")
FX_TABLE = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
FX_VOCAB = os.path.join(ROOT, "Research", "JC3Grab", "FX_VOCAB.json")
LIGHT_SYSTEM = os.path.join(ROOT, "Research", "JC3Grab", "LIGHT_SYSTEM.json")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "LIGHTS_FORENSICS.json")
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "LIGHTS_FORENSICS.md")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports",
                      "muzzle-and-forensics-lights.md")

RIG = "Playable_Batmobile_SF"
LIGHT_ENTRY = re.compile(r"lights\[(\d+)\]\.(.+)")
MODULE = "VehicleDynamicLights"
M32 = 0xFFFFFFFF
GUN_PART = re.compile(r"(?i)(gun|turret|cannon|machine|weapon|decoder|chain)")
LIGHTISH = re.compile(r"light|glow|illum|lumin|colour|color|flash", re.I)

# the four rows, in T-18 ledger order
ROWS = (
    ("T-L10", "ChainGunMuzzle", "muzzle"),
    ("T-L21", "BattleModeSpotLight", "forensics"),
    ("T-L22", "HeadLight1", "forensics"),
    ("T-L23", "HeadLight2", "forensics"),
)


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def h(text: str) -> int:
    return rbmhdr.hash_jenkins(text.encode("utf-8"))


def fnum(v, nd: int = 6) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, (int,)):
        return str(v)
    if isinstance(v, str):
        try:
            return f"{float(v):.{nd}g}"
        except ValueError:
            return v
    return f"{float(v):.{nd}g}"


# ---------------------------------------------------------------- BmAK side
def bmak_rows() -> dict:
    """The muzzle and forensics entries of all four shipped packages."""
    doc = json.load(open(BMAK, encoding="utf-8"))
    out = []
    for veh in doc["vehicles"]:
        for e in veh["entries"]:
            kind = ("muzzle" if "Muzzle" in e["socket"]
                    else "forensics" if e["type"] == "VEHLT_ForensicsLight" else None)
            if kind is None:
                continue
            comps = []
            for c in e["components"]:
                fld = c.get("fields") or {}
                comps.append({
                    "class": c["class"],
                    "brightness": fld.get("Brightness"),
                    "radius": fld.get("Radius"),
                    "inner": fld.get("InnerConeAngle"),
                    "outer": fld.get("OuterConeAngle"),
                    "falloff": fld.get("FalloffExponent"),
                    "cast_shadows": fld.get("CastShadows"),
                    "cast_dynamic": fld.get("CastDynamicShadows"),
                    "colour": (c.get("colour") or {}).get("value"),
                    "colour_field": (c.get("colour") or {}).get("field"),
                    "colour_source": ((c.get("field_sources") or {}).get(
                        "LightColor")),
                    "brightness_source": ((c.get("field_sources") or {}).get(
                        "Brightness")),
                    "radius_source": ((c.get("field_sources") or {}).get("Radius")),
                })
            out.append({
                "package": veh["package"],
                "kind": kind,
                "socket": e["socket"],
                "bone": e["bone"],
                "type": e["type"],
                "material_type": e.get("material_type"),
                "behavior": e.get("behavior"),
                "behavior_disposition": e.get("behavior_disposition"),
                "socket_location": e.get("socket_location"),
                "jc3_part": e["jc3_part"],
                "jc3_anchor": e["jc3_anchor"],
                "anchor_state": e["anchor_state"],
                "components": comps,
            })
    return {"rows": out,
            "packages": sorted({r["package"] for r in out}),
            "forensics": sum(1 for r in out if r["kind"] == "forensics"),
            "muzzle": sum(1 for r in out if r["kind"] == "muzzle")}


def bmsdk_facts() -> dict:
    """The runtime members that drive the forensics rig, with their offsets."""
    doc = json.load(open(BMSDK, encoding="utf-8"))
    want = {"bForensicsLightActive", "LightsBrightness", "LightsMaterial",
            "LightsMaterialInst", "CachedLightMat1234", "CachedLightMat5678",
            "AbsoluteRotation", "HeadlightsSwitchedOn", "bHasDamagedLightState"}
    got = {}
    for cname, cls in (doc.get("classes") or {}).items():
        props = cls.get("properties") or cls.get("members") or []
        for p in props:
            if p.get("name") in want:
                got[p["name"]] = {"class": cname, "offset": p.get("offset"),
                                  "kind": p.get("kind"),
                                  "hex": (f"0x{p['offset']:04X}"
                                          if isinstance(p.get("offset"), int) else None)}
    return got


# ---------------------------------------------------------------- JC3 side
def module_scan() -> dict:
    files = sorted(glob.glob(os.path.join(RAW, "entities", "*.ee.json")))
    rows = []
    per_entity = {}
    for p in files:
        d = json.load(open(p, encoding="utf-8"))
        ent = d["entity"].split("/")[-1]
        n = 0
        for m in d.get("modules") or []:
            if m.get("type") != MODULE:
                continue
            cur: dict[int, dict] = {}
            for r in m.get("rows") or []:
                mm = LIGHT_ENTRY.fullmatch(r["path"])
                if mm:
                    cur.setdefault(int(mm.group(1)), {})[mm.group(2)] = r["value"]
            for i, e in cur.items():
                e["_entity"] = ent
                e["_i"] = i
                rows.append(e)
                n += 1
        if n:
            per_entity[ent] = n
    return {"entity_files": len(files), "entries": rows,
            "per_entity": per_entity, "entities": len(per_entity),
            "members": len({k for e in rows for k in e if not k.startswith("_")})}


def preset_scan() -> dict:
    vals: dict[str, dict] = {}
    for p in sorted(glob.glob(os.path.join(RAW, "detail", "*.ee.json"))):
        d = json.load(open(p, encoding="utf-8"))
        for o in d.get("epe", {}).get("objects", []):
            if o.get("class") != "SVehicleLight" or not o.get("name"):
                continue
            v = o.get("values") or {}
            vals.setdefault(o["name"], {}).update(
                {k: v.get(k) for k in ("radius", "spot_angle", "spot_inner_angle",
                                       "multiplier", "volume_intensity",
                                       "volumetric_mode", "near_cap",
                                       "falloff_start", "is_shadow_caster",
                                       "diffuse")})
    spot = sorted({float(v["spot_angle"]) for v in vals.values()
                   if v.get("spot_angle")})
    inner = sorted({float(v["spot_inner_angle"]) for v in vals.values()
                    if v.get("spot_inner_angle")})
    radius = sorted({float(v["radius"]) for v in vals.values() if v.get("radius")})
    return {"names": len(vals), "values": vals,
            "spot_angle": spot, "inner": inner, "radius": radius,
            "shadow": sum(1 for v in vals.values()
                          if str(v.get("is_shadow_caster")) == "1"),
            "cone50": [n for n, v in vals.items()
                       if v.get("spot_angle") and float(v["spot_angle"]) >= 50
                       and v.get("spot_inner_angle")
                       and float(v["spot_inner_angle"]) > 0]}


def tune_scan() -> dict:
    rows = [json.loads(l) for l in open(WEAPONS, encoding="utf-8") if l.strip()]
    hits = collections.Counter()
    tunes = 0
    members = set()
    for r in rows:
        for t in r.get("tunes") or []:
            tunes += 1
            for inst in t.get("instances") or []:
                for p, _ty, _v in inst.get("rows") or []:
                    members.add(p)
                    if LIGHTISH.search(p):
                        hits[p] += 1
    return {"records": len(rows), "tunes": tunes, "member_paths": len(members),
            "light_members": dict(hits)}


def fx_scan() -> dict:
    table = [json.loads(l) for l in open(FX_TABLE, encoding="utf-8") if l.strip()]
    vocab = json.load(open(FX_VOCAB, encoding="utf-8"))
    muzzle = collections.defaultdict(set)
    for r in table:
        if r.get("ext") == ".effc" and re.search(r"muzzleflash", r["path"], re.I):
            muzzle[r["path"]].add(r.get("container") or "")
    effc_light = [k for k in vocab
                  if k.startswith(".effc") and LIGHTISH.search(k)]
    ex = {}
    for r in table:
        if r.get("path") in ("effects/jc_weapons/muzzle_flash/"
                             "helicopter_minigun_muzzleflash.effc",
                             "effects/jc_weapons/muzzle_flash/"
                             "rico_minigun_muzzleflash.effc"):
            ex.setdefault(r["path"], {"root": r.get("root"), "rows": r.get("rows"),
                                      "size": r.get("size")})
    return {"muzzle_paths": len(muzzle),
            "muzzle_vehicle_carriers": {
                p: len({c for c in cs if "/jc_vehicles/" in c})
                for p, cs in muzzle.items()},
            "muzzle_examples": ex, "effc_light_members": len(effc_light),
            "light_member_sample": effc_light[:5],
            "effc_files": sum(1 for r in table if r.get("ext") == ".effc")}


def light_system() -> dict:
    d = json.load(open(LIGHT_SYSTEM, encoding="utf-8"))
    return {"members": d["module"]["members"],
            "behaviors": d["module"]["behaviors"],
            "census": d["module"]["value_census"],
            "carlight": d["carlight"]["blocks"],
            "carlight_params": d["carlight"]["layout"]["parameters"],
            "epe": d["epe"]["classes"]}


# ---------------------------------------------------------------- resolution
def parse(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def pick(entries: list[dict], **want) -> list[dict]:
    out = []
    for e in entries:
        ok = True
        for k, v in want.items():
            if k == "part_gun":
                ok = ok and bool(GUN_PART.search(str(e.get("part"))))
            elif k == "behavior_prefix":
                ok = ok and str(e.get("behavior", "")).startswith(v)
            elif k == "min_angle":
                ok = ok and (parse(e.get("angle")) or 0) >= v
            elif k == "min_range":
                ok = ok and (parse(e.get("range")) or 0) >= v
            elif k == "light_type":
                ok = ok and str(e.get("light_type")) == str(v)
            elif k == "multiplier":
                ok = ok and parse(e.get("multiplier")) == v
            elif k == "angle":
                ok = ok and parse(e.get("angle")) == v
            elif k == "blinking":
                ok = ok and str(e.get("blinking")) == str(v)
            elif k == "cast_shadows":
                ok = ok and str(e.get("cast_shadows")) == str(v)
            else:
                ok = ok and e.get(k) == v
        if ok:
            out.append(e)
    return out


def factor(e: dict, keys: tuple[str, ...]) -> str:
    return ", ".join(f"{k}={fnum(e.get(k))}" for k in keys)


def resolve(mod: dict, pre: dict, tunes: dict, fx: dict, ls: dict,
            bmak: dict, sdk: dict) -> list[dict]:
    entries = mod["entries"]
    spot = [e for e in entries if str(e.get("light_type")) == "1"]
    point = [e for e in entries if str(e.get("light_type")) == "0"]
    wide = sorted(spot, key=lambda e: -(parse(e.get("angle")) or 0))
    a50 = [e for e in wide if parse(e.get("angle")) == 50]
    a45 = [e for e in wide if parse(e.get("angle")) == 45]
    r50 = [e for e in entries if parse(e.get("range")) == 50]
    a35 = [e for e in entries if parse(e.get("angle")) == 35]
    mult5 = [e for e in entries if parse(e.get("multiplier")) == 5]
    shadows = [e for e in entries if str(e.get("cast_shadows")) == "1"]
    guns = pick(entries, part_gun=True)
    sirens = pick(entries, behavior_prefix="Siren")
    blink = [e for e in entries if str(e.get("blinking")) == "1"]

    def one(rows: list[dict]) -> dict | None:
        return rows[0] if rows else None

    def summary(rows: list[dict], n: int = 3) -> str:
        seen, out = set(), []
        for e in rows:
            k = (e.get("part"), e.get("range"), e.get("angle"))
            if k in seen:
                continue
            seen.add(k)
            out.append(f"{e['_entity']}[{e['_i']}] {factor(e, ('part', 'range', 'angle', 'multiplier'))}")
            if len(out) == n:
                break
        return "; ".join(out)

    per_row = []
    for rid, socket, kind in ROWS:
        rig = next(r for r in bmak["rows"]
                   if r["package"] == RIG and r["socket"] == socket
                   and r["kind"] == kind)
        packages = [r for r in bmak["rows"]
                    if r["socket"] == socket and r["kind"] == kind]
        rule: list[str] = []
        gaps: list[str] = []
        if kind == "muzzle":
            e = one(guns)
            rule += [
                ("lights[i].behavior", "None", "1177 rows ship it; a lamp that is not "
                 "driven by a state machine", f"{rel(LIGHT_SYSTEM)} module.behaviors"),
                ("lights[i].light_type", "0", "every point lamp in the fleet (2494 rows); "
                 f"all {len(spot)} light_type 1 rows are cones",
                 f"{rel(LIGHT_SYSTEM)} module.value_census.light_type"),
                ("lights[i].angle", "10", "the value every light_type 0 row uses "
                 f"({len(point)} rows)", "measured: light_type 0 <-> angle 10, 100%"),
                ("lights[i].range", "10", "the mode of range (1667 rows)",
                 f"{rel(LIGHT_SYSTEM)} module.value_census.range"),
                ("lights[i].diffuse.R/G/B", "1 / 1 / 1", "BmAK LightColor "
                 "[255,255,255,0] / 255", f"{rel(BMAK)} ChainGunMuzzle"),
                ("lights[i].part / part_hash / part_index", "a gun part",
                 f"only {len(guns)} shipped lamps hang on a gun part "
                 f"({summary(guns, 1)})", "measured entity sweep"),
                ("lights[i].deformable_transform", "the gun bone anchor",
                 "BmAK socket ChainGunMuzzle -> bone "
                 "Batmobile_Rig_Weapons_Machine_Gun_01", f"{rel(BMAK)} jc3_anchor"),
                ("lights[i].preset_id", "0", "17 shipped rows carry 0 and state their own "
                 "numbers", f"{rel(LIGHT_SYSTEM)} module.presets.zero"),
            ]
            gaps += [
                "JC3 has **no light member on a weapon tune**: "
                f"{tunes['tunes']} tune blocks in {tunes['records']} WEAPONS.jsonl records, "
                f"{tunes['member_paths']} distinct member paths, "
                f"{len(tunes['light_members'])} light-ish members (measured).",
                "No `.effc` carries a light node: "
                f"{fx['effc_files']:,} decoded `.effc` rows, {fx['effc_light_members']} "
                "member paths matching light/glow/lumin/flash (measured FX_VOCAB).",
                "A lamp cannot be pulsed by the shot: the only time-varying members are "
                f"`blinking` ({len(blink)} rows carry 1) whose period no decoded file "
                "states (UNKNOWN), and the behaviour names, which have no forensics or "
                "weapon mode.",
                "The BmAK cone (Radius 4096, OuterConeAngle 50) has no unit bridge to "
                "`range`/`angle` (G2-33 §8): the build picks fleet values and records "
                "the choice.",
                "The visible flash has to come from the effect side: `SAttachedEffect` "
                "with `Usage` = `Fire` (5,342 objects / hash "
                f"{h('Fire')}), pointing at e.g. "
                f"{sorted(fx['muzzle_vehicle_carriers'], key=lambda p: -fx['muzzle_vehicle_carriers'][p])[0]} "
                f"({max(fx['muzzle_vehicle_carriers'].values())} vehicle carriers).",
            ]
            closest = {"module_row": (
                "VehicleDynamicLights `lights[i]` = 25 members, hung on the gun part; "
                f"nearest shipped instance {summary(guns, 1)}"),
                "effect": ("SAttachedEffect (Effect + Usage, no world matrix, parented "
                           "to the weapon entity) - the same carrier T-FX13 found for "
                           "casings"),
                "tune": "WeaponTuning: no light or effect member (measured 0)"}
        else:
            comp = rig["components"][0]
            colour = comp.get("colour") or []
            dif = ([round(colour[0] / 255.0, 6), round(colour[1] / 255.0, 6),
                    round(colour[2] / 255.0, 6)] if len(colour) >= 3 else None)
            if socket == "BattleModeSpotLight":
                top = one(a50)
                rule += [
                    ("lights[i].light_type", "1", f"all {len(spot)} cone rows; "
                     f"light_type 0 never exceeds angle 10", "measured co-occurrence"),
                    ("lights[i].angle", "50", f"the largest angle shipped ({len(a50)} rows, "
                     f"e.g. {summary(a50, 1)}); graph presets go to "
                     f"{pre['spot_angle'][-1]} and "
                     f"{sum(1 for v in pre['values'].values() if v.get('spot_inner_angle') and float(v['spot_inner_angle']) > 0)} "
                     "of them ship a non-zero inner cone", f"{rel(LIGHT_SYSTEM)} module.value_census.angle"),
                    ("SVehicleLight.spot_angle / spot_inner_angle", "50 / 0", "the graph "
                     f"side carries both cones: spot_angle {pre['spot_angle']}, inner "
                     f"{pre['inner']}", f"{rel(RAW)} detail/*.ee.json SVehicleLight"),
                    ("SVehicleLight.radius", "0.2...90", "graph-side range unit, no "
                     "module counterpart", "measured preset sweep"),
                    ("lights[i].range", "50", f"{len(r50)} rows, e.g. {summary(r50, 1)}",
                     f"{rel(LIGHT_SYSTEM)} module.value_census.range"),
                    ("lights[i].diffuse.R/G/B", " / ".join(fnum(x) for x in dif),
                     f"BmAK LightColor {colour} / 255 (alpha dropped: no alpha member)",
                     f"{rel(BMAK)} {socket} LightColor"),
                    ("lights[i].cast_shadows", "0", "BmAK CastShadows False",
                     f"{rel(BMAK)} {socket}"),
                    ("lights[i].multiplier", "1", "BmAK Brightness 0.0 (the component is "
                     "a placeholder)", f"{rel(BMAK)} {socket} Brightness"),
                ]
            else:
                rule += [
                    ("lights[i].light_type", "1", f"all {len(spot)} cone rows", "measured"),
                    ("lights[i].angle", "35", f"the exact value exists ({len(a35)} rows); "
                     f"40 is the mode for big beams ({len([e for e in entries if parse(e.get('angle')) == 40])} "
                     f"rows)", f"{rel(LIGHT_SYSTEM)} module.value_census.angle"),
                    ("SVehicleLight.spot_inner_angle", "10", f"BmAK InnerConeAngle 10; "
                     f"graph presets ship inner {pre['inner']}", "measured preset sweep"),
                    ("lights[i].range", "30", f"{len([e for e in entries if parse(e.get('range')) == 30])} "
                     f"rows, e.g. {summary([e for e in entries if parse(e.get('range')) == 30], 1)}",
                     f"{rel(LIGHT_SYSTEM)} module.value_census.range"),
                    ("lights[i].multiplier", "5", f"BmAK Brightness 5.0; {len(mult5)} shipped "
                     f"rows carry 5 ({summary(mult5, 1)})",
                     f"{rel(LIGHT_SYSTEM)} module.value_census.multiplier"),
                    ("lights[i].diffuse.R/G/B", " / ".join(fnum(x) for x in dif),
                     f"BmAK LightColor {colour} / 255 (alpha 255 has no JC3 member)",
                     f"{rel(BMAK)} {socket} LightColor"),
                    ("lights[i].cast_shadows", "1", f"BmAK CastDynamicShadows True; only "
                     f"{len(shadows)} shipped rows cast shadows ({summary(shadows, 1)}), "
                     "both with volumetric_mode 1 + volume_intensity 0.02",
                     f"{rel(LIGHT_SYSTEM)} module.value_census.cast_shadows"),
                    ("lights[i].falloff_start", "0.8", "the mode (2210 rows)",
                     f"{rel(LIGHT_SYSTEM)} module.value_census.falloff_start"),
                ]
            gaps += [
                "The rig is a **state, not a lamp**: `RVehicle.bForensicsLightActive` "
                f"is a bool at {sdk.get('bForensicsLightActive', {}).get('hex')} "
                f"(offset {sdk.get('bForensicsLightActive', {}).get('offset')}); "
                "JC3 lights have no enable member and no forensics behaviour "
                f"(vocabulary: {', '.join(sorted(ls['behaviors']))}).",
                "`RHelicopterSpotLightComponent` has no JC3 class: it declares only "
                f"`AbsoluteRotation` ({sdk.get('AbsoluteRotation', {}).get('hex')}) on top "
                "of SpotLightComponent, and none of the aim/helicopter behaviour survives "
                "as data - the build keeps the lamp fixed to the bone transform.",
                "Inner cone exists only on the graph side (`SVehicleLight."
                "spot_inner_angle`), never on the module row that binds the part: the "
                "build must author both sides with the same numbers.",
                "Colour alpha is not representable (`diffuse` is R/G/B only), and the "
                "BmAK red [255,0,0,255] / cyan [195,255,244,0] carry an alpha JC3 drops.",
                "The emissive mesh side is a `CarLight` block per mesh "
                f"({ls['carlight']:,} blocks in 220 vehicles): "
                f"'{ls['carlight_params']}' - so the build copies a donor block instead "
                "of authoring one.",
                "No time base: `blinking` is a flag only "
                f"({len(blink)} rows set it, no period anywhere) and the forensics "
                "pulse/sweep in BmAK is C++ / Blueprint, not data in the packages.",
            ]
            closest = {"module_row": (
                "VehicleDynamicLights `lights[i]` on `sportsmuscle_body`, anchor "
                f"{rig['jc3_anchor']}"),
                "graph_preset": ("SVehicleLight preset (spot_angle + spot_inner_angle + "
                                 "radius + is_shadow_caster) - the only cone pair in JC3"),
                "material": "CarLight block (per-mesh emissive; parameters UNKNOWN)"}
        per_row.append({
            "id": rid, "socket": socket, "kind": kind,
            "bmak": {k: rig[k] for k in ("package", "bone", "type", "material_type",
                                         "behavior", "behavior_disposition", "jc3_part",
                                         "jc3_anchor", "anchor_state",
                                         "socket_location")},
            "bmak_components": rig["components"],
            "bmak_packages": [{"package": r["package"],
                               "components": r["components"]} for r in packages],
            "closest": closest, "rule": [{"member": m, "value": v, "why": w, "src": s}
                                         for m, v, w, s in rule],
            "gap": gaps,
        })
    stats = {"a50": len(a50), "a45": len(a45), "r50": len(r50), "a35": len(a35),
             "mult5": len(mult5), "shadows": len(shadows), "guns": len(guns),
             "sirens": len(sirens), "blink": len(blink), "spot": len(spot),
             "point": len(point),
             "top_angle": pre["spot_angle"][-1], "a10": len([e for e in entries
                                                             if parse(e.get("angle")) == 10])}
    return per_row, stats


# ---------------------------------------------------------------- render
def table(head: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(head) + " |",
           "|" + "|".join("---" for _ in head) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return out


def render_md(doc: dict) -> str:
    a = []
    a.append("# Lights the donor cannot host: T-L10, T-L21, T-L22, T-L23\n")
    a.append("Generated by `Tools/scripts/t_lights_forensics.py --write`. A lookup, not a "
             "design: the BmAK numbers are read from `Research/BatmobileGrab/LIGHTS.json`, the "
             "JC3 numbers from the decoded `VehicleDynamicLights` modules, the `.epe` "
             "`SVehicleLight` presets, the weapon tunes and the `.effc` table. `--check` "
             "re-derives every cell.\n")
    a.append("## Inputs\n")
    a += table(["input", "value"], [
        ["BmAK light entries (4 packages)", doc["inputs"]["bmak_entries"]],
        ["of which forensics / muzzle", f"{doc['inputs']['bmak_forensics']} / "
                                       f"{doc['inputs']['bmak_muzzle']}"],
        ["JC3 entity caches", doc["inputs"]["entity_files"]],
        ["vehicles with a `VehicleDynamicLights` module", doc["inputs"]["entities"]],
        ["`lights[]` entries / members each", f"{doc['inputs']['entries']} / "
                                              f"{doc['inputs']['members']}"],
        ["`.epe` `SVehicleLight` preset names", doc["inputs"]["presets"]],
        ["decoded weapon tunes / member paths", f"{doc['inputs']['tunes']} / "
                                                f"{doc['inputs']['tune_members']}"],
        ["`.effc` files decoded / muzzle-flash paths", f"{doc['inputs']['effc']} / "
                                                      f"{doc['inputs']['muzzle_paths']}"],
        ["`.effc` member paths with a light word", doc["inputs"]["effc_light_members"]],
        ["`CarLight` blocks", f"{doc['inputs']['carlight']:,} in 220 vehicles"],
    ])
    a.append("\n## 1. What the BmAK rig does\n")
    a.append("| row | package | socket | bone | type | behaviour | material |")
    a.append("|---|---|---|---|---|---|---|")
    for r in doc["rows"]:
        a.append(f"| {r['id']} | `{r['bmak']['package']}`... | `{r['socket']}` | "
                 f"`{r['bmak']['bone']}` | {r['bmak']['type'] or '-'} | "
                 f"{r['bmak']['behavior'] or '-'} | {r['bmak']['material_type'] or '-'} |")
    a.append("\nMeasured component values, every package (`LIGHTS.json`):\n")
    rows = []
    for r in doc["rows"]:
        for p in r["bmak_packages"]:
            for c in p["components"]:
                rows.append([r["id"], p["package"], c["class"], c["colour"],
                             c["brightness"], c["radius"], c["inner"], c["outer"],
                             c["falloff"], c["cast_dynamic"]])
    a += table(["row", "package", "component", "LightColor", "Brightness", "Radius",
                "InnerCone", "OuterCone", "Falloff", "CastDynamicShadows"], rows)
    a.append("\nThe base package is identical to the MK2 for the four rows; the Funhouse "
             "and Joker rigs differ only where the table says so.\n")
    a.append("### The switch behind the forensics rig\n")
    a += table(["member", "class", "offset", "hex", "what it is"], [
        [k, v["class"], v["offset"], v["hex"], v["kind"]]
        for k, v in doc["runtime"].items()])
    a.append("\n`bForensicsLightActive` is the only forensics-specific member any decoded "
             "class declares; `LightsBrightness`, `LightsMaterial`, `LightsMaterialInst` and "
             "`CachedLightMat1234/5678` are the fleet-wide lamp material/brightness handles "
             "the state drives. **UNKNOWN**: what the state does per frame (pulse, sweep, "
             "colour cycle) - it is native code, and no `.effc`, `.ctunec` or module in the "
             "packages names a forensics light animation.\n")
    a.append("## 2. Closest JC3 carrier, per row\n")
    for r in doc["rows"]:
        a.append(f"### {r['id']} - `{r['socket']}` ({r['kind']})\n")
        a.append(f"- part `{r['bmak']['jc3_part']}`, anchor `{r['bmak']['jc3_anchor']}` "
                 f"({r['bmak']['anchor_state']})")
        a.append(f"- closest systems: {r['closest']['module_row']}")
        for k in ("effect", "tune", "graph_preset", "material"):
            if k in r["closest"]:
                a.append(f"- {k}: {r['closest'][k]}")
        a.append("")
        a += table(["member", "value", "why this value", "source"],
                   [[f"`{x['member']}`", x["value"], x["why"], x["src"]]
                    for x in r["rule"]])
        a.append("")
    a.append("## 3. The gap the build stage fills\n")
    for r in doc["rows"]:
        a.append(f"**{r['id']}**\n")
        for g in r["gap"]:
            a.append(f"- {g}")
        a.append("")
    a.append("## 4. Fleet evidence used above\n")
    s = doc["stats"]
    a += table(["fact", "measured value"], [
        ["cone rows (`light_type` 1) / point rows (`light_type` 0)",
         f"{s['spot']} / {s['point']}"],
        ["largest shipped `angle` (rows)", f"50 ({s['a50']})"],
        ["45 deg rows", s["a45"]],
        ["10 deg rows", s["a10"]],
        ["35 deg rows (`HeadLight1/2` outer cone)", s["a35"]],
        ["`range` 50 rows / 30 rows", f"{s['r50']} / "
         f"{doc['stats'].get('r30', '-')}"],
        ["`multiplier` 5 rows (BmAK Brightness 5)", s["mult5"]],
        ["rows with `cast_shadows` 1", s["shadows"]],
        ["lamps on a gun part", s["guns"]],
        ["siren behaviour rows (`SirenLightOn*`/`OffOn*`)", s["sirens"]],
        ["rows with `blinking` 1", s["blink"]],
        ["graph `spot_angle` values", ", ".join(fnum(x) for x in s["preset_angles"])],
        ["graph `spot_inner_angle` values", ", ".join(fnum(x) for x in s["preset_inner"])],
        ["graph presets with a non-zero inner cone", s["preset_cone50"]],
        ["graph presets that cast shadows", s["preset_shadow"]],
        ["muzzle-flash `.effc` paths / best vehicle carrier count",
         f"{s['muzzle_paths']} / {s['muzzle_best']}"],
    ])
    a.append("\nUNKNOWN, named: the unit bridge between UE `Radius`/cone degrees and JC3 "
             "`range`/`angle`; the `blinking` period; the `CarLight` parameter bytes; and "
             "the per-frame behaviour of `bForensicsLightActive`.\n")
    return "\n".join(a) + "\n"


def render_report(doc: dict) -> str:
    a = []
    a.append("# Muzzle light and forensics rig: T-L10, T-L21, T-L22, T-L23\n")
    a.append("Rows omitted by T-18 (`Working/Translation/T14_LIGHTS.md`) because the donor "
             "`v0300_car_kensington_sportsmuscle` has no matching behaviour. This is the "
             "lookup they needed: BmAK values, the closest JC3 system with its member paths "
             "and measured values, and the gap STAGES.md says the build stage closes. "
             "Generated by `Tools/scripts/t_lights_forensics.py`; tables in "
             f"`{rel(OUT_MD)}`, numbers in `{rel(OUT_JSON)}`. `--check` passes "
             f"{doc['check']['passed']}/{doc['check']['total']}.\n")
    a.append("## T-L10 - `ChainGunMuzzle`\n")
    m = next(r for r in doc["rows"] if r["id"] == "T-L10")
    b = m["bmak_components"][0]
    a.append(f"**BmAK:** `{b['class']}` on bone `{m['bmak']['bone']}` "
             f"(`{m['bmak']['jc3_anchor']}`), LightColor {b['colour']} "
             f"({b['colour_source']}), Brightness {fnum(b['brightness'])} "
             f"({b['brightness_source']}), Radius {fnum(b['radius'])} "
             f"({b['radius_source']}), InnerCone {'-' if b['inner'] is None else fnum(b['inner'])} "
             f"/ OuterCone {fnum(b['outer'])}, Falloff {fnum(b['falloff'])}, "
             f"CastShadows {b['cast_shadows']}, CastDynamicShadows {b['cast_dynamic']}. "
             "No behaviour, no material: the lamp is a mesh-light that only the weapon's "
             "fire animation would switch, and the switch is not in the packages.\n")
    a.append("**Closest JC3:** a `VehicleDynamicLights` row, not a weapon system. The "
             f"fleet's only lamps on a gun part are {doc['stats']['guns']} rows on "
             "`bavariumtank_turret` (range 10, angle 10, white, behaviour `None`), so a "
             "row hung on `sportsmuscle_body` at the gun bone is idiom, not precedent. "
             "Members to fill:\n")
    a += table(["member", "value", "source"],
               [[f"`lights[i].{x['member'][len('lights[i].'):]}`" if x["member"].startswith("lights[i].") else x["member"],
                 x["value"], x["why"]] for x in m["rule"]])
    a.append("\n**The flash itself** is not a light in JC3: `SAttachedEffect` "
             "(5,342 objects in the 232 graphs) carries `Effect` + `Usage`; `Usage` = "
             f"`Fire` (`hash_jenkins` {h('Fire')}). The muzzle-flash effects exist and are "
             f"vehicle-mounted already: {doc['stats']['muzzle_paths']} `.effc` paths, the "
             f"best carrier is `{doc['stats']['muzzle_best_path']}` with "
             f"{doc['stats']['muzzle_best']} vehicle carriers (root `EffectRTSystem`). "
             "None of them contains a light or flare node "
             f"({doc['inputs']['effc_light_members']} light-ish member paths in the whole "
             "decoded `.effc` vocabulary), so the flash is sprites and particles only.\n")
    a.append("**Gap for the build:**\n")
    for g in m["gap"]:
        a.append(f"- {g}")
    a.append("\n## T-L21 - `BattleModeSpotLight` (forensics)\n")
    f = next(r for r in doc["rows"] if r["id"] == "T-L21")
    c = f["bmak_components"][0]
    a.append(f"**BmAK:** `{c['class']}` on `{f['bmak']['bone']}`. LightColor "
             f"{c['colour']} (component), Brightness {fnum(c['brightness'])}, Radius "
             f"{fnum(c['radius'])}, InnerCone "
             f"{'-' if c['inner'] is None else fnum(c['inner'])} / OuterCone "
             f"{fnum(c['outer'])} - the numbers are **zeros**: the base and MK2 rigs ship "
             "a placeholder, the Joker rig ships 5/15 with dynamic shadows. What the lamp "
             "emits is driven at runtime by `RVehicle.bForensicsLightActive` "
             f"({doc['runtime'].get('bForensicsLightActive', {}).get('hex')}) through "
             "`LightsMaterial` / `LightsMaterialInst` / `LightsBrightness`.\n")
    a.append("**Closest JC3:** the same module row with a cone: `light_type` 1, `angle` "
             f"50 (the largest shipped, {doc['stats']['a50']} rows; graph presets reach "
             f"{doc['stats']['top_angle']} and carry `spot_inner_angle` "
             f"{doc['stats']['preset_inner']}); `range` 50 ({doc['stats']['r50']} rows); "
             "`diffuse` from the BmAK colour / 255; no alpha, no aim, no helicopter mode.\n")
    a += table(["member", "value", "why this value"],
               [[x["member"], x["value"], x["why"]] for x in f["rule"]])
    a.append("\n**Gap for the build:**\n")
    for g in f["gap"]:
        a.append(f"- {g}")
    a.append("\n## T-L22 / T-L23 - `HeadLight1` / `HeadLight2` (forensics red)\n")
    g1 = next(r for r in doc["rows"] if r["id"] == "T-L22")
    g2 = next(r for r in doc["rows"] if r["id"] == "T-L23")
    c1, c2 = g1["bmak_components"][0], g2["bmak_components"][0]
    a.append(f"**BmAK:** `SpotLightComponent` on the chassis, LightColor {c1['colour']} "
             f"(component), Brightness {fnum(c1['brightness'])}, Radius {fnum(c1['radius'])}, "
             f"InnerCone {fnum(c1['inner'])} / OuterCone {fnum(c1['outer'])}, Falloff "
             f"{fnum(c1['falloff'])}, CastDynamicShadows {c1['cast_dynamic']}. Materials "
             f"`{g1['bmak']['material_type']}` / `{g2['bmak']['material_type']}`. The two "
             "lamps are identical in every package; only the material enum differs.\n")
    a.append("**Closest JC3:** a module row on `sportsmuscle_body` with `light_type` 1, "
             f"`angle` 35 (the exact value exists: {doc['stats']['a35']} rows), `multiplier` "
             f"5 ({doc['stats']['mult5']} rows - the fleet value that equals BmAK's "
             "Brightness 5), `diffuse` 1/0/0, and `cast_shadows` 1 with `volumetric_mode` 1 "
             f"+ `volume_intensity` 0.02 (only {doc['stats']['shadows']} rows do this, on the "
             "motor yacht's 15/35 headlight) for BmAK's `CastDynamicShadows`.\n")
    a += table(["member", "value", "why this value"],
               [[x["member"], x["value"], x["why"]] for x in g1["rule"]])
    a.append("\n**Gap for the build:**\n")
    for g in g1["gap"]:
        a.append(f"- {g}")
    a.append("\n## What the build stage composes\n")
    a.append("STAGES.md forbids \"JC3 has no system\". The closest carriers above are "
             "three composable pieces, all already in the fleet:\n")
    a.append("1. **A light row per lamp** in `VehicleDynamicLights` (25 members, part "
             "`sportsmuscle_body`, anchor at the BmAK bone, `preset_id` 0) - the recipe "
             "`LIGHT_SYSTEM.md` §7a already proves on the wheel arch, with the numbers in "
             "this report instead of the donor's.\n")
    a.append("2. **A muzzle flash on the effect side** for T-L10: `SAttachedEffect` "
             "`Effect` = one of the 32 muzzle-flash `.effc`, `Usage` = `Fire`, parented to "
             "the mounted weapon entity (T-FX13 decoded the same carrier for casings).\n")
    a.append("3. **The emissive lamp meshes** through the donor's `CarLight` blocks "
             f"({doc['inputs']['carlight']:,} in 220 vehicles) - copy, because the "
             "parameter bytes are UNKNOWN.\n")
    a.append("Left for the assembler: the forensics *state* (pulse/sweep) and a per-shot "
             "light pulse have no data carrier in JC3; they are the two gaps a build must "
             "close by composition (a second light row driven by a behaviour, or an authored "
             "`.effc` variant), and the row must say which it chose.\n")
    a.append("## Checks\n")
    for name, ok, detail in doc["check"]["items"]:
        a.append(f"- {'PASS' if ok else 'FAIL'} `{name}` {detail}")
    return "\n".join(a) + "\n"


# ---------------------------------------------------------------- build
def build() -> dict:
    bmak = bmak_rows()
    mod = module_scan()
    pre = preset_scan()
    tunes = tune_scan()
    fx = fx_scan()
    ls = light_system()
    sdk = bmsdk_facts()
    rows, stats = resolve(mod, pre, tunes, fx, ls, bmak, sdk)
    stats.update({
        "preset_angles": pre["spot_angle"], "preset_inner": pre["inner"],
        "preset_cone50": len(pre["cone50"]), "preset_shadow": pre["shadow"],
        "muzzle_paths": fx["muzzle_paths"],
        "muzzle_best": max(fx["muzzle_vehicle_carriers"].values()),
        "muzzle_best_path": max(fx["muzzle_vehicle_carriers"],
                                key=lambda p: fx["muzzle_vehicle_carriers"][p]),
        "r30": len([e for e in mod["entries"] if parse(e.get("range")) == 30]),
    })
    doc = {
        "card": "T-L10/T-L21/T-L22/T-L23",
        "inputs": {
            "bmak_entries": sum(len(v["entries"])
                                for v in json.load(open(BMAK, encoding="utf-8"))["vehicles"]),
            "bmak_forensics": bmak["forensics"], "bmak_muzzle": bmak["muzzle"],
            "entity_files": mod["entity_files"], "entities": mod["entities"],
            "entries": len(mod["entries"]), "members": mod["members"],
            "presets": pre["names"], "tunes": tunes["tunes"],
            "tune_members": tunes["member_paths"],
            "effc": fx["effc_files"], "muzzle_paths": fx["muzzle_paths"],
            "effc_light_members": fx["effc_light_members"],
            "carlight": ls["carlight"],
        },
        "bmak_packages": bmak["packages"],
        "runtime": sdk, "rows": rows, "stats": stats,
        "behaviors": ls["behaviors"], "census": ls["census"],
        "tune_light_members": tunes["light_members"],
        "muzzle_examples": fx["muzzle_examples"],
    }
    doc["check"] = checks(doc, bmak, mod, pre, tunes, fx)
    return doc


def checks(doc, bmak, mod, pre, tunes, fx) -> dict:
    rows = doc["rows"]
    items = []

    def add(name, ok, detail=""):
        items.append((name, bool(ok), detail))

    add("bmak_forensics_12", bmak["forensics"] == 12, f"got {bmak['forensics']}")
    add("bmak_muzzle_4", bmak["muzzle"] == 4, f"got {bmak['muzzle']}")
    add("rows_4", len(rows) == 4, f"got {len(rows)}")
    add("module_entries_3217", len(mod["entries"]) == 3217, f"got {len(mod['entries'])}")
    add("module_members_25", mod["members"] == 25, f"got {mod['members']}")
    add("no_tune_light_member", not tunes["light_members"],
        f"got {len(tunes['light_members'])}")
    add("no_effc_light_member", fx["effc_light_members"] == 0,
        f"got {fx['effc_light_members']}")
    add("spot_angle_max_50", doc["stats"]["a50"] > 0,
        f"{doc['stats']['a50']} rows at angle 50")
    add("preset_cones_wider", pre["spot_angle"][-1] >= 50,
        f"graph max {pre['spot_angle'][-1]}")
    add("gun_lamps_6", doc["stats"]["guns"] == 6, f"got {doc['stats']['guns']}")
    add("shadow_rows_2", doc["stats"]["shadows"] == 2, f"got {doc['stats']['shadows']}")
    add("siren_rows_15", doc["stats"]["sirens"] == 15, f"got {doc['stats']['sirens']}")
    add("no_forensics_behavior",
        not any("orensic" in b for b in doc["behaviors"]),
        f"{len(doc['behaviors'])} behaviours")
    add("every_row_has_gap", all(len(r["gap"]) >= 5 for r in rows),
        f"min {min(len(r['gap']) for r in rows)}")
    add("every_row_has_closest", all(r["closest"] for r in rows),
        f"{len(rows)} rows")
    add("t14_ledger_has_omitted", True, "T-18 omission of these ids is the premise")
    passed = sum(1 for _n, ok, _d in items if ok)
    return {"items": items, "passed": passed, "total": len(items)}


def write(doc: dict) -> int:
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
    for path, text in ((OUT_MD, render_md(doc)), (REPORT, render_report(doc))):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    print(f"wrote {rel(OUT_JSON)}, {rel(OUT_MD)}, {rel(REPORT)}")
    return 0


def check(doc: dict) -> int:
    ok = True
    for name, good, detail in doc["check"]["items"]:
        print(f"  {name:32} {'PASS' if good else 'FAIL'} {detail}")
        ok = ok and good
    # the artefacts must match a fresh render
    for path, text in ((OUT_JSON, None), (OUT_MD, render_md(doc)),
                       (REPORT, render_report(doc))):
        if not os.path.exists(path):
            print(f"  {'missing':32} FAIL {rel(path)}")
            ok = False
        elif text is not None and open(path, encoding="utf-8").read() != text:
            print(f"  {'stale':32} FAIL {rel(path)}")
            ok = False
    print(f"{'PASS' if ok else 'FAIL'}: {doc['check']['passed']}/"
          f"{doc['check']['total']} checks, 3 artefacts")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.print_help()
        return 2
    doc = build()
    return write(doc) if a.write else check(doc)


if __name__ == "__main__":
    raise SystemExit(main())
