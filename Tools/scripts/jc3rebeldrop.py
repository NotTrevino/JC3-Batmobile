#!/usr/bin/env python
"""jc3rebeldrop.py - G2-26: the Rebel Drop tables (`profile/item.onlinec`, `task.onlinec`).

The card asks for three things:

  1. decode the mod's and the vanilla profile tables;
  2. document an entry's fields (entity path, name string hash, icon, category,
     cost/cooldown, unlock);
  3. diff mod vs vanilla to see exactly how a new entry is added -> a field-by-field
     recipe for an entry named "Batmobile" that spawns a given `.ee`.

Inputs, all read-only:

  * `profile/item.onlinec` and `profile/task.onlinec` from every archive layer that ships
    them (the patch layer is the effective one), extracted to
    `E:\\Modding\\_shared\\gamedata\\JC3grab\\rebeldrop\\` - game bytes stay outside the repo (R10);
  * the three variants of the Rebel Drop mod V5.3 in
    `Research/1456340180_Rebel-Drop-Mod-V5.3/`;
  * `Research/JC3Grab/INDEX.jsonl` to resolve an entry's name hash to an `.ee` path.

Two reader facts had to be established before any field could be trusted, and `--check`
re-derives both:

  * **the mod's tables carry no type dictionary** (`type_count` 0, a single name). Their
    schema can only be lent from the vanilla file; the mod's root hash `0x79DE48AE`
    stands for `ItemRoot` (`0x921AF417` in vanilla). With that, every item's hash fields
    equal a raw 32-bit read at the vanilla member offsets and the item stride is 128 B;
  * **`jc3adf.walk` reads a 4-byte `StringHash` as 8 bytes** (`StringHash_48C5294D_4`
    names element `0x48C5294D`, which is not a known primitive, so the reader falls
    through to `<Q`). Masking to 32 bits restores the value; that is checked against
    `struct.unpack_from("<I", ...)` for every hash field of every item.

The binding the recipe rests on: `Item.Name == rbmhdr.hash_jenkins(<entity leaf name>)`
(UIName equals Name, and vanilla vehicles also carry the same leaf in
UIImagePath/UIVideoPath). The index resolves that hash to exactly one `.ee` for 80/80
vanilla vehicle items and 45/45 mod-added items.

Usage:
  python jc3rebeldrop.py --write
  python jc3rebeldrop.py --check
  python jc3rebeldrop.py dump schema|items|tasks|added|recipe|counts
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
CACHE = os.path.join(RAW, "rebeldrop")
MOD_ROOT = os.path.join(ROOT, "Research", "1456340180_Rebel-Drop-Mod-V5.3")
MOD_VARIANTS = ("Regular v5.2", "V5.2 Plus", "V5.3 Plus")
JSON_NAME = "REBELDROP.json"
MD_NAME = "REBELDROP.md"
VAN_FILES = ("profile/item.onlinec", "profile/task.onlinec")

# The mod's item table has no type dictionary; its root hash is this. It decodes as
# `ItemRoot` because every field then lands on the vanilla offsets (proven, not guessed).
MOD_ITEM_ROOT = 0x79DE48AE
ITEM_ROOT = "ItemRoot"
TASK_ROOT = "TaskRoot"
BATMOBILE_LEAF = "v0300_car_kensington_sportsmuscle_batmobile"


# ------------------------------------------------------------------ decoding
def blob_of(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def open_adf(blob: bytes) -> jc3adf.Adf:
    return jc3adf.Adf(blob)


def schema(adf: jc3adf.Adf, struct_name: str) -> list[dict]:
    """Member list of one structure type, with resolved type names and sizes."""
    t = adf.types[adf.by_name[struct_name]]
    out = []
    for m in t["members"]:
        out.append({"name": m["name"], "type": adf.type_name(m["type"]),
                    "size": m["size"], "offset": m["offset"]})
    return out


def is_hash(field: dict) -> bool:
    return field["type"].startswith("StringHash")


def lend(mod: jc3adf.Adf, layers: list) -> dict:
    """Give a type-table-less file the layout of the layer whose root hash it declares.

    The base game's `Item` has 25 members (`Type` at 8, no `DlcId`); the patch's has 26
    (`DlcId` at 8, `Type` at 12).  A mod table carries no type table and declares the
    base root (`0x79DE48AE`), so it is read with the base layer's member list - not the
    patch's, which would name every int one slot late.  Both layouts are 128 B per item
    and agree on every member except `DlcId` (asserted by the base/patch diff).
    """
    meta = {"own_types": len(mod.types), "root_hash": mod.instances[0]["type"],
            "layout": "own" if mod.types else None,
            "layout_from": "own type table" if mod.types else None}
    if mod.types:
        return meta
    root = mod.instances[0]["type"]
    donor = next(((layer, adf) for layer, _path, _raw, adf in layers
                  if adf.instances[0]["type"] == root), None)
    if donor is None:
        raise SystemExit(f"no vanilla layer declares root {root:#010x}; cannot lend a layout")
    layer, adf = donor
    mod.types = dict(adf.types)
    mod.by_name = dict(adf.by_name)
    meta["layout"] = "lent"
    meta["layout_from"] = f"{layer} root {root:#010x}"
    return meta


def item_rows(adf: jc3adf.Adf, blob: bytes, fields: list[dict]) -> tuple[list[dict], dict]:
    """Decode every `Item` and verify each hash field against a raw 32-bit read."""
    rows = {p: v for p, _t, v in jc3adf.walk(adf)}
    arr_off, count = struct.unpack_from("<QQ", blob, adf.data_off)
    start = adf.data_off + arr_off
    stride = 128                       # vanilla `Item` size; proven by the checks below
    items, bad, string_bad = [], 0, 0
    img_off = next(f["offset"] for f in fields if f["name"] == "UIImagePath")
    for i in range(count):
        rec = {}
        for f in fields:
            v = rows.get(f"Items[{i}].{f['name']}")
            if is_hash(f) and isinstance(v, int):
                v &= 0xFFFFFFFF
                raw = struct.unpack_from("<I", blob, start + i * stride + f["offset"])[0]
                if raw != v:
                    bad += 1
            rec[f["name"]] = v
        # independent stride proof: the UIImagePath pointer (offset 88) must resolve
        # to a printable / empty NUL-terminated string for every record
        off, = struct.unpack_from("<Q", blob, start + i * stride + img_off)
        pos = adf.data_off + off
        end = blob.find(b"\x00", pos) if pos < len(blob) else -1
        s = blob[pos:end] if end > 0 else b"\xff"
        if end < 0 or not all(32 <= c < 127 for c in s):
            string_bad += 1
        items.append(rec)
    meta = {"objects": count, "stride": stride, "block_bytes": count * stride,
            "array_off": arr_off, "data_off": adf.data_off,
            "strings_start": start + count * stride,
            "hash_field_mismatches": bad, "string_pointer_failures": string_bad,
            "rows": len(rows)}
    return items, meta


def task_rows(adf: jc3adf.Adf) -> tuple[dict, list[dict]]:
    rows = {p: v for p, _t, v in jc3adf.walk(adf)}
    tasks = []
    i = 0
    while f"Tasks[{i}].Name" in rows:
        t = {"Name": (rows.get(f"Tasks[{i}].Name") or 0) & 0xFFFFFFFF,
             "TaskGroup": (rows.get(f"Tasks[{i}].TaskGroup") or 0) & 0xFFFFFFFF,
             "Type": rows.get(f"Tasks[{i}].Type"),
             "UIName": (rows.get(f"Tasks[{i}].UIName") or 0) & 0xFFFFFFFF,
             "UIOrderHint": rows.get(f"Tasks[{i}].UIOrderHint"),
             "rewards": [], "prerequisites": []}
        j = 0
        while f"Tasks[{i}].RewardThresholds[{j}].Threshold" in rows:
            k = 0
            while f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Item" in rows:
                t["rewards"].append({
                    "threshold": rows[f"Tasks[{i}].RewardThresholds[{j}].Threshold"],
                    "item": rows[f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Item"]
                    & 0xFFFFFFFF,
                    "permanent": rows[f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Permanent"],
                    "duration": rows[f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Duration"],
                    "quantity": rows[f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Quantity"],
                    "delivery": rows[f"Tasks[{i}].RewardThresholds[{j}].Reward.Items[{k}].Delivery"],
                })
                k += 1
            j += 1
        p = 0
        while f"Tasks[{i}].Prerequisites[{p}].Name" in rows:
            t["prerequisites"].append({
                "name": (rows[f"Tasks[{i}].Prerequisites[{p}].Name"] or 0) & 0xFFFFFFFF,
                "tag": (rows[f"Tasks[{i}].Prerequisites[{p}].Tag"] or 0) & 0xFFFFFFFF,
                "reward_index": rows[f"Tasks[{i}].Prerequisites[{p}].RewardIndex"]})
            p += 1
        tasks.append(t)
        i += 1
    return rows, tasks


# --------------------------------------------------------------------- index
def entity_index() -> dict[int, list[str]]:
    out: dict[int, list[str]] = collections.defaultdict(list)
    path = os.path.join(OUT, "INDEX.jsonl")
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            p = r["path"]
            if p.endswith(".ee"):
                out[hash_jenkins(p.rsplit("/", 1)[-1][:-3].encode())].append(p)
    return out


def mod_entities() -> dict[int, list[str]]:
    """Every `.ee` the mod itself ships, keyed by the Jenkins hash of its leaf."""
    out: dict[int, list[str]] = collections.defaultdict(list)
    for path in glob.glob(os.path.join(MOD_ROOT, "**", "*.ee"), recursive=True):
        leaf = os.path.basename(path)[:-3]
        out[hash_jenkins(leaf.encode())].append(
            os.path.relpath(path, ROOT).replace(os.sep, "/"))
    return {k: sorted(v) for k, v in out.items()}


def vanilla_files(rows: list[dict]) -> list[dict]:
    """Every archive layer that ships the two profile tables, highest layer last."""
    order = {"archives_win64": 0, "patch_win64": 1}
    out = []
    for path in VAN_FILES:
        hits = [r for r in rows if r.get("path") == path]
        hits.sort(key=lambda r: (order.get(r["archive"].split("/")[0], 9), r["archive"]))
        for r in hits:
            out.append(r)
    return out


def extract(rows: list[dict], entry: dict) -> tuple[str, bytes]:
    os.makedirs(CACHE, exist_ok=True)
    raw = jc3grab.read_entry(entry, GAME)
    tag = entry["archive"].replace("/", "_")
    dst = os.path.join(CACHE, tag + "__" + entry["path"].replace("/", "_"))
    with open(dst, "wb") as fh:
        fh.write(raw)
    return dst, raw


# --------------------------------------------------------------------- build
def build() -> dict:
    idx = jc3index.load_index(OUT)
    sources = []
    van = {}
    for entry in vanilla_files(idx):
        path, raw = extract(idx, entry)
        adf = open_adf(raw)
        sources.append({"kind": "vanilla", "layer": entry["archive"], "file": entry["path"],
                        "path": path, "bytes": len(raw),
                        "sha1": hashlib.sha1(raw).hexdigest()[:16]})
        van.setdefault(entry["path"], []).append((entry["archive"], path, raw, adf))
    if "profile/item.onlinec" not in van or "profile/task.onlinec" not in van:
        sys.exit("profile/item.onlinec or profile/task.onlinec missing from INDEX.jsonl")

    # the effective (highest) vanilla layer is the schema and the diff baseline
    van_item_layer, van_item_path, van_item_raw, van_item_adf = van["profile/item.onlinec"][-1]
    van_task_layer, van_task_path, van_task_raw, van_task_adf = van["profile/task.onlinec"][-1]
    item_fields = schema(van_item_adf, "Item")          # patch layer: 26 members
    base_layer0 = van["profile/item.onlinec"][0]
    base_fields = schema(base_layer0[3], "Item") if base_layer0[1] != van_item_path else None
    task_fields = schema(van_task_adf, "Task")
    reward_fields = schema(van_task_adf, "Reward")
    itemreward_fields = schema(van_task_adf, "ItemReward")
    prereq_fields = schema(van_task_adf, "Prerequisite")

    van_items, van_item_meta = item_rows(van_item_adf, van_item_raw, item_fields)
    van_task_rows, van_tasks = task_rows(van_task_adf)

    def items_of(path: str) -> tuple[list[dict], dict]:
        raw = blob_of(path)
        adf = open_adf(raw)
        meta = lend(adf, van["profile/item.onlinec"])
        fields = schema(adf, "Item")
        meta["members"] = len(fields)
        out, rows_meta = item_rows(adf, raw, fields)
        meta.update(rows_meta)
        return out, meta

    def tasks_of(path: str) -> tuple[list[dict], dict]:
        raw = blob_of(path)
        adf = open_adf(raw)
        meta = lend(adf, van["profile/task.onlinec"])
        rows_meta, out = task_rows(adf)
        meta.update({"objects": len(out), "rows": len(rows_meta)})
        return out, meta

    variants = {}
    for v in MOD_VARIANTS:
        ip = os.path.join(MOD_ROOT, v, "profile", "item.onlinec")
        tp = os.path.join(MOD_ROOT, v, "profile", "task.onlinec")
        items, imeta = items_of(ip) if os.path.exists(ip) else ([], {})
        tasks, tmeta = tasks_of(tp) if os.path.exists(tp) else ([], {})
        variants[v] = {
            "items": items, "item_meta": imeta,
            "tasks": tasks, "task_meta": tmeta,
            "item_sha1": hashlib.sha1(blob_of(ip)).hexdigest()[:16] if items else None,
            "task_sha1": hashlib.sha1(blob_of(tp)).hexdigest()[:16] if tasks else None,
            "item_bytes": len(blob_of(ip)) if items else 0,
            "task_bytes": len(blob_of(tp)) if tasks else 0,
        }

    # ---- the binding: Name == hash_jenkins(entity leaf)
    ee_by_hash = entity_index()

    def image_bound(items: list[dict]) -> int:
        return sum(1 for it in items
                   if (it.get("UIImagePath") or "")
                   and hash_jenkins(it["UIImagePath"].encode()) == it["Name"])

    van_image_bound = image_bound(van_items)
    for rec in variants.values():
        rec["image_bound"] = image_bound(rec["items"])

    def resolve(items: list[dict]) -> dict:
        hit = [it for it in items if it["Name"] in ee_by_hash]
        return {"items": len(items), "resolved": len(hit),
                "unresolved": [it["Name"] for it in items if it["Name"] not in ee_by_hash]}

    van_resolve = resolve(van_items)

    # ---- vanilla base vs patch: each layer is read with its own member list
    base = base_layer0 if base_layer0[1] != van_item_path else None
    base_diff = None
    base_meta = None
    if base and base_fields:
        base_meta = lend(base[3], van["profile/item.onlinec"])
        base_meta["members"] = len(base_fields)
        base_items, base_rows_meta = item_rows(base[3], base[2], base_fields)
        base_meta.update(base_rows_meta)
        by_name = {it["Name"]: it for it in base_items}
        pn = {it["Name"] for it in van_items}
        common = [f["name"] for f in item_fields if f["name"] in {g["name"] for g in base_fields}]
        five = ["Type", "Purchasable", "Consumable", "Rewardable", "Collectable"]
        changed_fields = collections.Counter()
        changed = matched = five_eq = 0
        for it in van_items:
            old = by_name.get(it["Name"])
            if old is None:
                continue
            matched += 1
            if all(old[f] == it[f] for f in five):
                five_eq += 1
            diff = [f for f in common if old[f] != it[f]]
            if diff:
                changed += 1
                for f in diff:
                    changed_fields[f] += 1
        base_diff = {"layer": base[0], "items": len(base_items),
                     "own_types": base_meta["own_types"],
                     "root_hash": base_meta["root_hash"],
                     "added": len(pn - set(by_name)),
                     "removed": len(set(by_name) - pn),
                     "matched": matched,
                     "five_int_equal": five_eq,
                     "common_fields": len(common),
                     "only_base": sorted({g["name"] for g in base_fields} - set(common)),
                     "only_patch": sorted({f["name"] for f in item_fields} - set(common)),
                     "changed": changed,
                     "changed_fields": dict(changed_fields.most_common())}

    # ---- mod vs vanilla (items and tasks)
    def diff_items(cur: list[dict], ref: list[dict]) -> dict:
        ref_by_name = {it["Name"]: it for it in ref}
        cur_names = {it["Name"] for it in cur}
        # two layouts: compare only the fields both files carry (the mods omit DlcId)
        common = [k for k in (cur[0] if cur else {}) if ref and k in ref[0]]
        added = [it for it in cur if it["Name"] not in ref_by_name]
        removed = [n for n in ref_by_name if n not in cur_names]
        changed_fields = collections.Counter()
        changed_items = 0
        for it in cur:
            old = ref_by_name.get(it["Name"])
            if old is None:
                continue
            d = [f for f in common if old[f] != it[f]]
            if d:
                changed_items += 1
                for f in d:
                    changed_fields[f] += 1
        return {"items_added": len(added), "items_removed": len(removed),
                "items_changed": changed_items,
                "changed_fields": dict(changed_fields.most_common()),
                "added": added}

    def diff_tasks(cur: list[dict], ref: list[dict]) -> dict:
        ref_by_name = {t["Name"]: t for t in ref}
        cur_names = {t["Name"] for t in cur}
        changed = sum(1 for t in cur
                      if ref_by_name.get(t["Name"]) is not None
                      and ref_by_name[t["Name"]] != t)
        ref_order = [t["Name"] for t in ref]
        cur_order = [t["Name"] for t in cur]
        return {"tasks_added": len(cur_names - set(ref_by_name)),
                "tasks_removed": len(set(ref_by_name) - cur_names),
                "tasks_changed": changed,
                "task_order_moved": sum(1 for a, b in zip(ref_order, cur_order) if a != b),
                "task_order_identical": ref_order == cur_order}

    base_items = base_tasks = None
    if base_diff:
        base_items, _bm = item_rows(base[3], base[2], base_fields)
        bt = van["profile/task.onlinec"][0]
        base_tasks, _tm = tasks_of(bt[1])
    for v, rec in variants.items():
        d_patch = diff_items(rec["items"], van_items)
        added = d_patch.pop("added")
        for it in added:
            it["_ee"] = ee_by_hash.get(it["Name"], [])
        d_patch.update(diff_tasks(rec["tasks"], van_tasks))
        rec["diff"] = d_patch
        if base_items is not None:
            d_base = diff_items(rec["items"], base_items)
            d_base.pop("added")
            d_base.update(diff_tasks(rec["tasks"], base_tasks))
            rec["diff_base"] = d_base
        rec["added"] = added
        rec["resolve"] = resolve(rec["items"])

    # ---- unlock: which items a task reward (or threshold reward) hands out
    def unlock_map(tasks: list[dict]) -> dict[int, list[dict]]:
        out: dict[int, list[dict]] = collections.defaultdict(list)
        for t in tasks:
            for r in t["rewards"]:
                out[r["item"]].append({"task": t["Name"], "task_type": t["Type"],
                                       "permanent": r["permanent"],
                                       "delivery": r["delivery"],
                                       "quantity": r["quantity"],
                                       "threshold": r["threshold"]})
        return out

    van_unlock = unlock_map(van_tasks)
    for v, rec in variants.items():
        rec["unlock"] = unlock_map(rec["tasks"])
        rec["added_with_unlock"] = sum(1 for it in rec["added"] if it["Name"] in rec["unlock"])

    # ---- the recipe
    donor = next((it for it in van_items
                  if it.get("UIImagePath") ==
                  "v0300_car_kensington_sportsmuscle_civilian_01"), None)
    if donor is None:
        sys.exit("donor sportsmuscle drop item not found in the vanilla table")
    bat_hash = hash_jenkins(BATMOBILE_LEAF.encode())
    recipe = {
        "leaf": BATMOBILE_LEAF,
        "ee_path": (ee_by_hash.get(bat_hash) or [None])[0],
        "existing_ee_named_that": bool(ee_by_hash.get(bat_hash)),
        "name_hash": bat_hash,
        "name_hash_hex": f"{bat_hash:08X}",
        "fields": dict(donor),
        "unlock": van_unlock.get(donor["Name"], []),
    }
    recipe["fields"].update({
        "Name": bat_hash, "UIName": bat_hash,
        "UIImagePath": BATMOBILE_LEAF, "UIVideoPath": BATMOBILE_LEAF,
    })
    # what the mod's own added entries look like (the pattern a working new entry has).
    # The added records carry the base 25-member layout, so use their own keys, not the
    # patch schema's (`DlcId` does not exist there).
    plus = variants.get("V5.3 Plus") or next(iter(variants.values()))
    if plus["added"]:
        # helper keys (`_ee`, `_mod_ee`) are bookkeeping, not members of the record
        added_fields = [k for k in plus["added"][0] if not k.startswith("_")]
        common = {}
        uniform = {}
        for name in added_fields:
            vals = collections.Counter(it[name] for it in plus["added"])
            common[name] = vals.most_common(1)[0][0]
            uniform[name] = vals[common[name]]
        recipe["mod_added_common"] = common
        recipe["mod_added_uniform"] = uniform
        recipe["mod_added_fields"] = added_fields
        recipe["mod_added_orders"] = sorted({it["UIDisplayOrder"] for it in plus["added"]})

    # the mod's own `.ee` files: which added entries name one, and which ship unnamed
    mod_ee = mod_entities()
    for rec in variants.values():
        for it in rec["added"]:
            it["_mod_ee"] = mod_ee.get(it["Name"], [])
    named_leaves = sorted({os.path.basename(v[0])[:-3] for h, v in mod_ee.items()
                           if any(it["Name"] == h for it in plus["added"])})
    unnamed_leaves = sorted({os.path.basename(v[0])[:-3] for h, v in mod_ee.items()
                             if not any(it["Name"] == h for it in plus["added"])})
    added_ui = collections.Counter(it["UIName"] for it in plus["added"])
    van_ui = {it["UIName"] for it in van_items}
    recipe["mod_added_uiname"] = {
        "added": len(plus["added"]),
        "uiname_differs": sum(1 for it in plus["added"] if it["UIName"] != it["Name"]),
        "shared_among_added": sum(v for v in added_ui.values() if v > 1),
        "groups": sorted(({"uiname": k, "items": v} for k, v in added_ui.items()
                          if v > 1), key=lambda r: (-r["items"], r["uiname"])),
        "vanilla_reuse": sum(1 for it in plus["added"]
                             if it["UIName"] in van_ui and it["UIName"] != it["Name"]),
    }

    vehicle_items = [it for it in van_items if it["Type"] == 1]
    vehicle_ui_tuples = len({tuple(it[f"UIPar{k}"] for k in range(5))
                             for it in vehicle_items})
    orders_all = sorted({it["UIDisplayOrder"] for it in van_items})
    base_name_sizes = collections.Counter(collections.Counter(
        it["BaseName"] for it in van_items).values())
    unresolved = [it for it in van_items if it["Name"] not in ee_by_hash]
    # a free menu slot for the recipe: one past the highest slot in the vanilla table
    recipe["donor_order"] = recipe["fields"]["UIDisplayOrder"]
    recipe["free_order"] = (max(orders_all) + 1) if orders_all else 0
    recipe["fields"]["UIDisplayOrder"] = recipe["free_order"]
    recipe["mod_named_items"] = sum(1 for it in plus["added"] if mod_ee.get(it["Name"]))
    recipe["mod_added_base_eq_name"] = sum(1 for it in plus["added"]
                                           if it["BaseName"] == it["Name"])
    totals = {
        "vanilla_layers": [s["layer"] for s in sources if s["kind"] == "vanilla"],
        "vanilla_items": len(van_items),
        "vanilla_tasks": len(van_tasks),
        "vanilla_vehicle_items": van_image_bound,
        "vanilla_items_resolved": van_resolve["resolved"],
        "vanilla_reward_links": sum(len(t["rewards"]) for t in van_tasks),
        "ee_paths": sum(len(v) for v in ee_by_hash.values()),
        "item_hash_mismatches": van_item_meta["hash_field_mismatches"],
        "vehicle_ui_tuples": vehicle_ui_tuples,
        "vanilla_orders": orders_all,
        "vanilla_vehicle_values": {
            f: sorted({it[f] for it in vehicle_items})
            for f in ("Type", "Purchasable", "Consumable", "Rewardable", "Collectable",
                      "Region", "MaxInventory", "UIType", "UIFlag", "RebelDropTimer",
                      "UIDisplayOrder")},
        "vanilla_vehicle_base_eq_name": sum(1 for it in vehicle_items
                                            if it["BaseName"] == it["Name"]),
        "vanilla_vehicle_name_eq_uiname": sum(1 for it in vehicle_items
                                              if it["UIName"] == it["Name"]),
        "vanilla_vehicle_distinct_images": len({it["UIImagePath"] for it in vehicle_items}),
        "vanilla_empty_image": sum(1 for it in van_items if it["UIImagePath"] in ("", None)),
        "vanilla_unresolved": len(unresolved),
        "vanilla_unresolved_uitypes": sorted({it["UIType"] for it in unresolved}),
        "vanilla_unresolved_empty_image": sum(1 for it in unresolved
                                              if it["UIImagePath"] in ("", None)),
        "vanilla_unresolved_placeholder": sum(1 for it in unresolved
                                              if it["UIImagePath"] == "placeholder"),
        "patch_dlc_zero": sum(1 for it in van_items if it.get("DlcId") == 0),
        "base_name_group_sizes": {str(k): v for k, v in sorted(base_name_sizes.items())},
        "mod_shipped_entities": len(mod_ee),
        "mod_shipped_named": len(named_leaves),
        # str keys: json turns int keys into strings, and --check compares the loaded
        # json against a fresh build (int 0 vs "0" would always look stale)
        "reward_values": {str(k): v for k, v in sorted(collections.Counter(
            r["delivery"] for t in van_tasks for r in t["rewards"]).items())},
        "vanilla_task_types": {str(k): v for k, v in sorted(collections.Counter(
            t["Type"] for t in van_tasks).items())},
    }

    # per-source object counts and the layout each file was read with (for §5)
    counts_by_file = {}
    if base:
        counts_by_file[(base[0], "profile/item.onlinec")] = len(base_items)
    counts_by_file[(van_item_layer, "profile/item.onlinec")] = len(van_items)
    if base_tasks is not None:
        counts_by_file[(van["profile/task.onlinec"][0][0], "profile/task.onlinec")] = len(base_tasks)
    counts_by_file[(van_task_layer, "profile/task.onlinec")] = len(van_tasks)
    for s in sources:
        s["objects"] = counts_by_file.get((s["layer"], s["file"]))
        if s["file"].endswith("item.onlinec"):
            n = len(base_fields) if base and s["layer"] == base[0] and base_fields \
                else len(item_fields)
            s["layout"] = f"own type table, {n} members"
        else:
            s["layout"] = "own type table"

    out = {
        "totals": totals,
        "sources": sources,
        "variants": {v: {k: rec[k] for k in
                         ("item_meta", "task_meta", "item_sha1", "task_sha1",
                          "item_bytes", "task_bytes", "image_bound", "diff",
                          "diff_base", "resolve", "added_with_unlock")
                         if k in rec}
                     for v, rec in variants.items()},
        "schema": {"Item": item_fields, "ItemBase": base_fields,
                   "roots": {"base": f"{base_layer0[3].instances[0]['type']:#010x}",
                             "patch": f"{van_item_adf.instances[0]['type']:#010x}",
                             "mod": f"{MOD_ITEM_ROOT:#010x}"},
                   "Task": task_fields, "Reward": reward_fields,
                   "ItemReward": itemreward_fields, "Prerequisite": prereq_fields},
        "mod_entities": {"files": len(mod_ee), "named": named_leaves,
                         "unnamed": unnamed_leaves},
        "vanilla": {"items": van_items, "tasks": van_tasks,
                    "item_meta": van_item_meta,
                    "base_diff": base_diff, "base_meta": base_meta,
                    "unlock": {str(k): v for k, v in sorted(van_unlock.items())}},
        "mod_added": {v: [{k: it[k] for k in ("Name", "BaseName", "UIName", "Type",
                                              "UIType", "UIFlag", "UIDisplayOrder",
                                              "RebelDropTimer", "UIImagePath", "_ee",
                                              "_mod_ee")
                            if k in it} for it in rec["added"]]
                      for v, rec in variants.items()},
        "recipe": recipe,
    }
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True, separators=(",", ":"))
                                 .encode()).hexdigest()[:16]
    return out


# ------------------------------------------------------------------------ md
def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, str) and v == "":
        return "`(empty)`"
    return str(v)


# Templates: every number is filled from the build (`notes`), never typed here (R11).
FIELD_NOTE = {
    "Name": "hash of the entity leaf name - this is the spawn binding (§4)",
    "BaseName": "a different hash; it takes {base_groups} distinct values over the {items} vanilla items, so it is a grouping key (what it names: UNKNOWN)",
    "DlcId": "{dlc_zero}/{items} records carry 0; this member exists only in the patch layout (the base/mod 25-member layout has no `DlcId`)",
    "Type": "`{type}` on all {veh} vanilla vehicle items and on the mod's {added} added entries; enum labels UNKNOWN",
    "Purchasable": "`{purch}` on all {veh} vanilla vehicle items; not a price (no price field exists)",
    "Consumable": "`{cons}` on all {veh} vanilla vehicle items and on the mod's added entries",
    "Rewardable": "`{rew}` on all {veh} vanilla vehicle items",
    "Collectable": "`{coll}` on all {veh} vanilla vehicle items",
    "Feats": "array of hashes, empty on the vehicle items",
    "Region": "`{region}` on all {veh} vanilla vehicle items",
    "RebelDropTimer": "the only time-like number: {timer} on vanilla vehicles, 0 on the mod's added entries; unit UNKNOWN (consistent with seconds)",
    "MaxInventory": "`{maxinv}` on all {veh} vanilla vehicle items",
    "UIType": "`{uitype}` on all {veh} vanilla vehicle items; enum labels UNKNOWN",
    "UIFlag": "{uiflag} on vanilla vehicles; enum labels UNKNOWN",
    "UIDisplayOrder": "menu order; {vorder} on vanilla vehicles ({aorder} over all items)",
    "UIName": "equal to `Name` on {name_eq_uiname}/{veh} vanilla vehicle items",
    "UIDescription": "localization key hash (string not in these files)",
    "UITypeDescription": "localization key hash, shared by items of one category",
    "UIFlagDescription": "localization key hash, one per `UIFlag` value",
    "UIImagePath": "string: the entity leaf name on vanilla vehicles, `placeholder` on the mod's new entries - cosmetic, not the binding",
    "UIVideoPath": "string: equal to `UIImagePath` on vanilla vehicles",
    "UIPar0": "float; one of five per-item numbers (the distinct-set count is in the text below); icon framing is the likely meaning and is UNKNOWN from the files",
}
for _k in ("UIPar1", "UIPar2", "UIPar3", "UIPar4"):
    FIELD_NOTE[_k] = "float; part of the same five-number set as `UIPar0`"

TASK_NOTE = {
    "Name": "task hash (string not in these files)",
    "TaskGroup": "task-group hash",
    "Type": "task type; the type histogram is in the text below, the enum labels are UNKNOWN",
    "ProvinceWeight": "weighting for province selection",
    "LiberationPercent": "liberation gate",
    "RepeatableRewardSemantics": "enum, UNKNOWN",
    "RepeatableReward": "a `Reward` handed out each repeat",
    "RewardThresholds": "`RewardThreshold[]`: threshold -> `Reward`",
    "Prerequisites": "`Prerequisite[]`: name + reward index + tag",
    "HasChurch": "flag",
    "ShownOnMap": "flag",
    "UIName": "localization key hash",
    "UIDescription": "localization key hash",
    "UITip": "localization key hash",
    "UIOrderHint": "sort key",
}


def render_md(d: dict) -> str:
    tot = d["totals"]
    van = d["vanilla"]
    recipe = d["recipe"]
    plus = d["variants"].get("V5.3 Plus") or next(iter(d["variants"].values()))
    b = van.get("base_diff") or {}
    roots = d["schema"]["roots"]
    ui = recipe["mod_added_uiname"]
    me = d["mod_entities"]
    mc = recipe["mod_added_common"]
    mu = recipe["mod_added_uniform"]
    vv = tot["vanilla_vehicle_values"]

    def span(field: str) -> str:
        vs = vv[field]
        if vs and all(isinstance(v, int) for v in vs) and vs == list(range(vs[0], vs[-1] + 1)):
            return str(vs[0]) if len(vs) == 1 else f"{vs[0]}..{vs[-1]}"
        return "/".join(str(v) for v in vs)

    notes = {f: span(f) for f in ("Type", "Purchasable", "Consumable", "Rewardable",
                                  "Collectable", "Region", "MaxInventory", "UIType",
                                  "UIFlag", "RebelDropTimer", "UIDisplayOrder")}
    notes.update({
        "type": span("Type"), "purch": span("Purchasable"), "cons": span("Consumable"),
        "rew": span("Rewardable"), "coll": span("Collectable"), "region": span("Region"),
        "maxinv": span("MaxInventory"), "uitype": span("UIType"),
        "uiflag": span("UIFlag"), "timer": span("RebelDropTimer"),
        "vorder": span("UIDisplayOrder"),
        "aorder": "/".join(str(v) for v in tot["vanilla_orders"]),
        "veh": tot["vanilla_vehicle_items"], "items": tot["vanilla_items"],
        "added": plus["diff"]["items_added"],
        "dlc_zero": tot["patch_dlc_zero"],
        "name_eq_uiname": tot["vanilla_vehicle_name_eq_uiname"],
        # number of distinct `BaseName` values = number of groups
        "base_groups": sum(tot["base_name_group_sizes"].values()),
    })
    # every record's `UIImagePath` pointer resolves (the stride proof) - counted, not typed
    proof_parts = []
    if van.get("base_meta"):
        n = van["base_meta"]["objects"]
        proof_parts.append(f"{n}/{n} base")
    n = van["item_meta"]["objects"]
    proof_parts.append(f"{n}/{n} patch")
    for v, rec in d["variants"].items():
        n = rec["item_meta"]["objects"]
        proof_parts.append(f"{n}/{n} mod {v}")
    stride_proof = ", ".join(proof_parts)
    L = [
        "# Rebel Drop - `profile/item.onlinec` and `profile/task.onlinec`",
        "",
        "G2-26. **A drop entry is an `Item` whose `Name` is the 32-bit Jenkins hash of an",
        "entity leaf name**, and the game spawns the `.ee` that hash names. Every field the card",
        "asks about is in the `Item` struct except the unlock, which lives in `task.onlinec` as a",
        "task reward. There is no entity-path field and no price field anywhere in either table.",
        "",
        f"- {tot['vanilla_items']} vanilla items and {tot['vanilla_tasks']} vanilla tasks from",
        f" {len(set(tot['vanilla_layers']))} archive layers ({', '.join(sorted(set(tot['vanilla_layers'])))}; the",
        " patch layer is the effective one);",
        f"- {tot['vanilla_vehicle_items']} of them are vehicle drops, and",
        f" {tot['vanilla_items_resolved']} of the {tot['vanilla_items']} name hashes resolve to an",
        f" `.ee` path in `INDEX.jsonl` ({tot['ee_paths']} entity paths) - the",
        f" {tot['vanilla_unresolved']} that do not name a shipped `.ee` (§4);",
        f"- the mod's newest variant adds {plus['diff']['items_added']} items and changes",
        f" {plus['diff']['items_changed']} of the vanilla ones; {plus['resolve']['resolved']} of",
        f" its {plus['resolve']['items']} items resolve to an `.ee` path (the same",
        f" {tot['vanilla_unresolved']} stay unresolved).",
        "",
        "## 1. What the two files are, and two reader facts",
        "",
        "Both are bare ADF v4 files (`20 46 44 41 04 00 00 00`): one root instance, an",
        "`A[Item]` / `A[Task]` array, and string data after it. Two facts had to be",
        "established before any value could be trusted, and `--check` re-derives both:",
        "",
        "1. **Base and patch are two layouts of the same 25 fields; the mods use the base",
        "   one.** The base game's own `profile/item.onlinec` declares five types and its",
        "   `Item` has **25** members (`Type` at 8, no `DlcId`); the patch layer",
        f"   (`patch_win64/game4`, root `{roots['patch']}`) has **26** (`DlcId` at 8, `Type` at",
        "   12). Both arrays are 128 B per item and the content is the same: the 25 common",
        f"   fields agree on {b.get('five_int_equal', '-')}/{b.get('matched', '-')} matched",
        f"   items and `DlcId` is 0 on {tot['patch_dlc_zero']}/{tot['vanilla_items']} records, so the"
        " patch adds the member and changes",
        "   no value. The mod tables carry no type table and declare the **base** root",
        f"   `{MOD_ITEM_ROOT:#010x}`, so they are read with the base 25-member layout, not the",
        "   patch's - the patch list names every int at 8..24 one slot late. Each file is read",
        "   with the layout it declares (its own type table, or the vanilla layer whose root",
        "   hash it carries), and §9 asserts that assignment. The 128 B stride is proved",
        "   without the type table: the `UIImagePath` pointer at offset 88 resolves to a",
        "   printable or empty NUL-terminated string for **every** record -",
        f"   {stride_proof} (§9).",
        "2. **`jc3adf.walk` reads a 4-byte `StringHash` as 8 bytes.** The type",
        "   `StringHash_48C5294D_4` declares element `0x48C5294D`, which is not a known",
        "   primitive, so the reader falls through to `<Q`. The low 32 bits are the true hash",
        "   (the high half is whatever the next member holds - e.g. `Region` reads",
        "   `2576980377600` = `600 << 32` because `RebelDropTimer` 600 follows it). Every hash",
        "   in this doc is masked to 32 bits and checked against",
        "   `struct.unpack_from(\"<I\", ...)` at the declared member offset.",
        "",
        "## 2. `Item` - the drop entry (26 members in the effective patch layout, 128 B)",
        "",
        "The table is the patch layer's 26-member `Item`. The base layer and the three mod",
        "tables carry the same list **without `DlcId`** (25 members); every other member keeps",
        "the offset printed here (§1).",
        "",
        "| field | type | size | offset | what the files prove |",
        "|---|---|---:|---:|---|",
    ]
    for f in d["schema"]["Item"]:
        L.append(f"| `{f['name']}` | {f['type']} | {f['size']} | {f['offset']} | "
                 f"{FIELD_NOTE.get(f['name'], 'UNKNOWN').format(**notes)} |")
    sizes = ", ".join(f"{n} x{v}" for n, v in tot["base_name_group_sizes"].items())
    L += [
        "",
        f"Every value list in that table is measured over the {tot['vanilla_vehicle_items']}",
        " vanilla vehicle drops (`--check` re-derives the counts). Their `UIImagePath` is a",
        f" distinct leaf on {tot['vanilla_vehicle_distinct_images']}/{tot['vanilla_vehicle_items']},",
        f" and the five `UIPar` numbers take {tot['vehicle_ui_tuples']} distinct values over the",
        f" {tot['vanilla_vehicle_items']}. `BaseName` is not per-item: its",
        f" {sum(tot['base_name_group_sizes'].values())} distinct values group the",
        f" {tot['vanilla_items']} items by size ({sizes}), and `Name != BaseName` on",
        f" {tot['vanilla_vehicle_items']}/{tot['vanilla_vehicle_items']} vehicles.",
        "",
        "**Cost: there is no cost field.** The only economic fields are the flags above; the",
        "only time is `RebelDropTimer`. If the game charges anything for a drop it is not in",
        "these files.",
        "",
        "## 3. `Task` - where the unlock is",
        "",
        "| field | type | size | offset | what the files prove |",
        "|---|---|---:|---:|---|",
    ]
    for f in d["schema"]["Task"]:
        L.append(f"| `{f['name']}` | {f['type']} | {f['size']} | {f['offset']} | "
                 f"{TASK_NOTE.get(f['name'], 'UNKNOWN')} |")
    L += [
        "",
        "`Reward` (`Skillpoints` int32, `Chaos` int32, `ItemRewardSemantics` int32,",
        "`Items` `A[ItemReward]`) and `ItemReward` (`Item` hash, `Permanent`, `Duration`,",
        "`Quantity`, `Delivery`) are the only place an item is granted; `Prerequisite` is",
        "`Name` + `RewardIndex` + `Tag`. The vanilla tables carry",
        f"{tot['vanilla_reward_links']} reward links, all with `Delivery` = 0",
        " (" + ", ".join(f"`{k}` x{v}" for k, v in tot["reward_values"].items())
        + f"), and {len(van['unlock'])} distinct items are handed out by",
        f"some task. Task `Type` histogram ({len(tot['vanilla_task_types'])} buckets,",
        f" {sum(tot['vanilla_task_types'].values())} tasks): " + ", ".join(
            f"{k} x{v}" for k, v in sorted(tot["vanilla_task_types"].items(),
                                           key=lambda kv: int(kv[0]))) + ".",
        "",
        "## 4. What the name hash names",
        "",
        "`Item.Name` is the Jenkins hash (the archive-path function, `rbmhdr.hash_jenkins`)",
        "of an **entity leaf name**, and that is the whole spawn binding:",
        "",
        "- independent check on the vanilla vehicles: `Name == hash(UIImagePath)` for",
        f" {tot['vanilla_vehicle_items']}/{tot['vanilla_vehicle_items']} items whose",
        " `UIImagePath` is a vehicle leaf;",
        f"- `Name` resolves to an `.ee` path for {tot['vanilla_items_resolved']}/",
        f"{tot['vanilla_items']} vanilla items and {plus['resolve']['resolved']}/",
        f"{plus['resolve']['items']} items of the mod's newest variant, against the",
        f" {tot['ee_paths']} entity paths in `INDEX.jsonl`. The {tot['vanilla_unresolved']}",
        " vanilla items that do not resolve carry `UIType` "
        + "/".join(str(v) for v in tot["vanilla_unresolved_uitypes"])
        + f" and an empty ({tot['vanilla_unresolved_empty_image']}) or `placeholder`"
        f" ({tot['vanilla_unresolved_placeholder']}) `UIImagePath`; what they are is UNKNOWN,",
        " and the mod keeps exactly those unresolved (`--check` asserts it);",
        f"- the mod proves the direction the other way: it ships {me['files']} `.ee` files of",
        f"  its own, and {recipe['mod_named_items']} of its added entries hash to one of those",
        "  leaves ("
        + ", ".join(f"`{n}`" for n in me["named"]) + "); the",
        f" {len(me['unnamed'])} shipped `.ee` leaves that no added entry names are "
        + ", ".join(f"`{n}`" for n in me["unnamed"]) + ".",
        "",
        "So the `.ee` path is **not** stored: the game looks the entity up by the hash of its",
        "leaf. Two entries cannot share a name hash, and the `.ee` must exist (or be shipped by",
        "the mod) under the **leaf** the hash was computed from.",
        "",
        "## 5. Sources",
        "",
        "| source | file | bytes | sha1 | items / tasks | note |",
        "|---|---|---:|---|---|---|",
    ]
    for s in d["sources"]:
        kind = "item" if s["file"].endswith("item.onlinec") else "task"
        n = s.get("objects")
        count = f"{n} {kind}{'' if n == 1 else 's'}" if n is not None else "-"
        L.append(f"| vanilla `{s['layer']}` | `{s['file']}` | {s['bytes']} | `{s['sha1']}` | "
                 f"{count} | {s.get('layout', 'own type table')}; extracted to "
                 f"`_JC3grab\\rebeldrop\\` |")
    for v, rec in d["variants"].items():
        L.append(f"| mod `{v}` | `profile/item.onlinec` | {rec['item_bytes']} | "
                 f"`{rec['item_sha1']}` | {rec['item_meta']['objects']} items | "
                 f"base layout ({rec['item_meta'].get('layout_from', '-')}) |")
        L.append(f"| mod `{v}` | `profile/task.onlinec` | {rec['task_bytes']} | "
                 f"`{rec['task_sha1']}` | {rec['task_meta']['objects']} tasks | "
                 f"base layout ({rec['task_meta'].get('layout_from', '-')}) |")
    if van.get("base_diff"):
        only = ", ".join(f"`{x}`" for x in b["only_patch"]) or "nothing"
        L += ["",
              f"Base game vs patch layer: {b['items']} -> {tot['vanilla_items']} items,",
              f"+{b['added']} / -{b['removed']} items, and {b['changed']} items whose value",
              f" changes in any of the {b['common_fields']} members the two layouts share",
              f" (the five ints at 8..24 agree on {b['five_int_equal']}/{b['matched']} matched",
              f" items). The patch adds one member, {only} (0 on {tot['patch_dlc_zero']}/"
              f"{tot['vanilla_items']}), and no other",
              " value differs. `--check` re-derives this diff."]
    L += [
        "",
        "## 6. How a new entry is added (mod vs vanilla)",
        "",
        "**Two baselines, because the mod tables use the base layout.** Base and patch carry",
        f"the same content: the patch only adds `DlcId` (0 on {tot['patch_dlc_zero']}/"
        f"{tot['vanilla_items']}), and every one of the",
        f" {b.get('common_fields', '-')} shared members is equal on {b.get('five_int_equal', '-')}",
        f" of {b.get('matched', '-')} matched items. The mod tables declare the base root and are",
        "read with the base 25-member layout, so their own edits are the diff against the base",
        "layer; the patch column is shown for completeness.",
        "",
        "| variant | items | added | removed | changed vs patch | changed vs base | fields it changes vs base (top) | tasks vs base |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for v, rec in d["variants"].items():
        df = rec["diff"]
        db = rec.get("diff_base", {})
        top = ", ".join(f"`{k}` {n}" for k, n in list(db.get("changed_fields", {}).items())[:4])
        L.append(f"| `{v}` | {rec['item_meta']['objects']} | {df['items_added']} | "
                 f"{df['items_removed']} | {df['items_changed']} | "
                 f"{db.get('items_changed', '-')} | {top} | "
                 f"{db.get('tasks_added', df['tasks_added'])} / "
                 f"{db.get('tasks_changed', df['tasks_changed'])} |")
    L += [
        "",
        "What the newest variant actually does:",
        "",
        f"- **adds {plus['diff']['items_added']} items** at the end of the array, all with",
        f"  `Type` {mc['Type']}, `UIType` {mc['UIType']}, `RebelDropTimer` {mc['RebelDropTimer']},",
        f"  `UIImagePath` = `{mc['UIImagePath']}`, `BaseName` = `Name`",
        f"  ({recipe['mod_added_base_eq_name']}/{plus['diff']['items_added']}; vanilla vehicle items:",
        f" {tot['vanilla_vehicle_base_eq_name']}/{tot['vanilla_vehicle_items']})",
        "  and an explicit `UIDisplayOrder` that continues the menu; their `Name` hashes name",
        "  the `.ee` they spawn, and",
        f"  {recipe['mod_named_items']} of the {plus['diff']['items_added']} hash to an `.ee`",
        "  the mod ships itself (§4);",
        f"- **rewrites {plus.get('diff_base', plus['diff'])['items_changed']} existing items**",
        "  (against the base layer); the fields it changes most are "
        + ", ".join(f"`{k}` {n}" for k, n in
                    list(plus.get('diff_base', plus['diff'])['changed_fields'].items())[:5])
        + ". That is consistent with exposing entries that were already in the table but",
        " hidden from the menu - an inference: the files do not label the fields;",
        f"- **{plus['diff']['tasks_added']} tasks added** and {plus['diff']['tasks_changed']}",
        "  tasks changed by name, but the task file is **reordered**:",
        f"  {plus['diff']['task_order_moved']} of {tot['vanilla_tasks']} positions hold a",
        "  different task than vanilla (that is the whole byte difference). None of its added",
        "  items appears in a task reward",
        f"  ({plus['added_with_unlock']} of {plus['diff']['items_added']} have an unlock). The",
        f"  added entries carry `Type` {mc['Type']}, `UIType` {mc['UIType']} and no reward; the",
        "  mod also rewrites `Type` on",
        f"  {plus.get('diff_base', plus['diff'])['changed_fields'].get('Type', 0)} existing items,",
        f"  and all its additions carry the same `Type {mc['Type']}` / `UIType {mc['UIType']}`"
        " pair.",
        "  Whether the absence of a task reward is what makes an entry available is UNKNOWN:",
        "  the mod is evidence of a working pattern, not of the rule.",
        "",
        "## 7. The recipe - an entry named \"Batmobile\" that spawns a given `.ee`",
        "",
        "1. **Pick the leaf name** of the entity to spawn. The entry binds by hash, so the",
        "   leaf must match the `.ee` exactly. For the Batmobile in the donor's chassis folder",
        "   this doc uses `" + recipe["leaf"] + "`.",
        "2. **Compute the 32-bit Jenkins hash** of that leaf - the same function as the",
        "   archive paths (`rbmhdr.hash_jenkins`; §9 re-runs the checks):",
        "",
        f"   `hash_jenkins(\"{recipe['leaf']}\")` = **{recipe['name_hash']}** =",
        f"   `0x{recipe['name_hash']:08X}`. That `.ee` is",
        f"   {'already in the index' if recipe['existing_ee_named_that'] else '**not** in the shipped index yet - the entity must be shipped as an archive override (`G2-27`)'}.",
        "",
        "3. **Add one `Item`** with these values (the row is the donor vehicle drop",
        "   `v0300_car_kensington_sportsmuscle_civilian_01` with the identity fields swapped):",
        "",
        "| field | value | why |",
        "|---|---|---|",
    ]
    veh = tot["vanilla_vehicle_items"]
    why = {
        "Name": "hash of the leaf (step 2) - the spawn binding",
        "UIName": f"same hash as `Name` ({tot['vanilla_vehicle_name_eq_uiname']}/{veh} vanilla vehicles)",
        "UIImagePath": "the leaf name (vanilla convention; `placeholder` also occurs in the mod)",
        "UIVideoPath": "the leaf name",
        "BaseName": "kept from the donor; its meaning is UNKNOWN",
        "Type": f"kept from the donor: {mc['Type']} is what all {veh} vanilla vehicle drops use",
        "UIType": f"{mc['UIType']} on all {veh} vanilla vehicle drops",
        "RebelDropTimer": (f"donor cooldown {recipe['fields']['RebelDropTimer']}; 0 if no cooldown "
                           "is wanted (the mod uses 0)"),
        "UIDisplayOrder": (f"one past the highest slot in the vanilla table "
                           f"({max(tot['vanilla_orders'])}), so a free slot; the donor's own "
                           f"value is {recipe['donor_order']} and the mod's added entries use "
                           f"{min(recipe['mod_added_orders'])}.."
                           f"{max(recipe['mod_added_orders'])}"),
        "DlcId": (f"{tot['patch_dlc_zero']}/{tot['vanilla_items']} vanilla records carry 0; only the "
                  "patch layout has this member - a base-root table omits it and every other "
                  "offset is unchanged"),
        "Purchasable": f"{notes['purch']} (all {veh} vanilla vehicle drops)",
        "Consumable": f"{notes['cons']} (all {veh} vanilla vehicle drops and the mod's added entries)",
        "Rewardable": f"{notes['rew']} (all {veh} vanilla vehicle drops)",
        "Collectable": f"{notes['coll']} (all {veh} vanilla vehicle drops)",
        "Region": f"{notes['region']} (all {veh} vanilla vehicle drops)",
        "MaxInventory": f"{notes['maxinv']} (all {veh} vanilla vehicle drops)",
        "Feats": f"empty array (all {veh} vanilla vehicle drops)",
        "UIFlag": (f"the donor's flag; {notes['uiflag']} occur on vanilla vehicles, "
                   "enum labels UNKNOWN"),
    }
    for f in d["schema"]["Item"]:
        name = f["name"]
        val = recipe["fields"][name]
        if name in ("UIPar0", "UIPar1", "UIPar2", "UIPar3", "UIPar4"):
            L.append(f"| `{name}` | {val:g} | donor icon parameter; the five are per-item |")
            continue
        shown = "(empty)" if val == "" else f"`{fmt(val)}`"
        L.append(f"| `{name}` | {shown} | "
                 + why.get(name, "the donor's localization key hash (string not in these files)")
                 + " |")
    L += [
        "",
        "4. **Keep the array valid**: append the item to `Items[]`, bump the array count, and",
        "   write the strings (`UIImagePath`, `UIVideoPath`) into the string area. In the two",
        "   mod tables the items sit back to back at 128 B each and the strings follow the",
        "   block - that is the layout `--check` verifies (`stride` 128, `strings_start` =",
        "   block end).",
        "5. **Optional unlock**: vanilla hands the donor drop out from a task reward. The",
        "   donor item's unlock rows are " + (
            "; ".join(f"task `{u['task']}` (type {u['task_type']}, permanent {u['permanent']}, "
                      f"delivery {u['delivery']}, quantity {u['quantity']})"
                      for u in recipe["unlock"]) or "absent (no task grants it)") +
        ". To gate the new entry the same way, add an `ItemReward` with `Item` = the hash,",
        "   `Permanent` 1, `Quantity` 1, `Delivery` 0 to a `Reward.Items[]` of a task; to make",
        f"   it available like the mod does, leave it out: its added entries carry `Type` {mc['Type']},",
        f"   `UIType` {mc['UIType']}, `RebelDropTimer` {mc['RebelDropTimer']} and no reward (measured).",
        "   Whether the missing reward is what makes them available is UNKNOWN (Q-1 probe).",
        "",
        f"`UIName` may also be shared: {ui['uiname_differs']} of the mod's {ui['added']} added",
        f" items set it to a hash other than `Name`, and {ui['shared_among_added']} of those share it",
        " with another added item ("
        + ", ".join(f"one hash covers {g['items']}" for g in ui["groups"])
        + f"), while {ui['vanilla_reuse']} reuse a `UIName` that a vanilla item also uses. So the",
        " field is a display-name key, not an identity. `Name` (and the `BaseName` the mod also",
        " sets to it) is the identity.",
        "",
        "The mod's own added entries look like this (most common value per field over its",
        f" {plus['diff']['items_added']} additions, `UIDisplayOrder` {min(recipe['mod_added_orders']) if recipe['mod_added_orders'] else '-'}.."
        f"{max(recipe['mod_added_orders']) if recipe['mod_added_orders'] else '-'}):",
        "",
        "| field | mod value |",
        "|---|---|",
    ]
    for f in d["schema"]["ItemBase"]:
        name = f["name"]
        if name == "Name":
            continue
        v = recipe["mod_added_common"].get(name)
        shown = "(empty)" if v == "" else f"`{fmt(v)}`"
        L.append(f"| `{name}` | {shown} |")
    L += [
        "",
        "The mod tables carry the base 25-member layout, so there is no `DlcId` row here;",
        "their records hold `Type`..`Collectable` at 8..24, i.e. the ordinary vanilla ints",
        f" (`Type` {mc['Type']} on all {mu['Type']} added entries). The patch layout inserts",
        "`DlcId` at 8 and moves those five by 4 B; the values are not 'mirrored' - the whole",
        "run shifts by one member.",
        "",
        "",
        "## 8. UNKNOWN",
        "",
        "- The **strings behind every hash** (`Name`, `BaseName`, `UIName`, `UIDescription`,",
        "  `UITypeDescription`, `UIFlagDescription`, task names/tips): only hashes are in these",
        "  files. Resolving them needs the string tables (G2-32). What `BaseName`, `Type`,",
        "  `UIType`, `UIFlag`, `DlcId` and `ItemReward.Delivery` *mean* is likewise UNKNOWN -",
        "  only their distributions are measured.",
        f"- The **`RebelDropTimer` unit**: the field name and the {notes['timer']} values",
        "  read as seconds, but nothing in the file states the unit.",
        "- **Which layout a type-table-less table is loaded with.** The mod ships the base root",
        f"  and its records read as ordinary base-layout entries (`Type` {mc['Type']}), so this"
        " doc uses the",
        "  base layout; nothing in the files says which member list the loader picks, and the",
        "  question matters to a writer even though base and patch values are identical.",
        "- Whether the absence of a task reward is what makes an entry available: the mod's",
        f"  added entries carry `Type` {mc['Type']}, `UIType` {mc['UIType']} and no reward, a"
        " working pattern, not a",
        "  decoded rule (Q-1 probe: one variable).",
        "- What `UIPar0..4` frame and whether `UIImagePath` must be a real icon for the menu",
        "  (the mod ships `placeholder`).",
        "- The exact array serialisation a *new* item must follow beyond stride 128 + string",
        "  area: both mod files were written by an external tool and this doc reproduces their",
        "  layout, not the game's writer.",
        "",
        "## 9. Validation and limits",
        "",
        "`jc3rebeldrop.py --check` re-extracts both vanilla layers, re-decodes the three mod",
        "variants with the layout each file declares, rebuilds `REBELDROP.json` and this file byte for",
        "byte and asserts:",
        "",
        f"- {tot['vanilla_items']} vanilla items / {tot['vanilla_tasks']} vanilla tasks;",
        f" {tot['vanilla_vehicle_items']} vehicle-bound items; {tot['vanilla_items_resolved']} of",
        f" {tot['vanilla_items']} items resolving to an `.ee` (the other"
        f" {tot['vanilla_unresolved']} name no shipped `.ee`)",
        " and the same 11 staying unresolved in every mod variant;",
        "- **the stride proof is the string pointer, not the hash read**: every `UIImagePath`",
        "  pointer resolves to a printable or empty NUL-terminated string for every record",
        f"  ({stride_proof}; 0 failures). The hash-field",
        "  check (0 mismatches) only proves the 32-bit masking, because it reads the same",
        "  offset it decodes;",
        "- **the layout assignment**: the base and patch files carry their own type tables (25",
        "  and 26 members), the mods carry none and their root hash selects the base layout; the",
        "  base/patch diff over the 25 common members is re-derived and the five ints at 8..24",
        "  must agree on every matched item;",
        "- the base table's type count (5) and root hash (`0x79DE48AE`), the mods' empty type",
        "  tables and their root, and the variant item/task counts, diffs, added-entry pattern",
        f"  (`BaseName` = `Name`, `Type` {mc['Type']}, `UIType` {mc['UIType']}, timer 0,"
        " `placeholder`) and the task reorder;",
        "- the recipe hash (`hash_jenkins(leaf)`) and the documented Jenkins checks.",
        "",
        "**Limits.** Only the two `profile` tables are read; how the game consumes an item",
        "(menu, pricing, delivery animation) is code. The `.ee` resolved from a name hash is a",
        "path in `INDEX.jsonl`, not proof the entity loads. Task strings and enums stay",
        "UNKNOWN. Nothing here is written into the game; the recipe produces a table edit for",
        "phases T/B, and shipping the entity itself is `G2-27`.",
        "",
    ]
    return "\n".join(L).rstrip() + "\n"


# ----------------------------------------------------------------- invariants
def invariants(d: dict) -> list[str]:
    bad = []
    tot = d["totals"]
    if tot["vanilla_items"] != 196 or tot["vanilla_tasks"] != 591:
        bad.append(f"vanilla objects {tot['vanilla_items']}/{tot['vanilla_tasks']}")
    if tot["vanilla_vehicle_items"] != 80 or tot["vanilla_items_resolved"] != 185:
        bad.append(f"vehicle-bound/resolved {tot['vanilla_vehicle_items']}/"
                   f"{tot['vanilla_items_resolved']}")
    if tot["item_hash_mismatches"] != 0:
        bad.append(f"{tot['item_hash_mismatches']} hash fields disagree with the raw read")
    if tot["vanilla_reward_links"] != 87:
        bad.append(f"vanilla reward links {tot['vanilla_reward_links']}")
    item_fields = [f["name"] for f in d["schema"]["Item"]]
    base_fields = [f["name"] for f in (d["schema"].get("ItemBase") or [])]
    if len(item_fields) != 26 or d["vanilla"]["item_meta"]["stride"] != 128:
        bad.append(f"Item schema {len(item_fields)} fields")
    if len(base_fields) != 25 or "DlcId" in base_fields:
        bad.append(f"base Item layout {len(base_fields)} members")
    if len(d["totals"].get("vanilla_task_types", {})) != 14 or \
            sum(d["totals"].get("vanilla_task_types", {}).values()) != d["totals"]["vanilla_tasks"]:
        bad.append("task Type histogram does not cover every task")
    expect = {"Regular v5.2": (232, 591, 39), "V5.2 Plus": (240, 591, 45),
              "V5.3 Plus": (240, 591, 45)}
    for v, (items, tasks, added) in expect.items():
        rec = d["variants"].get(v)
        if not rec:
            bad.append(f"variant {v} missing")
            continue
        if rec["item_meta"]["objects"] != items or rec["task_meta"]["objects"] != tasks:
            bad.append(f"{v} counts {rec['item_meta']['objects']}/{rec['task_meta']['objects']}")
        if rec["diff"]["items_added"] != added:
            bad.append(f"{v} added {rec['diff']['items_added']}")
        if rec["item_meta"].get("layout") != "lent":
            bad.append(f"{v} was not read with a lent layout")
        if rec["item_meta"].get("members") != len(base_fields):
            bad.append(f"{v} layout has {rec['item_meta'].get('members')} members, "
                       f"base has {len(base_fields)}")
        if rec["item_meta"].get("root_hash") != MOD_ITEM_ROOT:
            bad.append(f"{v} item root {rec['item_meta'].get('root_hash')}")
        if rec["resolve"]["resolved"] != items - 11:
            bad.append(f"{v} resolved {rec['resolve']['resolved']} of {items}")
    plus = d["variants"].get("V5.3 Plus", {})
    if plus and plus["diff"]["items_changed"] != 162:
        bad.append(f"V5.3 Plus changed {plus['diff']['items_changed']}")
    if tot.get("vanilla_unresolved") != tot["vanilla_items"] - tot["vanilla_items_resolved"]:
        bad.append("unresolved count inconsistent with resolved count")
    if plus and plus["diff"]["task_order_identical"]:
        bad.append("V5.3 Plus task order unexpectedly identical")
    bm = d["vanilla"].get("base_meta") or {}
    if bm.get("own_types") != 5 or bm.get("root_hash") != MOD_ITEM_ROOT:
        bad.append(f"base table types/root {bm.get('own_types')}/{bm.get('root_hash')}")
    if bm.get("layout") != "own" or bm.get("members") != 25:
        bad.append(f"base table layout {bm.get('layout')}/{bm.get('members')}")
    bdiff = d["vanilla"].get("base_diff") or {}
    if bdiff.get("common_fields") != 25 or bdiff.get("only_patch") != ["DlcId"] or \
            bdiff.get("only_base"):
        bad.append(f"base/patch layout members {bdiff.get('common_fields')}/"
                   f"{bdiff.get('only_base')}/{bdiff.get('only_patch')}")
    if bdiff.get("matched") != d["totals"]["vanilla_items"] or \
            bdiff.get("five_int_equal") != bdiff.get("matched"):
        bad.append(f"base/patch ints agree on {bdiff.get('five_int_equal')}/"
                   f"{bdiff.get('matched')}")
    if (d["vanilla"]["item_meta"].get("string_pointer_failures") or 0) != 0:
        bad.append("vanilla ImagePath pointers do not resolve")
    for v, rec in d["variants"].items():
        if (rec["item_meta"].get("string_pointer_failures") or 0) != 0:
            bad.append(f"{v} ImagePath pointers do not resolve")
    if plus and plus["added_with_unlock"] != 0:
        bad.append(f"V5.3 Plus added entries with a reward: {plus['added_with_unlock']}")
    added = d["mod_added"].get("V5.3 Plus", [])
    if len(added) != 45 or any(a["BaseName"] != a["Name"] for a in added):
        bad.append("added entries do not set BaseName = Name")
    if any(a["UIType"] != 3 or a["RebelDropTimer"] != 0 or a["UIImagePath"] != "placeholder"
           for a in added):
        bad.append("added entries do not share the documented pattern")
    if any(a.get("Type") != 1 or "DlcId" in a for a in added):
        bad.append("added entries are not base-layout Type 1")
    r = d["recipe"]
    if not tot["vanilla_orders"] or r["free_order"] in tot["vanilla_orders"]:
        bad.append("recipe display order is not a free slot")
    if r["fields"]["UIDisplayOrder"] != r["free_order"]:
        bad.append("recipe display order does not use the free slot")
    if r["name_hash"] != hash_jenkins(r["leaf"].encode()):
        bad.append("recipe hash does not re-derive")
    if hash_jenkins(b"v0300_car_kensington_sportsmuscle_civilian_01") != 3535039305:
        bad.append("jenkins check sportsmuscle")
    if hash_jenkins(b"v1704_boat_na_lightpatrol_civic_police_01") != 1244074668:
        bad.append("jenkins check new boat")
    if hash_jenkins(b"w141_rpg_uvk_13_mm110") != 2722878274:
        bad.append("jenkins check new weapon")
    if hash_jenkins(b"sponge") != 124127185:
        bad.append("jenkins check sponge")
    if r["fields"]["Name"] != r["name_hash"] or r["fields"]["UIImagePath"] != r["leaf"]:
        bad.append("recipe identity fields not swapped")
    donor = next((it for it in d["vanilla"]["items"]
                  if it["Name"] == 3535039305), None)
    if donor is None or donor["UIImagePath"] != "v0300_car_kensington_sportsmuscle_civilian_01":
        bad.append("donor item missing")
    if not d["vanilla"]["base_diff"]:
        bad.append("no base-vs-patch diff")
    return bad


def cmd_write() -> int:
    d = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(md)
    bad = invariants(d)
    print(f"{JSON_NAME}/{MD_NAME}: {d['totals']['vanilla_items']} vanilla items, "
          f"{d['totals']['vanilla_tasks']} tasks, {d['totals']['vanilla_vehicle_items']} "
          f"vehicle-bound, {len(d['variants'])} mod variants, {len(md.splitlines())} md lines"
          + (f", INVARIANTS: {'; '.join(bad)}" if bad else ""))
    return 1 if bad else 0


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
    tot = d["totals"]
    print(f"PASS: {tot['vanilla_items']} vanilla items / {tot['vanilla_tasks']} tasks / "
          f"{tot['vanilla_vehicle_items']} vehicle-bound / {tot['vanilla_items_resolved']} "
          f"resolved to .ee, 0 hash mismatches, "
          f"{'+'.join(str(v['diff']['items_added']) for v in d['variants'].values())} items "
          f"added by the 3 mod variants, recipe hash "
          f"{d['recipe']['name_hash']} for {d['recipe']['leaf']}")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    if what in ("schema", "counts", "recipe", "added", "totals", "variants"):
        sel = {"schema": d["schema"], "counts": d["totals"], "recipe": d["recipe"],
               "added": d["mod_added"], "totals": d["totals"],
               "variants": d["variants"]}[what]
        print(json.dumps(sel, indent=1, sort_keys=True, ensure_ascii=False)[:14000])
        return 0
    if what == "items":
        print(json.dumps(d["vanilla"]["items"][:3], indent=1, sort_keys=True))
        return 0
    if what == "tasks":
        print(json.dumps(d["vanilla"]["tasks"][:3], indent=1, sort_keys=True))
        return 0
    print("unknown section; use schema|items|tasks|added|recipe|counts|variants")
    return 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="counts")
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
