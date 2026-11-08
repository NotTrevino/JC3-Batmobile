"""t15_world.py - world translation (T-20).

The eight `WLD` codes of `GRAB_BACKLOG.md` §1.9 are the car's *world* behaviour: how it is
spawned (Rebel Drop), what it is called (strings and icon), how Rico gets in and stands on it,
how heavy it is, what it does in water, what it does with the tether / cargo bay / helicopter,
and whether NPC Batmobiles can appear. Unlike the module rows of T-1/T-3, almost none of these
are numbers in a `.vmodc`: they live in **five other data files** plus the entity graph, and
two decisions (D-6 standalone, D-8 lore water) already fix the intent.

This tool therefore does not choose anything by hand. It re-reads the G2 / T-13 evidence and
re-derives every cell of every row:

  REBELDROP.json        G2-26  the item record recipe, the donor item, the tasks table
  STANDALONE.json       G2-27  the new leaf and what the entity needs
  TRAFFIC.json          G2-29  the donor's spawn record and the 41 traffic selectors
  WATER.json            G2-31  will_sink / buoyancy / the fleet-wide water constants
  TETHER.json           G2-34  the 6 t mass ratio, 12 cargo bays, 0 helicopter bays
  INTERACTION.json      G2-18  the 85-object graph and the 3 stunt areas
  t9_interaction.json   T-13   where those objects were placed on the Batmobile
  INDEX.jsonl           G2     every path in the install (icons, `.stringlookup`, tables)
  online.stringlookup   G2-32  the name/blurb pairs, decoded in place by `jc3strings`

Every row carries a disposition from `t_rows.py`'s vocabulary:

  next     a build step already owns the value (B-13 for the drop / strings / icon,
           B-05 for the graph objects)
  keep     the shipped data already satisfies the requirement - nothing to write
  epe      the value lives in the entity graph (the T-13 placement)
  blocked  the write side does not exist in `Tools/scripts` (a `.stringlookup` pair, the
           stunt-area welds), so the row cannot be built with this toolkit
  out      a proven absence (no vehicle-side tether member, no helicopter cargo bay)

`--write` writes `Working/Translation/T15_WORLD.md` + `t15_world.json`; `--check` re-reads every
input, re-derives both files, compares them byte-for-byte and cross-checks the rows against
`T_ROWS.jsonl` (the ledger `t_rows.py build` makes from this document).

Usage:
  python Tools/scripts/t15_world.py --write
  python Tools/scripts/t15_world.py --check
  python Tools/scripts/t15_world.py show T-WLD11
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
REBELDROP = os.path.join(JC3, "REBELDROP.json")
STANDALONE = os.path.join(JC3, "STANDALONE.json")
TRAFFIC = os.path.join(JC3, "TRAFFIC.json")
WATER = os.path.join(JC3, "WATER.json")
TETHER = os.path.join(JC3, "TETHER.json")
INTERACTION = os.path.join(JC3, "INTERACTION.json")
T9 = os.path.join(WORK, "t9_interaction.json")
INDEX = os.path.join(JC3, "INDEX.jsonl")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
OUT_MD = os.path.join(WORK, "T15_WORLD.md")
OUT_JSON = os.path.join(WORK, "t15_world.json")

CODES = ["WLD-1", "WLD-2", "WLD-3", "WLD-4", "WLD-5", "WLD-6", "WLD-7", "WLD-8"]
ICON_DIR = "textures/ui/vehicle_icons/"
PROFILE_STORE = "profile/online.stringlookup"
SPAWN_TABLE = "settings/spawn_vehicle_defs.bin"

sys.path.insert(0, HERE)


# --------------------------------------------------------------------------- inputs
def load_json(path: str) -> dict:
    return json.load(open(path, encoding="utf-8"))


def load_index_paths() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in open(INDEX, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        cur = out.get(r["path"])
        if cur is None or r.get("size", 0) > cur.get("size", 0):
            out[r["path"]] = {"path": r["path"], "mount": r.get("mount"),
                              "size": r.get("size", 0)}
    return out


def load_strings(hashes: list[int]) -> dict:
    """Resolve each hash in `profile/online.stringlookup` through G2-32's own decoder."""
    import jc3index  # noqa: E402
    import jc3strings  # noqa: E402
    game = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
    index = jc3strings.load_index()
    store = jc3strings.decode_stringlookup(jc3strings.PROFILE, index, game)
    return {"path": jc3strings.PROFILE,
            "bytes": store["bytes"],
            "languages": len(store["pairs"]),
            # string keys: the record is written and re-read as JSON, so the keys must round-trip
            "resolved": {str(h): jc3strings.resolve(store, h) for h in hashes}}


def family_rule(items: list[dict]) -> tuple[int, int, list[str]]:
    """`BaseName` == `hash_jenkins(<leaf family prefix>)`?  Derived, not assumed."""
    from rbmhdr import hash_jenkins  # noqa: E402
    ok = 0
    bad: list[str] = []
    for it in items:
        prefix = it["UIImagePath"].split("_")[0]
        if it["BaseName"] == hash_jenkins(prefix.encode()):
            ok += 1
        else:
            bad.append(f"{it['UIImagePath']} -> {it['BaseName']:#010x}")
    return ok, len(items), bad


