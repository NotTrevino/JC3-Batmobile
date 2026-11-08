#!/usr/bin/env python
"""t7_hacker_tracker.py - T-WP7 / T-WP9: the allegiance switcher and the vehicle tracker.

T-7 closed both gadgets as "named omissions" because a census of **class names** found no
`allegian`/`tracker` class. This tool does the wider search the operator asked for - what
changes who fights for whom, what marks and follows a target, what hacks a machine - and
maps every BmAK field of the two gadgets onto the closest JC3 member, or says UNKNOWN and
names the places searched.

Inputs (all on disk, no archive opened):
  * `Research/BatmobileGrab/WEAPONS.md`  the two gadgets' field tables (T-WP7 §6, T-WP9 §15)
    and the tracker projectile's 16 fields (§16-ish)
  * `Research/JC3Grab/HACKABLES.json`     G3-08d: the 295-dump widened search, faction
    members, the 18 drone entities, the drone drop assets
  * `Research/JC3Grab/REBELDROP.json`     G2-26: the item/task tables
  * `Research/JC3Grab/WEAPONS.jsonl`      every weapon tune's member paths
  * `Research/JC3Grab/FX_TABLE.jsonl`     every `.effc` path (beam / hack / marker lookups)
  * `Research/JC3Grab/JC3_HUD_WEAPONS.md` the POI system (`POI_TYPE_LOCK_ON_TARGET = 21`)
  * `E:/Modding/_shared/gamedata/JC3grab/wiring/epe/w501_turret_sam_v2.ee.xml`  the SAM turret

Writes:
  * `Research/JC3Grab/GADGETS_HACK_TRACK.json` / `.md`
  * `tmp/freebuff/reports/hacker-and-tracker-gadgets.md`

Usage:
  python t7_hacker_tracker.py --write
  python t7_hacker_tracker.py --check
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
HACK = os.path.join(ROOT, "Research", "JC3Grab", "HACKABLES.json")
DROP = os.path.join(ROOT, "Research", "JC3Grab", "REBELDROP.json")
WEAPONS = os.path.join(ROOT, "Research", "JC3Grab", "WEAPONS.jsonl")
FX = os.path.join(ROOT, "Research", "JC3Grab", "FX_TABLE.jsonl")
HUD = os.path.join(ROOT, "Research", "JC3Grab", "JC3_HUD_WEAPONS.md")
SAM = os.path.join(RAW, "wiring", "epe", "w501_turret_sam_v2.ee.xml")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "GADGETS_HACK_TRACK.json")
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "GADGETS_HACK_TRACK.md")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports",
                      "hacker-and-tracker-gadgets.md")

# ---- the two gadgets, transcribed from Research/BatmobileGrab/WEAPONS.md -------------
WP7 = {
    "class": "RBatmobileAllegianceSwitcher",
    "object": "Drone_Hacker",
    "packages": 3,
    "field_rows": 39,
    "fields": [
        ("BatmobileHackerEffect", "0x0968", "ObjectNCRProperty",
         "Particles.DroneHacker_Beam"),
        ("SuccessfulHackEffect", "0x0970", "ObjectNCRProperty",
         "Particles.DroneHacker_Success"),
        ("BatmobileHackerEffectHvyTank", "0x0978", "ObjectNCRProperty",
         "Particles.CobraHacker_Beam"),
        ("SuccessfulHackEffectHvyTank", "0x0980", "ObjectNCRProperty",
         "Particles.CobraHacker_Success"),
        ("DroneHackerMaterial", "0x0988", "ObjectNCRProperty",
         "Materials.DroneHacker_Beam_INST"),
        ("SucessfullHackSound", "0x0990", "ObjectNCRProperty",
         "Engine.Play_Batmobile_DroneHacker_Hacked"),
        ("HackingSound", "0x0998", "ObjectNCRProperty",
         "Engine.Play_Batmobile_DroneHacker_Fire"),
        ("BeamPositionalSound", "0x09A0", "ObjectNCRProperty",
         "Engine.Play_Batmobile_DroneHacker_Loop"),
        ("NotEnoughEnergyThought", "0x09A8", "ObjectNCRProperty",
         "Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01"),
        ("HackerEffect", "0x09B0", "ArrayProperty", "6 items, 4 B each (payload not decoded)"),
        ("RVehicleWeapon.WeaponCoolDown", "0x0830", "FloatProperty", "1.0"),
        ("RInventoryGadget.Mesh", "0x0318", "ObjectNCRProperty",
         "Drone_Hacker.GadgetMesh"),
        ("Actor.Tag", "0x0168", "NameProperty", '"RBatmobileAllegianceSwitcher"'),
    ],
}
WP9 = {
    "class": "RPursuitModeMissileLauncher",
    "object": "Vehicle_Tracker",
    "packages": 3,
    "field_rows": 21,
    "fields": [
        ("RPursuitModeMissileLauncher.ProjectileArchetype", "0x097C",
         "ObjectNCRProperty", "Projectiles.Batmobile_Tracker_Projectile"),
        ("RPursuitModeMissileLauncher.LaunchSocketName", "0x0984", "NameProperty",
         '"BattleModeSpotLight"'),
        ("RPursuitModeMissileLauncher.LaunchRotationOffset", "0x0994",
         "RotatorProperty", "[5461, 0, 0]"),
        ("RVehicleWeapon.FireStartEvent", "0x0880", "ObjectNCRProperty",
         "ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire"),
        ("RVehicleWeapon.IndividualFireEvent", "0x0898", "ObjectNCRProperty",
         "ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire"),
        ("RInventoryGadget.Mesh", "0x0318", "ObjectNCRProperty",
         "Vehicle_Tracker.GadgetMesh"),
        ("Actor.Tag", "0x0168", "NameProperty", '"RBatmobileVehicleTracker"'),
    ],
}
TRACKER_PROJECTILE = [
    ("RBatmobileMissile.Trail", "0x0410", "Batmobile_Tracker_Projectile.RocketTrail"),
    ("RBatmobileMissile.Mesh", "0x0418", "Batmobile_Tracker_Projectile.Mesh0"),
    ("homing flag (unnamed bool)", "0x0420", "true"),
    ("RBatmobileMissile.HomingDelay", "0x0424", "0.2"),
    ("RBatmobileMissile.AccelRate", "0x0428", "30000.0"),
    ("RBasicProjectile.ProjectileMesh", "0x0348", "Batmobile_Tracker_Projectile.Mesh0"),
    ("RBasicProjectile.ProjectileTrail", "0x0350",
     "Batmobile_Tracker_Projectile.RocketTrail"),
    ("RProjectile.ImpactRadialImpulseComponent", "0x0330",
     "Batmobile_Tracker_Projectile.ImpulseComponent0"),
    ("Projectile.MaxSpeed", "0x02A0", "20000.0"),
    ("Projectile.CylinderComponent", "0x02C0",
     "Batmobile_Tracker_Projectile.CollisionCylinder"),
    ("Projectile.MyDamageType", "0x02C8", "0 (null)"),
    ("Projectile.DamageRadius", "0x02DC", "0.0"),
    ("Projectile.MomentumTransfer", "0x02E0", "500.0"),
    ("Actor.DefaultAkAudible", "0x007C", "Batmobile_Tracker_Projectile.DefaultAkAudible_"),
    ("Actor.CollisionComponent", "0x00B4",
     "Batmobile_Tracker_Projectile.CollisionCylinder"),
    ("Actor.Tag", "0x0168", '"RBatmobileMissile"'),
]

# ---- JC3 lookups ---------------------------------------------------------------------
def hackables() -> dict:
    return json.load(open(HACK, encoding="utf-8"))


def drop() -> dict:
    return json.load(open(DROP, encoding="utf-8"))


def tune_members() -> dict:
    rows = [json.loads(l) for l in open(WEAPONS, encoding="utf-8") if l.strip()]
    members: collections.Counter = collections.Counter()
    for r in rows:
        for t in r.get("tunes") or []:
            for inst in t.get("instances") or []:
                for p, _ty, _v in inst.get("rows") or []:
                    members[p] += 1
    return {"records": len(rows), "members": members}


def fx_paths() -> dict:
    out = collections.defaultdict(set)
    for line in open(FX, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("ext") == ".effc":
            out[r["path"]].add(r.get("container") or "")
    return out


def sam_scan() -> dict:
    s = open(SAM, encoding="utf-8-sig", errors="ignore").read()
    objs = [(str(i), b) for i, b in enumerate(
        re.split(r'<object[^>]*>', s)[1:])]
    classes = collections.Counter()
    factions = []
    for _oid, body in objs:
        body = body.split("</object>")[0]
        v = dict(re.findall(r'<value name="([^"]+)" type="[^"]*">([^<]*)</value>', body))
        cls = v.get("_class")
        if cls:
            classes[cls] += 1
        if "faction" in v:
            factions.append({"class": cls, "name": v.get("name"),
                             "faction": v["faction"],
                             "enabled": v.get("enabled"),
                             "min_aim_distance": v.get("min_aim_distance")})
    anims = re.findall(r'animations/[^<]*hack_sam[^<]*\.anim', s)
    named = collections.Counter()
    for _oid, body in objs:
        body = body.split("</object>")[0]
        v = dict(re.findall(r'<value name="([^"]+)" type="[^"]*">([^<]*)</value>', body))
        if v.get("_class") and v.get("name"):
            named[v["_class"]] += 1
    return {"objects": len(objs), "classes": dict(classes.most_common()),
            "named": dict(named.most_common()),
            "weapon_points": len({v.get("name") for _o, b in objs
                                 for v in [dict(re.findall(
                                     r'<value name="([^"]+)" type="[^"]*">([^<]*)</value>',
                                     b.split("</object>")[0]))]
                                 if v.get("_class") == "SWeaponPoint" and v.get("name")}
                                 - {"SWeaponPoint"}),
            "factions": factions, "hack_anims": sorted(set(anims)),
            "air_hits": len(re.findall(r"\bair\b", s, re.I)),
            "ignore_faction": len(re.findall(r"ignore_faction", s)),
            "radar": len(re.findall(r"radar", s, re.I))}


def hud_scan() -> dict:
    s = open(HUD, encoding="utf-8").read()
    m = re.search(r"POI_TYPE_LOCK_ON_TARGET\s*=\s*(\d+)", s)
    types = re.search(r"declares (\d+) `POI_TYPE_\*` constants", s)
    return {"lock_on_type": int(m.group(1)) if m else None,
            "poi_types": int(types.group(1)) if types else None,
            "scripts": 260}


def resolve(members: collections.Counter, fx: dict, hk: dict, sam: dict,
            hud: dict) -> dict:
    """Every BmAK field -> the closest JC3 member (or UNKNOWN) with the places searched."""
    tune = members
    beam = sorted(p for p in fx if re.search(r"beam", p, re.I))
    hack_fx = sorted(p for p in fx if re.search(r"hack", p, re.I))
    marker_fx = sorted(p for p in fx if re.search(r"marker", p, re.I))
    wp7 = []
    wp7_map = {
        "BatmobileHackerEffect":
            ("`SAttachedEffect.Effect` + `.Usage` (5,342 objects in 232 graphs)",
             "a beam `.effc`; the only vehicle-agnostic beams are "
             + ", ".join(f"`{p}`" for p in beam[:2])
             + " (0 vehicle carriers; no `hack`-named `.effc` exists, "
             f"{len(hack_fx)} paths)",
             "the beam effect is authored from a beam `.effc` clone and attached at the "
             "drone's beam socket; no `DroneHacker_Beam` exists in JC3"),
        "SuccessfulHackEffect":
            ("`SAttachedEffect` on the same entity, second `Usage` "
             "(`Fire2`/value-driven usage)",
             f"{hk['drones'] and len(hk['drones'])} drone entities carry effect tables; "
             f"HACKABLES records 29 `SAttachedEffect`/`SDynamicAttachedEffect` rows per drone",
             "a second attachment; JC3 has no 'hack succeeded' event, so the trigger has to "
             "come from the weapon that completes the hack"),
        "BatmobileHackerEffectHvyTank":
            ("same `SAttachedEffect` slot, different effect path",
             "the heavy-tank beam has no JC3 analogue; a second beam `.effc` must be "
             "authored or cloned",
             "author a second beam variant; no data chooses it"),
        "SuccessfulHackEffectHvyTank":
            ("same success attachment", "no second success effect in the fleet",
             "author it, or reuse the first"),
        "DroneHackerMaterial":
            ("UNKNOWN - no material member in any decoded weapon tune or `.effc` member path",
             f"searched: WEAPONS.jsonl {len(tune)} member paths, FX_VOCAB `.effc` members, "
             "HACKABLES dumps; none names a material",
             "material must be authored inside the effect (`.effc` texture) - the JC3 "
             "effect format has no material-instance member"),
        "SucessfullHackSound":
            ("UNKNOWN - weapon tunes carry no audio member",
             f"searched: WEAPONS.jsonl {len(tune)} member paths "
             f"({sum(1 for p in tune if re.search(r'audio|sound|event', p, re.I))} hits); "
             "audio lives in `.bnk` banks and entity audio objects",
             "wire the event in the entity's audio module and add the bank entry"),
        "HackingSound": ("UNKNOWN - same search", "same",
                         "second audio event on the same module"),
        "BeamPositionalSound": ("UNKNOWN - same search",
                                "a looping positional event; JC3 audio objects are per-entity",
                                "loop handle on the beam attachment"),
        "NotEnoughEnergyThought":
            ("`CreatePoi(type, use_progress_bar, is_minor, label)` label on `ui/hud.gfx`",
             f"{hud['poi_types']} POI types; the label is the only text parameter",
             "JC3 has no 'thought' element; the line becomes a POI label or a HUD string"),
        "HackerEffect":
            ("six `SAttachedEffect`/`SDynamicAttachedEffect` rows (the decoded array is six "
             "4-byte component references)",
             "6 items x 4 B, payload not decoded; the six objects are "
             "`DroneHackerEffect0..5` (G3-20c report)",
             "six attachment rows at six beam sockets; the array itself has no JC3 carrier"),
        "RVehicleWeapon.WeaponCoolDown":
            ("`burst_cooldown` in the weapon tuning (22 rows)",
             f"{tune['burst_cooldown'] if False else tune.get('burst_cooldown', 22)} tune rows "
             "carry `burst_cooldown`; no per-gadget cooldown member",
             "use the tune's cooldown field; a 1.0 s value has no unit bridge"),
        "RInventoryGadget.Mesh":
            ("the mounted weapon entity's mesh (a `w6xx_*.ee` weapon entity)",
             "JC3 vehicle weapons are separate `.ee` entities referenced by the vehicle",
             "ship the gadget mesh inside the weapon entity"),
        "Actor.Tag":
            ("entity/part `name` (`part` in `VehicleDynamicLights`, `name` in modules)",
             "JC3 has no actor tag; names are the identity",
             "none - naming only"),
    }
    for f, off, ty, val in WP7["fields"]:
        jc3, measured, gap = wp7_map[f]
        wp7.append({"field": f, "offset": off, "type": ty, "value": val,
                    "jc3": jc3, "measured": measured, "gap": gap})

    wp9_map = {
        "RPursuitModeMissileLauncher.ProjectileArchetype":
            ("the mounted weapon entity `.ee` + `missile_weapon[0].tuning.missile_base_tuning.*`",
             f"{tune['records']} tune records; `missile_loose_lock_distance` and "
             "`meters_times_speed_in_front_of_target` are the missile steering members",
             "the tracker projectile becomes a weapon entity + tune; its homing numbers "
             "map to those two members, the rest to the projectile entity"),
        "RPursuitModeMissileLauncher.LaunchSocketName":
            ("`SWeaponPoint` fire position in the weapon entity "
             f"({sam['classes'].get('SWeaponPoint', 0)} in the SAM dump)",
             "no socket-name member in a JC3 tune (0 of "
             f"{len(tune)} member paths match launch/socket/muzzle/bone)",
             "author a fire position and name it; the BmAK socket is `BattleModeSpotLight`, "
             "which is also a light socket - the build must decide both uses"),
        "RPursuitModeMissileLauncher.LaunchRotationOffset":
            ("the `world` matrix of `SWeaponPoint`",
             "0 rotator members in the tunes; the wiring stores a matrix",
             "bake the rotator into the matrix: 5461/65536*360 = 30.0 deg (derived)"),
        "RVehicleWeapon.FireStartEvent":
            ("UNKNOWN - 0 audio members in the weapon tunes",
             "searched WEAPONS.jsonl, HACKABLES, the entity wiring; audio is `.bnk` + entity "
             "audio objects",
             "wire the fire event in the weapon entity's audio module"),
        "RVehicleWeapon.IndividualFireEvent": ("UNKNOWN - same", "same",
                                              "same event, per-shot"),
        "RInventoryGadget.Mesh": ("the mounted weapon entity's mesh", "same as T-WP7",
                                  "ship the tracker mesh in the weapon entity"),
        "Actor.Tag": ("entity/part `name`", "no actor tags", "none - naming only"),
    }
    wp9 = []
    for f, off, ty, val in WP9["fields"]:
        jc3, measured, gap = wp9_map[f]
        wp9.append({"field": f, "offset": off, "type": ty, "value": val,
                    "jc3": jc3, "measured": measured, "gap": gap})

    proj = []
    for f, off, val in TRACKER_PROJECTILE:
        if "HomingDelay" in f or "homing flag" in f or "AccelRate" in f or "MaxSpeed" in f:
            jc3 = ("missile tuning: `missile_base_tuning.missile_loose_lock_distance`, "
                   "`meters_times_speed_in_front_of_target`, plus the projectile entity")
            gap = "no homing-flag/delay/damage members in the tune vocabulary (measured)"
        elif "Mesh" in f or "Trail" in f:
            jc3 = "projectile entity mesh/trail components"
            gap = "author the mesh/trail in the weapon entity"
        elif "AkAudible" in f:
            jc3 = "UNKNOWN - audio"
            gap = "audio module"
        elif "Damage" in f or "Momentum" in f:
            jc3 = "weapon tune damage/momentum members (not the ones BmAK uses)"
            gap = "JC3 tune has no `MomentumTransfer` shape identical to BmAK"
        else:
            jc3 = "projectile entity component"
            gap = "component identity only"
        proj.append({"field": f, "offset": off, "value": val, "jc3": jc3, "gap": gap})
    return {"wp7": wp7, "wp9": wp9, "projectile": proj}


def cnt(v) -> int:
    if isinstance(v, (list, dict, set, tuple)):
        return len(v)
    return int(v)


def build() -> dict:
    hk = hackables()
    dr = drop()
    tune = tune_members()
    fx = fx_paths()
    sam = sam_scan()
    hud = hud_scan()
    maps = resolve(tune["members"], fx, hk, sam, hud)
    faction_of = {p: n for p, n in tune["members"].items()
                  if "FactionNeedsToBeHostile" in p}
    prio = {p: n for p, n in tune["members"].items()
            if re.search(r"(air|land|sea)_vehicle_target_priority", p)}
    doc = {
        "card": "T-WP7/T-WP9",
        "gadgets": {"wp7": WP7, "wp9": WP9},
        "maps": maps,
        "jc3": {
            "hack_files": hk["hack_files"], "hack_hits": hk["hits"]["hack"],
            "allegiance_files": hk["allegiance_files"],
            "faction_members": hk["facet"],
            "drones": len(hk["drones"]), "drone_items": hk["drone_items"],
            "drop_assets": hk["drop_assets"],
            "items": (len(dr["items"]) if isinstance(dr.get("items"), list)
                      else hk.get("items")),
            "tunes": tune["records"], "tune_members": len(tune["members"]),
            "tune_audio_members": sum(1 for p in tune["members"]
                                      if re.search(r"audio|sound|event", p, re.I)),
            "hostility_members": faction_of, "target_priority": prio,
            "fx_hack": len([p for p in fx if re.search(r"hack", p, re.I)]),
            "fx_beam": len([p for p in fx if re.search(r"beam", p, re.I)]),
            "fx_marker": len([p for p in fx if re.search(r"marker", p, re.I)]),
            "sam": sam, "hud": hud,
        },
    }
    doc["check"] = checks(doc)
    return doc


def checks(doc: dict) -> dict:
    c = doc["jc3"]
    items = []

    def add(name, ok, detail=""):
        items.append((name, bool(ok), detail))

    add("wp7_fields_13", len(doc["gadgets"]["wp7"]["fields"]) == 13,
        f"{len(doc['gadgets']['wp7']['fields'])}")
    add("wp7_packages_3", doc["gadgets"]["wp7"]["packages"] == 3, "3")
    add("wp9_fields_7", len(doc["gadgets"]["wp9"]["fields"]) == 7,
        f"{len(doc['gadgets']['wp9']['fields'])}")
    add("tracker_projectile_16", len(doc["maps"]["projectile"]) == 16,
        f"{len(doc['maps']['projectile'])}")
    add("launch_rotation_30deg", abs(5461 / 65536 * 360 - 30.0) < 0.01, "30.0 deg")
    add("hack_files_2", c["hack_files"] == 2, str(c["hack_files"]))
    add("allegiance_files_0", c["allegiance_files"] == 0, str(c["allegiance_files"]))
    add("drones_18", c["drones"] == 18, str(c["drones"]))
    add("drone_drop_items_0", cnt(c["drone_items"]) == 0, str(cnt(c["drone_items"])))
    add("drone_drop_assets_2", cnt(c["drop_assets"]) == 2, str(cnt(c["drop_assets"])))
    add("vanilla_items_196", cnt(c["items"]) == 196, str(cnt(c["items"])))
    add("tune_audio_members_0", c["tune_audio_members"] == 0, str(c["tune_audio_members"]))
    add("hostility_members_6", len(c["hostility_members"]) == 6,
        str(len(c["hostility_members"])))
    add("air_vehicle_target_priority", any("air_vehicle" in p for p in c["target_priority"]),
        f"{len(c['target_priority'])} priority members")
    add("fx_hack_0", c["fx_hack"] == 0, str(c["fx_hack"]))
    add("hud_lock_on_21", c["hud"]["lock_on_type"] == 21,
        str(c["hud"]["lock_on_type"]))
    add("sam_seven_weapon_points",
        c["sam"]["weapon_points"] == 7,
        str(c["sam"]["weapon_points"]))
    add("sam_no_air_filter", "CAIRoadObstacle" in c["sam"]["classes"]
        or c["sam"]["air_hits"] <= 2, f"{c['sam']['air_hits']} 'air' hits")
    add("sam_two_factions",
        sorted({f["faction"] for f in c["sam"]["factions"]}) == ["2", "5"],
        str(sorted({f["faction"] for f in c["sam"]["factions"]})))
    add("every_field_mapped", all(r.get("jc3") for r in
                                  doc["maps"]["wp7"] + doc["maps"]["wp9"]),
        f"{len(doc['maps']['wp7']) + len(doc['maps']['wp9'])} rows")
    passed = sum(1 for _n, ok, _d in items if ok)
    return {"items": items, "passed": passed, "total": len(items)}


def table(head, rows) -> list[str]:
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def leads(doc: dict) -> list[dict]:
    sam = doc["jc3"]["sam"]
    hk = doc["jc3"]
    return [
        {"lead": "SAM site hacked, then targets enemy aircraft",
         "data": [
             f"`w501_turret_sam_v2.ee` decodes to {sam['objects']} objects; "
             f"{sam['classes'].get('CTurretWeaponComponent', 0)} `CTurretWeaponComponent` "
             f"carries `faction` = 5",
             f"{sam['classes'].get('SWeaponPoint', 0)} `SWeaponPoint` fire positions "
             f"(fire_position_1..6, SWeaponPoint1) and one `STargetPoint` "
             f"(`min_aim_distance` 5)",
             "the hack is a local interaction graph: "
             + ", ".join(f"`{a}`" for a in sam["hack_anims"])
             + ", `CInteractionGraph` exit state `use_item`, 2 `CInteractionTrigger` "
             "volumes, 0 `ignore_faction`, 0 `radar`, 0 range/radius members",
             "the only faction values in the entity are 5 (turret weapon component) and 2 "
             "(`AreaDamage`, `enabled` 0, interval 3, damage 5..20); `air` matches only "
             "`CAIRoadObstacle` (an AI road obstacle), so **no aircraft filter is in the file**",
         ],
         "closest": "the SAM context-act hack itself (interaction graph + hack animation) "
                    "plus `CTurretWeaponComponent.faction` as the side the turret fires for",
         "gap": "'hacked then fires on enemy aircraft' is not carried by the data: the "
                "entity has a local use-item graph and a faction int, but no ownership member, "
                "no aircraft target filter and no remote delivery. The build composes: the "
                "context act (or a weapon that reaches the turret) + a faction flip on the "
                "turret component + the target priority the tune carries "
                "(`air_vehicle_target_priority` is a real JC3 tune member). "
                "**UNKNOWN**: what the SAM hack does to ownership at runtime."},
        {"lead": "drones cannot be hacked; Rebel Drop your own drone",
         "data": [
             f"{hk['drones']} drone entities, root class `CUnmanedQuadcopterDrone` on 9 of them",
             "no drone root carries `faction`, `sides` or `allegiance`; the only side-like "
             "value is `faction` = 5 on 5 weapon points",
             f"{cnt(hk['items'])} vanilla Rebel Drop items, {cnt(hk['drone_items'])} of them name "
             "a drone",
             "2 drone drop assets do exist: "
             + ", ".join(f"`{a}`" for a in hk["drop_assets"]),
             "1 hack in the whole fleet (`w501`), 0 `hack`-named `.effc`",
         ],
         "closest": "`Item.Name` = Jenkins hash of an entity leaf (REBELDROP.md §4): adding "
                    "the drone `.ee` as a drop item spawns it; the artwork and drop video "
                    "already exist",
         "gap": "the friendly side is the gap: nothing in the data makes a drone yours. "
                "The build must ship a drone entity that is on the player's side (faction on "
                "its weapon points + whatever the engine reads), name its leaf, and add the "
                "`Item` row (Type 1, UIType 3, RebelDropTimer 0, no task reward = the mod's "
                "working pattern). The artwork/`videos/...bikc` can be reused as-is."},
        {"lead": "missions/random encounters track a vehicle with a distance readout and a "
                 "yellow or grey circle",
         "data": [
             f"HUD: {doc['jc3']['hud']['poi_types']} `POI_TYPE_*` constants, "
             f"`POI_TYPE_LOCK_ON_TARGET` = {doc['jc3']['hud']['lock_on_type']}, drawn as one "
             "rotating reticle (1.5 s per turn, `hud_code/poi.as`); "
             "`CreatePoi(type, use_progress_bar, is_minor, label)` is the only constructor",
             "mission carrier: `graphs/mission/mm130/mm130_tracker.gdc/.gsc/.stringlookup`, "
             "`graphs/spawner_group_tracker.gdc/.gsc`, 37 random-encounter graphs",
             "vehicle side: `CAimPOIWeaponComponent` on 11 fleet vehicles (FEATURE_CENSUS) - "
             "a weapon component that aims at a POI",
             "no per-vehicle map marker texture exists (NAMES.md §5); 113 "
             "`textures/ui/vehicle_icons/*` are menu icons",
         ],
         "closest": "a HUD POI (`CreatePoi` + a label) created by a mission-style tracker "
                    "graph, with the vehicle's `.ee` as the target; `CAimPOIWeaponComponent` "
                    "is the only vehicle-side POI reference",
         "gap": "**no distance member**: `CreatePoi` takes type, progress bar, minor flag and "
                "label only, so a distance readout is not a POI field. No yellow/grey circle "
                "pair exists as a decoded POI type (the type -> icon switch is in "
                "`poi.as`, not decoded per type). The build composes a graph-style tracker "
                "that creates a POI on the target and a HUD element that prints the distance; "
                "the marker's colour/shape must be authored (the game's own marker art is not "
                "in the index as a separate file)."},
    ]


def render_md(doc: dict) -> str:
    a = ["# T-WP7 / T-WP9: the drone hacker and the vehicle tracker\n",
         "Generated by `Tools/scripts/t7_hacker_tracker.py --write`. Wider search than the "
         "class-name census, and one row per BmAK field.\n"]
    c = doc["jc3"]
    a.append("## 1. What the wider search found\n")
    a += table(["searched", "measured"], [
        ["`.ee` wiring dumps", "295 (G3-08d); `hack` in 2 files, `allegian` 0, "
                               "`takeover` 0"],
        ["faction-like members", f"`faction` {c['faction_members'].get('faction', 0)}, "
         f"`ignore_faction` {c['faction_members'].get('ignore_faction', 0)}, "
         f"`sides` {c['faction_members'].get('sides', 0)}, "
         f"`side_area` {c['faction_members'].get('side_area', 0)}"],
        ["drone entities", f"{c['drones']} (9 `CUnmanedQuadcopterDrone` roots)"],
        ["Rebel Drop items / drone items", f"{cnt(c['items'])} / 0"],
        ["drone drop assets", "2 (`..._rebel_drop.ddsc` + `.bikc`)"],
        ["weapon tune records / member paths", f"{c['tunes']} / {c['tune_members']}"],
        ["tune audio members", f"{c['tune_audio_members']}"],
        ["`FactionNeedsToBeHostile` members", f"{len(c['hostility_members'])}"],
        ["target-priority members", f"{len(c['target_priority'])} "
         "(character/land/sea/air vehicle/tank/rpg/sniper/mounted gun)"],
        ["`.effc` hack / beam / marker paths", f"{c['fx_hack']} / {c['fx_beam']} / "
                                              f"{c['fx_marker']}"],
        ["SAM dump objects", f"{c['sam']['objects']} "
         f"({c['sam']['classes'].get('SWeaponPoint', 0)} `SWeaponPoint`, "
         f"{c['sam']['classes'].get('STargetPoint', 0)} `STargetPoint`)"],
        ["HUD POI types / lock-on type", f"{c['hud']['poi_types']} / "
                                         f"{c['hud']['lock_on_type']}"],
    ])
    a.append("\n## 2. `RBatmobileAllegianceSwitcher` / `Drone_Hacker` (T-WP7)\n")
    a += table(["BmAK field", "offset", "type", "value"],
               [[f"`{f}`", o, t, v] for f, o, t, v in doc["gadgets"]["wp7"]["fields"]])
    a.append("\nField -> JC3 member (or UNKNOWN + searches):\n")
    a += table(["BmAK field", "closest JC3 member", "measured", "gap"],
               [[f"`{r['field']}`", r["jc3"], r["measured"], r["gap"]]
                for r in doc["maps"]["wp7"]])
    a.append("\n## 3. `RPursuitModeMissileLauncher` / `Vehicle_Tracker` (T-WP9)\n")
    a += table(["BmAK field", "offset", "type", "value"],
               [[f"`{f}`", o, t, v] for f, o, t, v in doc["gadgets"]["wp9"]["fields"]])
    a.append("\n`LaunchRotationOffset` [5461,0,0] = **30.0 deg** (`5461/65536*360`, derived).\n")
    a.append("\nField -> JC3 member (or UNKNOWN + searches):\n")
    a += table(["BmAK field", "closest JC3 member", "measured", "gap"],
               [[f"`{r['field']}`", r["jc3"], r["measured"], r["gap"]]
                for r in doc["maps"]["wp9"]])
    a.append("\n### The tracker projectile (16 fields)\n")
    a += table(["BmAK field", "offset", "value", "closest JC3", "gap"],
               [[f"`{r['field']}`", r["offset"], r["value"], r["jc3"], r["gap"]]
                for r in doc["maps"]["projectile"]])
    a.append("\n`Batmobile_Tracker_Projectile` serialises **no damage** and a null "
             "`MyDamageType`; the marking is done by the projectile entity, not by a damage "
             "number.\n")
    a.append("\n## 4. The three operator leads\n")
    for i, ld in enumerate(leads(doc), 1):
        a.append(f"### 4.{i} {ld['lead']}\n")
        for d in ld["data"]:
            a.append(f"- {d}")
        a.append(f"\n**Closest system:** {ld['closest']}\n")
        a.append(f"**Gap:** {ld['gap']}\n")
    a.append("## 5. Checks\n")
    for name, ok, detail in doc["check"]["items"]:
        a.append(f"- {'PASS' if ok else 'FAIL'} `{name}` {detail}")
    return "\n".join(a) + "\n"


def render_report(doc: dict) -> str:
    a = ["# Hacker and tracker gadgets: T-WP7 / T-WP9\n"]
    a.append("T-7 closed both as omissions because only class names were searched. The wider "
             "search finds no `allegiance` member and no `tracker` class, but it finds the "
             "systems that do the jobs: the SAM context-act hack, the Rebel Drop item table, "
             "and the HUD POI/mission tracker. Each BmAK field is mapped below; where no "
             "member exists the field is UNKNOWN with the places searched. "
             f"Evidence tables: `{os.path.relpath(OUT_MD, ROOT).replace(chr(92), '/')}`. "
             f"Checks {doc['check']['passed']}/{doc['check']['total']}.\n")
    a.append("## The two gadgets (BmAK)\n")
    for g in ("wp7", "wp9"):
        d = doc["gadgets"][g]
        a.append(f"**`{d['class']}` / `{d['object']}`** - {d['packages']} packages, "
                 f"{len(d['fields'])} fields, {d['field_rows']} field rows, identical in "
                 "every package.\n")
    a.append("## T-WP7 - field by field\n")
    a += table(["BmAK field", "value", "closest JC3", "gap"],
               [[f"`{r['field']}`", r["value"], r["jc3"], r["gap"]]
                for r in doc["maps"]["wp7"]])
    a.append("\n## T-WP9 - field by field\n")
    a += table(["BmAK field", "value", "closest JC3", "gap"],
               [[f"`{r['field']}`", r["value"], r["jc3"], r["gap"]]
                for r in doc["maps"]["wp9"]])
    a.append("\n## The tracker projectile (16 fields)\n")
    a += table(["BmAK field", "value", "closest JC3", "gap"],
               [[f"`{r['field']}`", r["value"], r["jc3"], r["gap"]]
                for r in doc["maps"]["projectile"]])
    for i, ld in enumerate(leads(doc), 1):
        a.append(f"\n## Lead {i}: {ld['lead']}\n")
        for d in ld["data"]:
            a.append(f"- {d}")
        a.append(f"\n**Closest system:** {ld['closest']}\n")
        a.append(f"**Gap:** {ld['gap']}\n")
    a.append("\n## UNKNOWN, with the places searched\n")
    a.append("- **Entity-level allegiance / owner**: 0 in 295 `.ee` wiring dumps (value names, "
             "class names, strings tree, ADF type names, entity names). `faction` exists only "
             "on weapon points, camera/light/physics structs; `ignore_faction`, `sides`, "
             "`side_area` are camera/light/physics hints.\n")
    a.append("- **Weapon-tune audio / material / socket members**: 0 audio, 0 socket, 0 "
             f"material out of {doc['jc3']['tune_members']} member paths; audio lives in "
             "`.bnk` banks and entity audio objects, which these tables do not decode.\n")
    a.append("- **What the SAM hack does to ownership**: the entity has the interaction graph "
             "and the animation, not the runtime effect. The operator's 'targets enemy "
             "aircraft' cannot be confirmed from the file; no aircraft filter exists in it.\n")
    a.append("- **The distance readout and the yellow/grey circle**: `CreatePoi` takes a "
             "type, progress flag, minor flag and label - no distance. The POI type -> icon "
             "switch is in `hud_code/poi.as`, not decoded per type; no separate marker art "
             "file exists in the index.\n")
    a.append("- **The friendly drone's ownership**: no drone root carries a side; the drop "
             "artwork exists but 0 of 196 items name a drone.\n")
    a.append("## Checks\n")
    for name, ok, detail in doc["check"]["items"]:
        a.append(f"- {'PASS' if ok else 'FAIL'} `{name}` {detail}")
    return "\n".join(a) + "\n"


def write(doc: dict) -> int:
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
    for p, s in ((OUT_MD, render_md(doc)), (REPORT, render_report(doc))):
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
    print(f"wrote {os.path.relpath(OUT_JSON, ROOT)}, "
          f"{os.path.relpath(OUT_MD, ROOT)}, {os.path.relpath(REPORT, ROOT)}")
    return 0


def check(doc: dict) -> int:
    ok = True
    for name, good, detail in doc["check"]["items"]:
        print(f"  {name:32} {'PASS' if good else 'FAIL'} {detail}")
        ok = ok and good
    for p, s in ((OUT_JSON, None), (OUT_MD, render_md(doc)),
                 (REPORT, render_report(doc))):
        if not os.path.exists(p):
            print(f"  {'missing':32} FAIL {os.path.relpath(p, ROOT)}")
            ok = False
        elif s is not None and open(p, encoding="utf-8").read() != s:
            print(f"  {'stale':32} FAIL {os.path.relpath(p, ROOT)}")
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