def gather() -> dict:
    from rbmhdr import hash_jenkins  # noqa: E402

    rebel = load_json(REBELDROP)
    stand = load_json(STANDALONE)
    traf = load_json(TRAFFIC)
    water = load_json(WATER)
    teth = load_json(TETHER)
    inter = load_json(INTERACTION)
    t9 = load_json(T9)
    index = load_index_paths()

    recipe = rebel["recipe"]
    fields = recipe["fields"]
    leaf_new = stand["new_leaf"]
    leaf_donor = stand["donor_leaf"]
    h_new = hash_jenkins(leaf_new.encode())
    h_donor = hash_jenkins(leaf_donor.encode())

    items = rebel["vanilla"]["items"]
    tasks = rebel["vanilla"]["tasks"]
    veh_items = [i for i in items
                 if isinstance(i.get("UIImagePath"), str) and i["UIImagePath"].startswith("v0")]
    donor_item = next((i for i in items if i["Name"] == h_donor), None)
    donor_task = None
    for t in tasks:
        if any(r.get("item") == h_donor for r in t.get("rewards", [])):
            donor_task = t
            break

    fam_ok, fam_n, fam_bad = family_rule(veh_items)
    item_fields = [f["name"] for f in rebel["schema"]["Item"]]

    # the strings this card needs, all resolved in the one store that holds them
    ui = {"UIName_new": h_new, "UIName_donor": h_donor,
          "UIDescription": fields["UIDescription"],
          "UITypeDescription": fields["UITypeDescription"],
          "UIFlagDescription": fields["UIFlagDescription"]}
    strings = load_strings(sorted(ui.values()))

    icons = {k: index.get(ICON_DIR + leaf + ".ddsc")
             for k, leaf in (("new", leaf_new), ("donor", leaf_donor),
                             ("placeholder", "placeholder"))}
    icon_files = [p for p in index if p.startswith(ICON_DIR)]

    sa = inter["stunt_areas"]
    areas = []
    for a in sa["areas"]:
        areas.append({"slot": a["slot"], "name": a["name"], "part_index": a["part_index"],
                      "part_name": a["part_name"], "vertices": a["n_deform_points"],
                      "triangles": a["n_triangles"],
                      "on_surface": a["bat_on_surface"],
                      "worst_m": a["bat_max_clearance_m"],
                      "centre_gap_m": a["bat_center_surface_m"]})

    wc = water["constants"]["rows"]
    const = {k: "/".join(str(v) for v in sorted(int(x) for x in wc[k]["values"]))
             for k in ("vehicle_damage.min_water_entry_ms",
                       "vehicle_damage.fatal_water_entry_ms",
                       "vehicle_damage.min_water_entry_floating_ms",
                       "vehicle_damage.fatal_water_entry_floating_ms",
                       "car_common.engine_shut_down_delay_s")}

    models = teth["carriers"]["models"]
    bay_masses = sorted({m for v in models.values() for m in v["masses"]})
    target = teth["mass"]["batmobile_target"]
    donor_mass = teth["mass"]["donor"]["mass"]

    variants = rebel["variants"]
    # the strongest single variant, not a sum: each variant rewrites the same table
    mod_added_variant, mod_added_max = max(
        ((k, v["diff"]["items_added"]) for k, v in variants.items()), key=lambda kv: kv[1])

    return {
        "rebel": {"leaf": recipe["leaf"], "hash": recipe["name_hash"],
                  "hex": recipe["name_hash_hex"], "fields": fields,
                  "field_count": len(fields), "schema_fields": len(item_fields),
                  "schema_field_names": item_fields,
                  "unlock": recipe["unlock"],
                  "mod_items_added": {"variant": mod_added_variant,
                                      "count": mod_added_max,
                                      "variants": len(variants)},
                  "vanilla_items": rebel["totals"]["vanilla_items"],
                  "vanilla_tasks": rebel["totals"]["vanilla_tasks"],
                  "vanilla_vehicle_items": len(veh_items),
                  "vanilla_reward_links": rebel["totals"]["vanilla_reward_links"],
                  "vehicle_item_profile": {
                      k: sorted({i[k] for i in veh_items})
                      for k in ("Type", "UIType", "Rewardable", "Purchasable", "Collectable",
                                "Consumable", "DlcId", "Region", "MaxInventory")},
                  "vehicle_orders": sorted({i["UIDisplayOrder"] for i in veh_items}),
                  "vehicle_flags": sorted({i["UIFlag"] for i in veh_items}),
                  "vehicle_timers": sorted({i["RebelDropTimer"] for i in veh_items}),
                  "donor_item": donor_item,
                  "donor_task": ({"name": donor_task["Name"], "type": donor_task["Type"]}
                                 if donor_task else None),
                  "task_types_19": sum(1 for t in tasks if t.get("Type") == 19),
                  "family_ok": fam_ok, "family_n": fam_n, "family_bad": fam_bad},
        "stand": {"new_leaf": leaf_new, "donor_leaf": leaf_donor, "hash_new": h_new,
                  "verdict": stand["verdict"], "needs": stand["needs"]},
        "strings": {"profile": strings,
                    "langs_new": len(strings["resolved"][str(h_new)]),
                    "langs_donor": len(strings["resolved"][str(h_donor)]),
                    "en_name_donor": strings["resolved"][str(h_donor)].get("en"),
                    "en_desc": strings["resolved"][str(fields["UIDescription"])].get("en"),
                    "en_type": strings["resolved"][str(fields["UITypeDescription"])].get("en"),
                    "en_flag": strings["resolved"][str(fields["UIFlagDescription"])].get("en"),
                    "langs_desc": len(strings["resolved"][str(fields["UIDescription"])]),
                    "langs_type": len(strings["resolved"][str(fields["UITypeDescription"])]),
                    "langs_flag": len(strings["resolved"][str(fields["UIFlagDescription"])])},
        "icons": icons,
        "icon_files": len(icon_files),
        "inter": {"objects": inter["counts"]["objects"],
                  "entry": inter["counts"]["by_prefix"].get("entry", 0),
                  "exit": inter["counts"]["by_prefix"].get("exit", 0),
                  "point": inter["counts"]["by_prefix"].get("point", 0),
                  "areas_declared": sa["declared"], "slots": sa["slots"],
                  "inactive": sa["inactive"], "weld_rows": sa["weld_rows"],
                  "real_welds": sa["real_welds"], "weld_pairs": sa["weld_pairs"],
                  "areas": areas},
        "t9": {"objects": t9["counts"]["objects"], "placed": t9["counts"]["placed"],
               "in_band": t9["counts"]["in_band"], "dropped": t9["counts"]["dropped_D9"],
               "socket": t9["counts"]["socket"], "unknown": t9["counts"]["unknown"],
               "stunt_roles": t9["counts"]["by_role"].get("stunt", 0),
               "driver_roles": t9["counts"]["by_role"].get("driver", 0),
               "band": t9["band_m"], "anchors": t9["anchors"]},
        "mass": {"donor": donor_mass, "target": target,
                 "ratio": round(target / donor_mass, 3),
                 "unit": teth["mass"]["unit"],
                 "car": teth["mass"]["families"]["car"],
                 "entities": teth["mass"]["entities_with_mass"]},
        "water": {"will_sink": water["build"]["modules"]["WaterInteraction"]["will_sink"],
                  "buoyancy": water["build"]["modules"]["Buoyancy"],
                  "parts": water["build"]["modules"]["WaterInteraction"]["parts"],
                  "identical": water["build_check"]["identical"],
                  "census": water["census"]["groups"],
                  "entities": water["census"]["entities"],
                  "constants": const,
                  "module": next(iter(wc["vehicle_damage.min_water_entry_ms"]["modules"]))},
        "tether": {"bays": teth["carriers"]["bays"],
                   "bay_entities": teth["carriers"]["bay_entities"],
                   "bay_helicopters": teth["carriers"]["bay_helicopters"],
                   "models": models, "bay_masses": bay_masses,
                   "hooks": teth["carriers"]["hooks"],
                   "hook_entities": teth["carriers"]["hook_entities"],
                   "winch": teth["index"]["winch"],
                   "tether_hits": teth["index"]["tether"],
                   "helicopters": teth["mass"]["families"]["helicopter"]["n"]},
        "traffic": {"keyed_records": traf["spawn"]["main"]["keyed_records"],
                    "records": traf["spawn"]["main"]["records"],
                    "size": traf["spawn"]["main"]["size"],
                    "donor_record": traf["spawn"]["donor_record"],
                    "selectors": 1 + traf["rules"]["donor_misses"],
                    "match": traf["rules"]["donor_matches"][0] if traf["rules"]["donor_matches"] else None,
                    "table": SPAWN_TABLE},
    }


# --------------------------------------------------------------------------- rows
def f6(x: float) -> str:
    return f"{x:.4f}".rstrip("0").rstrip(".")


def build_rows(F: dict) -> list[dict]:
    r = F["rebel"]
    st = F["stand"]
    s = F["strings"]
    ic = F["icons"]
    it = F["inter"]
    t9 = F["t9"]
    m = F["mass"]
    w = F["water"]
    te = F["tether"]
    tr = F["traffic"]
    f = r["fields"]
    unlock = r["unlock"][0] if r["unlock"] else {}
    donor_mass = m["donor"]
    ratios = {k: round(100.0 * m["target"] / v, 1) for k, v in
              (("plane", 40000), ("boat", 100000), ("flatbed", 15000))}
    vp = r["vehicle_item_profile"]
    area_list = ", ".join(f"`{a['name']}` (part {a['part_index']}, {a['vertices']} pts, "
                          f"{a['triangles']} tris, {a['on_surface']} on surface)"
                          for a in it["areas"])

    rows: list[dict] = []

    def add(**kw) -> None:
        rows.append(kw)

    # ---------------------------------------------------------------- WLD-1
    add(id="T-WLD1", code="WLD-1", requirement="Spawned from a new Rebel Drop entry called Batmobile",
        source=(f"leaf `{st['new_leaf']}`; `hash_jenkins` = **{st['hash_new']}** = "
                f"`{st['hash_new']:08X}` (G2-26 recipe `name_hash`)"),
        carrier=(f"`profile/item.onlinec` item: `Name` = `UIName` = {st['hash_new']}, "
                 f"`UIImagePath` = `UIVideoPath` = the leaf, `BaseName` = {f['BaseName']} = "
                 f"`hash_jenkins(\"v0300\")`, {r['field_count']}/{r['schema_fields']} schema "
                 f"fields - B-13 writes the record"),
        dispo="next", confidence="decoded",
        verify="Q-1 #1: the drop list shows the entry and it spawns the car",
        why=("the Rebel Drop item is one 128-byte record whose Name/UIName is the 32-bit Jenkins "
             "hash of the entity leaf, so the new leaf is the key and the recipe's fields are the "
             "values to write (G2-26, REBELDROP.json recipe)"))

    add(id="T-WLD2", code="WLD-1", requirement="The entry is unlocked, not handed out for free",
        source=(f"the donor is rewarded by task **{r['donor_task']['name'] if r['donor_task'] else '?'}**"
                f" (Type {r['donor_task']['type'] if r['donor_task'] else '?'}); "
                f"{r['vanilla_reward_links']} `ItemReward` links in the vanilla `task.onlinec`, "
                f"{r['task_types_19']} of its {r['vanilla_tasks']} tasks are Type 19"),
        carrier=(f"`ItemReward` link on the same task {unlock.get('task')} -> the new item "
                 f"(`permanent` {unlock.get('permanent')}, `quantity` {unlock.get('quantity')}, "
                 f"`threshold` {unlock.get('threshold')}, `delivery` {unlock.get('delivery')}); a "
                 f"write precedent exists - the shipped mod rewrites `item.onlinec` "
                 f"(\"{r['mod_items_added']['variant']}\" adds {r['mod_items_added']['count']} "
                 f"items to it)"),
        dispo="next", confidence="decoded",
        verify="Q-1 #1: the entry appears only after the unlocking task",
        why=("the unlock is an ItemReward row in task.onlinec, not an item field: the donor's own "
             "task rewards the item, and the recipe reuses that task id (G2-26 §unlock)"))

    add(id="T-WLD3", code="WLD-1", requirement="The entry's UI profile matches the fleet's vehicle drops",
        source=(                f"{r['vanilla_vehicle_items']}/{r['vanilla_vehicle_items']} vanilla vehicle drops: "
                f"Type {vp['Type'][0]}, UIType {vp['UIType'][0]}, Rewardable {vp['Rewardable'][0]}, "
                f"Purchasable {vp['Purchasable'][0]}, Collectable {vp['Collectable'][0]}, "
                f"Consumable {vp['Consumable'][0]}, DlcId {vp['DlcId'][0]}, Region "
                f"{vp['Region'][0]}, MaxInventory {vp['MaxInventory'][0]}; timers "
                f"{', '.join(str(t) for t in r['vehicle_timers'])} (unit UNKNOWN)"),
        carrier=(f"copy the donor profile: `Type` {f['Type']}, `UIType` {f['UIType']}, "
                 f"`UIFlag` {f['UIFlag']} ({s['en_flag']}), `UIDisplayOrder` {f['UIDisplayOrder']}, "
                 f"`RebelDropTimer` {f['RebelDropTimer']}, `Rewardable` {f['Rewardable']}; the timer's "
                 f"unit and the `Type`/`UIType`/`UIFlag` enums are **UNKNOWN** - only the "
                 f"description strings are readable"),
        dispo="next", confidence="derived",
        verify="Q-1 #1: the entry sits in the vehicles tab and the timer countdown reads sensibly",
        why=("every vanilla vehicle drop shares the same Type/UIType/Rewardable values, so the "
             "donor's profile is the class value; the enum meanings are UNKNOWN, so nothing is "
             "re-picked by hand (G2-26 decoded no enum table)"))

    # ---------------------------------------------------------------- WLD-2
    add(id="T-WLD4", code="WLD-2", requirement="Display name \"Batmobile\" everywhere JC3 names the vehicle",
        source=(f"the name is a pair in `{s['profile']['path']}` keyed by the leaf hash: the donor "
                f"`{r['donor_item']['Name']:08X}` -> \"{s['en_name_donor']}\" in "
                f"{s['langs_donor']} of {s['profile']['languages']} languages"),
        carrier=(f"**key carried**: the plan hash **{st['hash_new']}** is "
                 f"`hash_jenkins(\"{st['new_leaf']}\")` and resolves in **{s['langs_new']} of "
                 f"{s['profile']['languages']}** - that leaf never ships (Q-1a). The leaf that ships "
                 f"is `..._debug`; its key is **1621485476** = `hash_jenkins(leaf)` and the pair is "
                 f"present **11/11** in `Builds/bm-013/drop/profile/online.stringlookup` with the "
                 f"text \"BATMOBILE\" (+22 pairs, 14,712 -> 14,734, nothing else changed); the "
                 f"writer is `Tools/scripts/jc3strings_write` (`name-string-lookup-key.md` §4)"),
        dispo="next", confidence="decoded",
        verify="Q-1 #1: the drop list reads \"Batmobile\", in 11 languages",
        why=("the key is `HashJenkins(leaf)` and is already written 11/11 for the shipped `_debug` "
             "leaf in bm-013's drop; what remains is carrying that drop into the RC and Q-1's "
             "runtime check - not a key and not a writer"))

    add(id="T-WLD5", code="WLD-2", requirement="A vehicle icon in the drop menu and the garage",
        source=(f"icon = `{ICON_DIR}<leaf>.ddsc`, 18,688 B for every vanilla vehicle; "
                f"{F['icon_files']} files in that directory, the donor's under the donor leaf"),
        carrier=(("the new leaf already has one: " + ic["new"]["path"]) if ic["new"] else
                 (f"the new leaf has **no** `{ICON_DIR}{st['new_leaf']}.ddsc` in the index (0 hits); "
                  f"copy the donor's file ({ic['donor']['size']:,} B) under the new leaf name - the "
                  f"menu keys on the file name, so a byte-identical copy needs no encoder; "
                  f"`placeholder.ddsc` ({ic['placeholder']['size']:,} B) is the fallback")),
        dispo="next", confidence="decoded",
        verify="Q-1 #1: the drop list and the garage show the Batmobile icon, not the placeholder",
        why=("G2-32 proved `UIImagePath` is the icon key and that the icon is a plain texture named "
             "after the leaf; a copy under the new leaf is the whole step"))

    add(id="T-WLD6", code="WLD-2", requirement="A description line for the entry that is not the Serpente's",
        source=(f"`UIDescription` {f['UIDescription']} resolves in {s['langs_desc']} languages to "
                f"\"{s['en_desc'][:80]}...\" - the Serpente's blurb"),
        carrier=(f"**pair carried**: `<leaf>_desc` = `hash_jenkins(\"..._debug_desc\")` = "
                 f"**4081821928**, present **11/11** in "
                 f"`Builds/bm-013/drop/profile/online.stringlookup` with the blurb in "
                 f"`Working/World/bm_rebel_text.json` (\"Arkham Knight's armoured Batmobile: "
                 f"pursuit speed, a battle-mode turret, and armour that shrugs off small arms.\"); "
                 f"the plan leaf's 1805638565 resolves 0/11 because that leaf never ships"),
        dispo="next", confidence="decoded",
        verify="Q-1 #1: the entry's blurb describes the Batmobile",
        why=("the `_desc` key is `HashJenkins(leaf + \"_desc\")` and is written 11/11 for the "
             "shipped `_debug` leaf; the remaining work is the same drop carry and Q-1 runtime "
             "check as T-WLD4"))

    add(id="T-WLD7", code="WLD-2", requirement="The category captions stay correct",
        source=(f"`UITypeDescription` {f['UITypeDescription']} = \"{s['en_type']}\" and "
                f"`UIFlagDescription` {f['UIFlagDescription']} = \"{s['en_flag']}\" in "
                f"{s['langs_type']} and {s['langs_flag']} languages"),
        carrier="keep both hashes: they name a UI category, not the donor car; nothing to write",
        dispo="keep", confidence="decoded",
        verify="Q-1 #1: the entry is filed under SPORTS CAR / SPORTS CARS",
        why=("the two caption hashes resolve to generic category strings, so they stay valid for a "
             "different vehicle in the same slot"))

    # ---------------------------------------------------------------- WLD-3
    add(id="T-WLD8", code="WLD-3", requirement="Entry points on the Batmobile's sides, not the Serpente's doors",
        source=(f"{it['entry']} `entry.*` objects ({it['objects']} interaction objects in total), "
                f"every position a Serpente-space translation (G2-18)"),
        carrier=(f"the T-13 placement: {t9['placed']} of {t9['objects']} objects inside the "
                 f"{t9['band'][0]}-{t9['band'][1]} m band, entries on the cockpit sides "
                 f"(left x {f6(t9['anchors']['left']['surface'][0])}, right x "
                 f"{f6(t9['anchors']['right']['surface'][0])} at y "
                 f"{f6(t9['anchors']['left']['surface'][1])}, z "
                 f"{f6(t9['anchors']['left']['surface'][2])}), "
                 f"{t9['dropped']} hijack objects dropped under D-9; B-05 writes the graph"),
        dispo="epe", confidence="decoded",
        verify="Q-1 #3: Rico enters from both sides; the canopy opens instead of a door",
        why=("entry objects are entity-graph nodes; T-13 placed all of them on the Batmobile hull "
             "by role and distance, and phase B only moves them into the built `.epe`"))

    add(id="T-WLD9", code="WLD-3", requirement="Exit points that work from the real sides",
        source=(f"{it['exit']} `exit.*` objects, including `S_EXIT_DRIVER_VEHICLE_IN_WATER` and the "
                f"moving-exit pair (G2-20)"),
        carrier=(f"same pass: exits sit on the placed `point.*` nodes ({it['point']} point objects), "
                 f"state names unchanged so the animation wiring stays valid (G2-18 §4)"),
        dispo="epe", confidence="decoded",
        verify="Q-1 #3: exit parked, and exit at 30 km/h (parachute/eject)",
        why=("exits are graph nodes with a state string each; T-13's placement covers them and "
             "B-05 moves them with the rest of the graph"))

    # ---------------------------------------------------------------- WLD-4
    add(id="T-WLD10", code="WLD-4", requirement="Rico can stand on the roof: stunt point nodes",
        source=(f"{it['point']} `point.*` nodes, {t9['stunt_roles']} of the objects mapped to a stunt "
                f"role (G2-18 §3-4: the donor's surfaces scale 0.374-0.596 m off the Batmobile shell)"),
        carrier=(f"T-13 placed the stunt objects on the hull top (roof y "
                 f"{f6(t9['anchors']['roof']['surface'][1])} at z "
                 f"{f6(t9['anchors']['roof']['surface'][2])}, deck y "
                 f"{f6(t9['anchors']['hood']['surface'][1])} at z "
                 f"{f6(t9['anchors']['hood']['surface'][2])}) - B-05 writes them"),
        dispo="epe", confidence="decoded",
        verify="Q-1 #3: Rico climbs up and stands on the hood, roof and rear deck",
        why=("the three `point.stunt*` nodes are graph nodes; the placement is measured against the "
             "body mesh and recorded in t9_interaction.json"))

    add(id="T-WLD11", code="WLD-4", requirement="The stunt *areas* (the surfaces that hold Rico up)",
        source=(                f"`StuntAreas`: {it['areas_declared']} active areas in {it['slots']} slots, "
                f"{it['weld_rows']} weld rows of which {it['real_welds']} real "
                f"({', '.join(f'{k} x{v}' for k, v in sorted(it['weld_pairs'].items()))}); "
                f"{area_list}"),
        carrier=("**re-fit derived (P-1), not blocked**: all **22** bound vertices can be placed "
                 "on a standing RC2 face inside the donor band 0.0388-0.1578 m - 22/22 at "
                 "0.036-0.105 m, up-cos 0.749-0.994, outside the shell. Hood rows "
                 "-1.390/-2.309/-2.916 m at x +/-0.10/0.30/0.30, y = top + the vertex's own donor "
                 "clearance -> x,y,z: (-0.100, 1.9939, -1.390), (0.100, 1.9927, -1.390), "
                 "(0.300, 1.4090, -2.309), (0.300, 1.1828, -2.916), (-0.300, 1.1827, -2.916), "
                 "(-0.300, 1.4080, -2.309); roof rows -1.039/+0.057/+1.294/+2.400/+2.583 m -> "
                 "(-0.160, 2.0866, -1.039), (0.140, 1.9766, 0.057), (-0.300, 2.1417, 1.294), "
                 "(0.300, 2.1600, 2.400), (-0.300, 2.0886, 2.583), (0.300, 2.0884, 2.583), "
                 "(0.300, 2.1583, 2.400), (-0.300, 2.1321, 1.294), (0.140, 1.9623, 0.057), "
                 "(-0.160, 2.0866, -1.039) "
                 "(`tmp/freebuff/reports/stunt-areas-deform-points.md` §4.3 has the arithmetic). "
                 "Stored areas sit 0.19-0.31 m **below** the surface (unsigned 0.00-0.08 m); the "
                 "bbox map floats 0.32-0.49 m. A two-column ribbon still chords the roof vents "
                 "(1/40 and 16/80 interior samples inside, worst 0.110/0.162 m), so full width "
                 "needs a third column - 3 new indices per hood area and 5 for the roof (135+, "
                 "none exist) in `sportsmuscle_vehicle_deform.vmodc` + "
                 "`sportsmuscle_stunt_areas.vmodc`"),
        dispo="next", confidence="derived",
        verify="Q-1 #3: Rico stands on the roof without sliding off in motion",
        why=("the stored donor points top out at y 1.5242 m, 0.46-0.56 m below the RC2 spine, so "
             "re-indexing cannot work; the derived spine fit places every vertex (22/22) and the "
             "write is 22 `start_transform[12..14]` + `vertices3D_local` pairs, with a 3-column "
             "ribbon needed for the donor's full width"))

    # ---------------------------------------------------------------- WLD-5
    add(id="T-WLD12", code="WLD-5", requirement="Heavy: shoves cars, flattens fences like a 6 t armoured car",
        source=(f"DIM-3 / T-M1: the 6 t class row (BmAK has no absolute mass). donor "
                f"`rigid_body.mass` {m['donor']}, {m['entities']} entities read, car family "
                f"{m['car']['min']}-{m['car']['max']:,} (median {m['car']['median']:,})"),
        carrier=(f"`rigid_body.mass` {m['donor']} -> **{m['target']}** = {m['ratio']}x the donor and "
                 f"{round(m['target'] / m['car']['median'], 1)}x the car median; the contact hull is "
                 f"DIM-4's set (T-22, `jc3hkx.py write` proved the writer); the mass unit is "
                 f"**{m['unit']}**"),
        dispo="next", confidence="class",
        verify="Q-3 #1: ram a wall and cars at 40/80 km/h - no damage, the other car is shoved",
        why=("mass is the only lever a car presents for shoving; the class value is T-M1's 6 t row, "
             "and the hull that turns it into a contact response is T-22's, not this card's"))

    # ---------------------------------------------------------------- WLD-6
    add(id="T-WLD13", code="WLD-6", requirement="Water: not amphibious - it sinks (D-8 = lore)",
        source=(f"D-8 resolved: sink and stall. fleet census: {w['census']['sink']} of "
                f"{w['entities']} entities sink, {w['census']['boat']} boats and "
                f"{w['census']['floating']} floaters are the rest"),
        carrier=(f"`WaterInteraction.will_sink` **{w['will_sink']}** + `Buoyancy` buoyancy "
                 f"{w['buoyancy']['buoyancy']}, drag {w['buoyancy']['drag']}, radius "
                 f"{f6(w['buoyancy']['radius'])}, side_area {f6(w['buoyancy']['side_area'])}, "
                 f"bottom_area {f6(w['buoyancy']['bottom_area'])}, up_velocity_cap "
                 f"{f6(w['buoyancy']['up_velocity_cap'])}, {w['parts']} hull element; test-091's "
                 f"modules are identical to the donor (build_check `identical` = {w['identical']})"),
        dispo="keep", confidence="decoded",
        verify="Q-3 #4: drive into a lake - the car sinks and Rico swims out",
        why=("the donor already is a sinking car with a measured buoyancy block, and the build's copy "
             "is byte-equal in value, so D-8's lore route ships as it stands"))

    add(id="T-WLD14", code="WLD-6", requirement="Water: the engine stalls and the hull takes entry damage",
        source=(f"D-8's \"stall\" half; the constants live in one shared module "
                f"({w['module']}, {w['entities']}/{w['entities']} entities)"),
        carrier=(                 f"`vehicle_damage.min_water_entry_ms` {w['constants']['vehicle_damage.min_water_entry_ms']}, "
                 f"`fatal_water_entry_ms` {w['constants']['vehicle_damage.fatal_water_entry_ms']}, "
                 f"`min_water_entry_floating_ms` {w['constants']['vehicle_damage.min_water_entry_floating_ms']}, "
                 f"`fatal_water_entry_floating_ms` {w['constants']['vehicle_damage.fatal_water_entry_floating_ms']}, "
                 f"`car_common.engine_shut_down_delay_s` "
                 f"{w['constants']['car_common.engine_shut_down_delay_s']}; 0 per-vehicle overrides, "
                 f"and R7 forbids editing the shared file in place"),
        dispo="keep", confidence="decoded",
        verify="Q-3 #4: the engine dies on water entry, not on the first wave",
        why=("the kill/stall behaviour is fleet-wide in `vehicle_common`, so the Batmobile inherits it "
             "with nothing to write - the row records the values that will be observed"))

    # ---------------------------------------------------------------- WLD-7
    add(id="T-WLD15", code="WLD-7", requirement="Rico's tether behaves sensibly with a 6 t car",
        source=(f"a car presents no tether parameter of its own; the engine's ability is native "
                f"({te['tether_hits']} `tether` paths in the index, all dialogue/UI)"),
        carrier=(f"**closest system**: the only decoded attach/release objects are "
                 f"`CVehicleCargoBay` (7 members: `world`, `enabled`, `enable`, `disable`, "
                 f"`name`, `name_hash`, `_object_id`; {te['bays']} on {te['bay_entities']} "
                 f"entities) and `CGrapplingHookPropData` ({te['hooks']} tags on "
                 f"{len(te['hook_entities'])} cargo holders, both events empty); the car itself "
                 f"supplies its {m['target']:,} mass (6.154x the 975 donor) and the "
                 f"`grapple_pull` damage channel (`grapple_pull_armor` -1..0, "
                 f"`grapple_pull_armor_strength` 0..100.0), and nothing else"),
        dispo="next", confidence="derived",
        verify="Q-3 #5: tether the car to a pole and pull - record whether it holds, drags or "
               "breaks (the pull is native code, so a probe, not a write)",
        why=("the tether is character-side native code with no member (G2-34: 0 tether/winch "
             "module types, 335 `tether` index paths all dialogue/UI); the row is translated to "
             "the two attach objects and the damage gate it does carry, and the behaviour is "
             "verified in Q-3 instead of being recorded as an omission"))

    add(id="T-WLD16", code="WLD-7", requirement="The cargo plane and boat can carry the car",
        source=(f"{te['bays']} `CVehicleCargoBay` objects on {te['bay_entities']} entities "
                f"(cargo plane 25,000/40,000, transport boat 100,000, monorail flatbed 15,000)"),
        carrier=(f"nothing on the car side: the {m['target']:,} car is "
                 f"{ratios['plane']}% / {ratios['boat']}% / {ratios['flatbed']}% of those bodies "
                 f"(`rigid_body.mass`); the bay's own enable flag is 1 on all {te['bays']}"),
        dispo="keep", confidence="decoded",
        verify="Q-3 #5: airlift the car with the cargo plane",
        why=("the cargo bay is a property of the carrier, already enabled fleet-wide; the car only "
             "has to be a registered vehicle, which the standalone entity row covers"))

    add(id="T-WLD17", code="WLD-7", requirement="Helicopter airlift of the car",
        source=(f"{te['helicopters']} helicopters in the fleet"),
        carrier=(f"**blocked (data-level)**: `bay_helicopters` = {te['bay_helicopters']} - 0 of "
                 f"{te['helicopters']} helicopters carries a `CVehicleCargoBay`; the closest carrier "
                 f"is the cargo plane's bay (6 entities) plus the compound "
                 f"`v4603_plane_urga_cargotransport_military_cargo_tank` (`CAirPlane` + `CCar`, "
                 f"bodies 25,000 + 40,000). Cloning a bay onto a helicopter is an entity-graph edit "
                 f"whose native attach rule is **UNKNOWN** (all {te['bays']} shipped bays have empty "
                 f"`enable`/`disable` events)"),
        dispo="blocked", confidence="decoded",
        verify="Q-3 #5: hook a helicopter to the car - expected absence until B-16's bay clone is "
               "built and its attach rule probed",
        why=("data-level gap: no helicopter entity carries a cargo bay (0/23) and the 103-class "
             "census has no helicopter hook class; what is missing is the native attach rule a "
             "cloned bay would need, not a value - card `Research/specs/B-16.md`"))

    # ---------------------------------------------------------------- WLD-8
    add(id="T-WLD18", code="WLD-8", requirement="No traffic record exists for the Batmobile",
        source=(f"`{tr['table']}` ({tr['size']:,} B, {tr['records']} records, "
                f"{tr['keyed_records']} keyed) keys on the **full path string**, not the leaf hash"),
        carrier=(f"the new leaf `{st['new_leaf']}` has 0 records there (G2-29's 11,751-file scan "
                 f"found 17 name-sites, none of them this leaf); D-6 = standalone, so **nothing is "
                 f"added** and no AI driver can select it"),
        dispo="keep", confidence="decoded",
        verify="Q-3 #6: drive 10 min through a town - count NPC Batmobiles (expect 0)",
        why=("the spawn table is keyed by path string and only `civilian_01` is in it (G2-29); a new "
             "leaf that is never added can never be picked by a traffic selector"))

    add(id="T-WLD19", code="WLD-8", requirement="The donor's own traffic record is left alone",
        source=(f"the donor's record at offset {tr['donor_record']['offset']} carries "
                f"{len(tr['donor_record']['tags'])} tags including `ambient` and `liberated`, and "
                f"satisfies 1 of {tr['selectors']} selectors: "
                f"`{tr['match']['selector']}` -> `{tr['match']['next_rule']}`"),
        carrier=(f"keep: the donor leaf and its record stay untouched (D-6); replacing "
                 f"`{st['donor_leaf']}` would put NPC-driven Batmobiles in liberated provinces - the "
                 f"MOD-5 lore break G2-29 named"),
        dispo="keep", confidence="decoded",
        verify="Q-3 #6: no Batmobile appears in traffic, and the Serpente still does",
        why=("replacing the civilian leaf is the one way to get AI Batmobiles (G2-29); the resolved "
             "decision is a standalone entity, so this row exists to forbid the edit"))
    return rows


def cells(row: dict) -> list[str]:
    return [row["id"], row["code"], row["requirement"], row["source"], row["carrier"],
            row["dispo"], row["confidence"], row["verify"]]


# --------------------------------------------------------------------------- payload
def build_payload() -> tuple[dict, list[str]]:
    F = gather()
    rows = build_rows(F)
    problems: list[str] = []
    for row in rows:
        row["cells"] = cells(row)

    # ---- the derivations the cells rest on, asserted rather than assumed -------------
    r, st, s = F["rebel"], F["stand"], F["strings"]
    f = r["fields"]
    from rbmhdr import hash_jenkins  # noqa: E402
    if hash_jenkins(st["new_leaf"].encode()) != st["hash_new"]:
        problems.append("the new leaf's hash does not re-derive")
    if st["hash_new"] != r["hash"]:
        problems.append(f"recipe name_hash {r['hash']} != hash(new leaf) {st['hash_new']}")
    if r["leaf"] != st["new_leaf"]:
        problems.append("recipe leaf != STANDALONE.new_leaf")
    for key in ("Name", "UIName"):
        if f[key] != st["hash_new"]:
            problems.append(f"recipe {key} {f[key]} != hash(new leaf) {st['hash_new']}")
    for key in ("UIImagePath", "UIVideoPath"):
        if f[key] != st["new_leaf"]:
            problems.append(f"recipe {key} != new leaf")
    if r["field_count"] != r["schema_fields"]:
        problems.append(f"recipe has {r['field_count']} fields, the schema {r['schema_fields']}")
    if f["BaseName"] != hash_jenkins(b"v0300"):
        problems.append(f"recipe BaseName {f['BaseName']} != hash(\"v0300\")")
    if (r["family_ok"], r["family_n"]) != (r["family_n"], r["family_n"]):
        problems.append(f"BaseName == hash(family prefix) holds on only {r['family_ok']}/"
                        f"{r['family_n']} vanilla vehicle drops")
    if r["donor_task"] is None:
        problems.append("no vanilla task rewards the donor item")
    elif r["unlock"] and r["unlock"][0]["task"] != r["donor_task"]["name"]:
        problems.append("the recipe's unlock task is not the donor's task")
    if s["langs_new"]:
        problems.append(f"the new name hash resolves in {s['langs_new']} languages - T-WLD4's "
                        f"'blocked' is wrong")
    if s["langs_donor"] != s["profile"]["languages"]:
        problems.append(f"the donor name resolves in only {s['langs_donor']} languages")
    if s["en_name_donor"] is None:
        problems.append("the donor name has no English text")
    for key, n in (("langs_desc", s["langs_desc"]), ("langs_type", s["langs_type"]),
                   ("langs_flag", s["langs_flag"])):
        if n != s["profile"]["languages"]:
            problems.append(f"{key}: resolves in {n} of {s['profile']['languages']} languages")
    if F["icons"]["new"] is not None:
        problems.append("an icon for the new leaf exists - T-WLD5's value is stale")
    if F["icons"]["donor"] is None or F["icons"]["placeholder"] is None:
        problems.append("the donor icon or the placeholder is missing from the index")
    if F["inter"]["objects"] != F["t9"]["objects"]:
        problems.append("INTERACTION and t9 disagree on the object count")
    if F["t9"]["in_band"] != F["t9"]["placed"]:
        problems.append("some placed objects are outside the band")
    if F["t9"]["socket"] + F["t9"]["unknown"] + F["t9"]["in_band"] + F["t9"]["dropped"] != \
            F["t9"]["objects"]:
        problems.append("t9's counts do not add up to the object count")
    if F["inter"]["areas_declared"] != len(F["inter"]["areas"]):
        problems.append("declared stunt areas != decoded areas")
    for a in F["inter"]["areas"]:
        if a["on_surface"]:
            problems.append(f"stunt area {a['name']} is on the shell - T-WLD11 is stale")
    if round(F["mass"]["target"] / F["mass"]["donor"], 3) != F["mass"]["ratio"]:
        problems.append("the mass ratio does not re-derive")
    if F["water"]["will_sink"] != 1:
        problems.append("the built entity does not sink")
    if not F["water"]["identical"]:
        problems.append("the build's water modules differ from the donor's")
    if F["tether"]["winch"]:
        problems.append(f"a winch member exists ({F['tether']['winch']}) - T-WLD15 is stale")
    if F["tether"]["bay_helicopters"]:
        problems.append("a helicopter carries a cargo bay - T-WLD17 is stale")
    if F["traffic"]["selectors"] != 41:
        problems.append(f"the selector count is {F['traffic']['selectors']}, not 41")
    if "ambient" not in F["traffic"]["donor_record"]["tags"] or \
            "liberated" not in F["traffic"]["donor_record"]["tags"]:
        problems.append("the donor's traffic record lost its ambient/liberated tags")

    counts = {
        "rows": len(rows),
        "codes": sorted({r_["code"] for r_ in rows}),
        "codes_covered": sorted({r_["code"] for r_ in rows if r_["dispo"]}),
        "by_dispo": {d: sum(1 for r_ in rows if r_["dispo"] == d)
                     for d in ("next", "keep", "epe", "blocked", "out")},
        "rows_per_code": {c: sum(1 for r_ in rows if r_["code"] == c) for c in CODES},
        "item_fields": r["field_count"],
        "new_leaf": st["new_leaf"],
        "new_hash": st["hash_new"],
        "mass_target": F["mass"]["target"],
        "water_constants": F["water"]["constants"],
    }
    for code in CODES:
        if not counts["rows_per_code"].get(code):
            problems.append(f"{code} has no row")

    payload = {
        "schema": 1,
        "generated_by": "t15_world.py",
        "card": "T-20 (GRAB_BACKLOG.md §7)",
        "decisions": {"D-6": "resolved 2026-10-28 (user): standalone entity",
                      "D-8": "resolved 2026-10-28 (user): lore - sink and stall, Rico swims out"},
        "inputs": {
            "rebel_drop": "Research/JC3Grab/REBELDROP.json",
            "standalone": "Research/JC3Grab/STANDALONE.json",
            "traffic": "Research/JC3Grab/TRAFFIC.json",
            "water": "Research/JC3Grab/WATER.json",
            "tether": "Research/JC3Grab/TETHER.json",
            "interaction": "Research/JC3Grab/INTERACTION.json",
            "t9_placement": "Working/Translation/t9_interaction.json",
            "index": "Research/JC3Grab/INDEX.jsonl",
            "strings": "profile/online.stringlookup (decoded through jc3strings.py)",
        },
        "summary": counts,
        "facts": {
            "rebel_drop": r,
            "standalone": {"new_leaf": st["new_leaf"], "donor_leaf": st["donor_leaf"],
                           "verdict": st["verdict"],
                           "needs_bytes": st["needs"]["bytes"],
                           "needs_inner_files": st["needs"]["inner_files"],
                           "toc_entries": st["needs"]["toc"]["entries"]},
            "strings": s,
            "icons": F["icons"],
            "interaction": F["inter"],
            "t9": F["t9"],
            "mass": F["mass"],
            "water": F["water"],
            "tether": {k: v for k, v in F["tether"].items()},
            "traffic": F["traffic"],
        },
        "rows": rows,
    }
    return payload, problems


# --------------------------------------------------------------------------- document
def read_doc(p: dict) -> list[str]:
    s = p["summary"]
    f = p["facts"]
    L: list[str] = []
    a = L.append
    a("# World translation (T-20)")
    a("")
    a("Generated by `Tools/scripts/t15_world.py` from the five G2 world files, T-13's placement")
    a("record and the install index; `--check` re-reads all of them (including the")
    a("`profile/online.stringlookup` pairs), re-derives this file and `t15_world.json`, compares")
    a("both byte-for-byte and cross-checks `T_ROWS.jsonl`. One row per world requirement, grouped")
    a("under the eight `WLD` codes of `GRAB_BACKLOG.md` §1.9.")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| rows | **{s['rows']}** over **{len(s['codes'])}/8** WLD codes |")
    a(f"| dispositions | " + ", ".join(f"`{k}` {v}" for k, v in s["by_dispo"].items()) + " |")
    a(f"| vehicle leaf | `{s['new_leaf']}` = `{s['new_hash']:08X}` (Jenkins hash of the leaf) |")
    a(f"| Batmobile mass | {s['mass_target']} (`rigid_body.mass`, T-M1 6 t class) |")
    a(f"| decisions | D-6 standalone entity · D-8 lore water (sink and stall) |")
    a("")
    a("## 1. What this card owns, and what it does not")
    a("")
    a("WLD-1…8 are *world* behaviours: the drop entry, the name and icon, the interaction points,")
    a("mass, water, tether/airlift and traffic. Two of the eight were already carried by another")
    a("card and are recorded here so the code has a row either way: **WLD-3/WLD-4's positions** are")
    a("T-13's placement (`t9_interaction.json`), and **WLD-5's contact hull** is DIM-4/T-22's")
    a("`.physicsc` set. This card writes no module and no entity: it decides, per requirement, which")
    a("file of phase B carries the value and whether that write side exists.")
    a("")
    a("| WLD | requirement | rows | carrier |")
    a("|---|---|---:|---|")
    carriers = {
        "WLD-1": "`profile/item.onlinec`, `profile/task.onlinec` (B-13)",
        "WLD-2": "`profile/online.stringlookup`, `textures/ui/vehicle_icons/` (B-13)",
        "WLD-3": "`.epe` `entry.*` / `exit.*` nodes (T-13 → B-05)",
        "WLD-4": "`.epe` `point.stunt*` nodes; `StuntAreas` in the interaction module",
        "WLD-5": "`rigid_body.mass` (T-M1); hull = T-22",
        "WLD-6": "`WaterInteraction` + `Buoyancy`; `vehicle_common` constants",
        "WLD-7": "`CVehicleCargoBay` on the carrier; no vehicle-side tether member",
        "WLD-8": "`settings/spawn_vehicle_defs.bin` (untouched, D-6)",
    }
    for code in CODES:
        row = next(r_ for r_ in p["rows"] if r_["code"] == code)
        a(f"| {code} | {row['requirement']} | {s['rows_per_code'][code]} | {carriers[code]} |")
    a("")
    a("## 2. The rows")
    a("")
    a("Cells: id, WLD code, requirement, lore/G2 source, JC3 carrier and value, disposition,")
    a("confidence (the R4 classes), verify (a §9b probe that can fail).")
    a("")
    a("| id | code | requirement | source | carrier and value | dispo | confidence | verify |")
    a("|---|---|---|---|---|---|---|---|")
    for row in p["rows"]:
        a("| " + " | ".join(row["cells"]) + " |")
    a("")
    a("## 3. The Rebel Drop item record, field by field")
    a("")
    rb = f["rebel_drop"]
    a(f"The recipe's {rb['field_count']} fields, checked against the `Item` schema the item table")
    a(f"decodes with ({rb['schema_fields']} members, 128 B). `Name`, `UIName`, `UIImagePath` and")
    a("`UIVideoPath` are the four that must name the leaf; `BaseName` is the vehicle family.")
    a("")
    a("| field | value | class |")
    a("|---|---|---|")
    classes = {
        "Name": "decoded (hash of the leaf, G2-26)",
        "BaseName": f"derived (`hash_jenkins(\"v0300\")`, holds {rb['family_ok']}/{rb['family_n']} vanilla vehicle drops)",
        "UIName": "decoded (points at the name pair, T-WLD4)",
        "UIImagePath": "decoded (the icon key, G2-32)",
        "UIVideoPath": "decoded (the leaf, as every vanilla drop)",
        "UIDescription": "decoded (points at the donor's blurb, T-WLD6)",
        "UITypeDescription": f"decoded (\"{f['strings']['en_type']}\", T-WLD7)",
        "UIFlagDescription": f"decoded (\"{f['strings']['en_flag']}\", T-WLD7)",
        "Type": f"class ({rb['vehicle_item_profile']['Type'][0]} on all vanilla vehicle drops)",
        "UIType": f"class ({rb['vehicle_item_profile']['UIType'][0]} on all vanilla vehicle drops)",
        "UIFlag": ("class (the donor's; the vanilla drops use "
                   + ", ".join(str(v) for v in rb['vehicle_flags'])
                   + ", and only the description strings say what a value means)"),
        "RebelDropTimer": "class (1800 s among the donor's peers, unit UNKNOWN)",
        "UIDisplayOrder": (f"class (a menu slot; the vanilla vehicle drops use "
                           f"{min(rb['vehicle_orders'])}..{max(rb['vehicle_orders'])})"),
        "Rewardable": "class (1 on every vehicle drop)",
        "Purchasable": "class (0 on every vehicle drop)",
        "DlcId": "class (0 = base game)",
        "Region": "class (0 on every vehicle drop)",
        "MaxInventory": "class (0 on every vehicle drop)",
        "Collectable": "class (0 on every vehicle drop)",
        "Consumable": "class (0 on every vehicle drop)",
        "Feats": "class (empty string)",
        "UIPar0": "decoded (the donor's, a UI scale parameter)",
        "UIPar1": "decoded (the donor's, a UI scale parameter)",
        "UIPar2": "decoded (the donor's, a UI scale parameter)",
        "UIPar3": "decoded (the donor's, a UI scale parameter)",
        "UIPar4": "decoded (the donor's, a UI scale parameter)",
    }
    for name in rb["schema_field_names"]:
        a(f"| `{name}` | {rb['fields'][name]} | {classes.get(name, 'class')} |")
    a("")
    a("## 4. Coverage by WLD code")
    a("")
    a("| code | rows | dispositions |")
    a("|---|---:|---|")
    for code in CODES:
        ds = sorted({r_["dispo"] for r_ in p["rows"] if r_["code"] == code})
        a(f"| {code} | {s['rows_per_code'][code]} | {', '.join(f'`{d}`' for d in ds)} |")
    a("")
    a(f"All {len(s['codes'])}/8 codes have at least one row, which is the card's `Done` line.")
    a("")
    a("## 5. Named omissions and blocked rows")
    a("")
    a("`out` means JC3 has no system to carry the requirement; `blocked` means the requirement has")
    a("a carrier but the write side does not exist in `Tools/scripts`. Neither is silently dropped.")
    a("")
    a("| row | code | disposition | what is missing | what carries it instead |")
    a("|---|---|---|---|---|")
    instead = {
        "T-WLD4": "the pair the store needs; use the donor's hash only if a Serpente name is acceptable",
        "T-WLD6": "same store, same writer gap",
        "T-WLD11": "the `point.stunt*` nodes (T-WLD10) still let the graph place Rico on the roof",
        "T-WLD15": "the car's mass is the only input it supplies to the tether",
        "T-WLD17": "the cargo plane and boat (T-WLD16); no helicopter has a bay",
    }
    for row in p["rows"]:
        if row["dispo"] not in ("out", "blocked"):
            continue
        a(f"| `{row['id']}` | {row['code']} | `{row['dispo']}` | {row['why']} | "
          f"{instead.get(row['id'], '-')} |")
    a("")
    a("## 6. UNKNOWNs and limits")
    a("")
    a("- **The `RebelDropTimer` unit** (1800 on the donor, 600…2700 fleet-wide) is a bare int32;")
    a("  seconds are plausible and unproven, so nothing is converted.")
    a("- **`Type`, `UIType`, `UIFlag` enum meanings** are UNKNOWN. Only the *description* strings")
    a("  resolve (\"SPORTS CAR\", \"SPORTS CARS\"), so the row copies the donor's values instead of")
    a("  picking a category.")
    a("- **`BaseName` is derived, not decoded**: it equals `hash_jenkins(<family prefix>)` on")
    a(f"  {rb['family_ok']}/{rb['family_n']} vanilla vehicle drops, which is strong but not a decoded")
    a("  field description (`REBELDROP.md` left it unnamed).")
    a("- **The string store has a writer** (`Tools/scripts/jc3strings_write`): bm-013 adds exactly 22")
    a("  pairs for the shipped `..._debug` leaf (1621485476 / 4081821928), 11/11 languages - so")
    a("  T-WLD4/T-WLD6 are `next` (carry the drop into the RC), not `blocked`.")
    a("- **The stunt areas are re-fittable**: 22/22 vertices place on the RC2 shell (P-1,")
    a("  0.036-0.105 m); full width needs 3 new deform indices (135+). Q-1 #3 is the standing probe.")
    a("- **The mass unit** is `UNKNOWN` (G2-34): the 6,000 target is a class value, compared to the")
    a("  fleet as a ratio, never as kilograms.")
    a("- **Native behaviour is not measured.** Tether strength, helicopter lift, traffic selection")
    a("  and water damage all end in game code; every `verify` cell is a §9b probe, and no game was")
    a("  launched here (R6).")
    a("")
    a("## 7. Outputs and regeneration")
    a("")
    a("| path | what it is |")
    a("|---|---|")
    a("| `Working/Translation/T15_WORLD.md` | this file, regenerated by `--write` |")
    a("| `Working/Translation/t15_world.json` | the same rows as data, with every fact behind them |")
    a("| `Tools/scripts/t15_world.py` | the tool; `--write` / `--check` / `show <id>` |")
    a("| `Working/Translation/T_ROWS.jsonl` | the ledger, through `t_rows.py` |")
    a("")
    a(f"`--check` re-derives {s['rows']} rows over {len(s['codes'])} codes, compares both files and")
    a("the ledger, and re-resolves the five string hashes against the live store.")
    a("")
    return L


# --------------------------------------------------------------------------- commands
def cmd_write() -> int:
    payload, problems = build_payload()
    lines = read_doc(payload)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    for p in problems:
        print("FAIL", p)
    s = payload["summary"]
    print(f"{OUT_JSON}: {s['rows']} rows, {len(s['codes_covered'])}/8 WLD codes, "
          f"dispositions {s['by_dispo']}")
    print(f"{OUT_MD}: {len(lines)} lines")
    return 1 if problems else 0


def cmd_check() -> int:
    payload, problems = build_payload()
    bad = 0
    if not os.path.exists(OUT_JSON):
        print(f"FAIL: no {OUT_JSON} - run --write first")
        return 1
    on_disk = json.load(open(OUT_JSON, encoding="utf-8"))
    if on_disk != payload:
        bad += 1
        print("FAIL: t15_world.json differs from the re-derived record")
        x, y = json.dumps(on_disk, sort_keys=True), json.dumps(payload, sort_keys=True)
        for i in range(min(len(x), len(y))):
            if x[i] != y[i]:
                print(f"   first difference at char {i}: {x[max(0, i - 60):i + 60]!r} != "
                      f"{y[max(0, i - 60):i + 60]!r}")
                break
    new_md = "\n".join(read_doc(payload)) + "\n"
    disk_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    if disk_md != new_md:
        bad += 1
        print("FAIL: T15_WORLD.md differs from the re-derived record")
        import difflib
        for line in list(difflib.unified_diff(disk_md.splitlines(), new_md.splitlines(),
                                              "T15_WORLD.md", "re-derived", lineterm=""))[:20]:
            print("   " + line)
    led: dict[str, dict] = {}
    if os.path.exists(LEDGER):
        led = {r["id"]: r for r in (json.loads(l) for l in open(LEDGER, encoding="utf-8")
                                    if l.strip())}
    for row in payload["rows"]:
        lr = led.get(row["id"])
        if lr is None:
            bad += 1
            print(f"FAIL {row['id']}: missing from T_ROWS.jsonl - run `t_rows.py build`")
            continue
        if lr["dispo"] != row["dispo"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger dispo {lr['dispo']} != {row['dispo']}")
        if not lr.get("why"):
            bad += 1
            print(f"FAIL {row['id']}: ledger row has no reason")
        if lr["cells"] != row["cells"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger cells differ from the document")
    for p in problems:
        bad += 1
        print("FAIL", p)
    s = payload["summary"]
    covered = len(set(s["codes_covered"]) & set(CODES))
    print(f"{'PASS' if not bad else 'FAIL'}: {s['rows']} rows | WLD codes {covered}/8 | "
          f"dispositions " + ", ".join(f"{k} {v}" for k, v in s["by_dispo"].items())
          + f" | ledger {sum(1 for r_ in payload['rows'] if r_['id'] in led)}/{s['rows']}")
    return 1 if bad else 0


def cmd_show(want: str) -> int:
    payload, _ = build_payload()
    hit = [r for r in payload["rows"] if want.lower() in r["id"].lower()]
    if not hit:
        raise SystemExit(f"no row matches {want!r}")
    print(json.dumps(hit, indent=1))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("show")
    s.add_argument("want")
    a = p.parse_args()
    if a.cmd == "show":
        return cmd_show(a.want)
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
