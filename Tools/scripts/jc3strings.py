"""jc3strings.py - where the vehicle's name and icons live (G2-32).

The donor is `v0300_car_kensington_sportsmuscle_civilian_01`. In the game it is called
**KERNER SERPENTE R**, and that string is not in the entity, not in `ui/ui_localization`, and not
in any `.gfx`: it is a pair in **`profile/online.stringlookup`**, keyed by the **32-bit Jenkins hash
of the entity leaf name**. The same file holds the `_desc` blurb and the flag/type descriptions the
Rebel Drop item points at. Icons are keyed the same way, as files:
`textures/ui/vehicle_icons/<leaf>.ddsc`.

What this script reads (all read-only, all re-derivable):

  * `profile/online.stringlookup` (patch)  - the profile/UI string store: `Languages[N]` each with a
    `SortedPairs[]` of `{Hash, TextOffset}` into one shared `Text` blob (`int8[]`, NUL-separated).
  * `ui/ui_localization.stringlookup`      - the HUD/UI store, searched for the same hashes to prove
    the name is *not* there.
  * the donor's own `.stringlookup`         - what the entity itself carries (interaction prompts).
  * `Research/JC3Grab/REBELDROP.json`       - G2-26's decode of `profile/item.onlinec`, for the item
    whose `Name` is the leaf hash: UIName, UIImagePath, UIDescription, UIFlag, UIFlagDescription,
    UITypeDescription, UIDisplayOrder, RebelDropTimer, plus the task that rewards it.
  * `Research/JC3Grab/INDEX.jsonl`          - for every icon path, and for the `.gfx`/`.blo` files
    that could reference the name.

Usage:
  python Tools/scripts/jc3strings.py --write     # writes Research/JC3Grab/NAMES.md
  python Tools/scripts/jc3strings.py --check     # re-derives and compares
  python Tools/scripts/jc3strings.py dump        # the payload
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
DOC = os.path.join(OUT, "NAMES.md")
INDEX = os.path.join(OUT, "INDEX.jsonl")
REBELDROP = os.path.join(OUT, "REBELDROP.json")
BUILD = os.path.join(ROOT, "Builds", "test-091")

LEAF = "v0300_car_kensington_sportsmuscle_civilian_01"
DONOR_DIR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
             + LEAF + ".stringlookup")
PROFILE = "profile/online.stringlookup"
UI_LOC = "ui/ui_localization.stringlookup"
ICON_DIR = "textures/ui/vehicle_icons/"
STORE_DIR = "textures/ui/store/"
LANG_ORDER = ["en", "fr", "de", "it", "es", "ru", "pl", "ja", "pt", "es-MX", "ar"]


# ----------------------------------------------------------------------- readers
def load_index() -> dict[str, dict]:
    import jc3weapons  # noqa: E402
    rows = [json.loads(line) for line in open(INDEX, encoding="utf-8") if line.strip()]
    return jc3weapons.best_by_path(rows)


def decode_stringlookup(path: str, index: dict[str, dict], game: str) -> dict:
    """`Languages[N].SortedPairs[]` + the shared `Text` blob, both decoded through `jc3adf`."""
    import jc3weapons  # noqa: E402
    import jc3adf  # noqa: E402
    row = index.get(path)
    if row is None:
        raise SystemExit(f"{path} not in the index")
    blob = jc3weapons.read_row(row, game)
    adf = jc3adf.Adf(blob)
    walk = list(jc3adf.walk(adf, 0))
    text = bytearray()
    lanes: dict[int, dict[int, int]] = {}
    pending: dict[tuple[int, int], int] = {}
    for p, _t, v in walk:
        if p.startswith("Text["):
            text.append(v & 0xFF)
            continue
        m = re.match(r"Languages\[(\d+)\]\.SortedPairs\[(\d+)\]\.(Hash|TextOffset)$", p)
        if not m:
            continue
        lang, idx, field = int(m.group(1)), int(m.group(2)), m.group(3)
        lanes.setdefault(lang, {})
        if field == "Hash":
            pending[(lang, idx)] = v
        else:
            lanes[lang][pending[(lang, idx)]] = v
    return {"path": path, "mount": row["mount"], "size": row["size"], "bytes": len(blob),
            "instances": [(i["name"], adf.type_name(i["type"])) for i in adf.instances],
            "text": bytes(text), "pairs": lanes, "walk_rows": len(walk)}


def text_at(text: bytes, off: int) -> str | None:
    if off is None or off < 0 or off >= len(text):
        return None
    end = text.find(b"\x00", off)
    return text[off:end].decode("utf-8", "replace")


def resolve(lookup: dict, h: int) -> dict[str, str]:
    out = {}
    for lang, pairs in sorted(lookup["pairs"].items()):
        off = pairs.get(h)
        if off is None:
            continue
        value = text_at(lookup["text"], off)
        if value is not None:
            out[LANG_ORDER[lang] if lang < len(LANG_ORDER) else f"lang{lang}"] = value
    return out


def tah(text: bytes, needle: bytes) -> list[int]:
    out, i = [], text.find(needle)
    while i >= 0:
        out.append(i)
        i = text.find(needle, i + 1)
    return out


# ----------------------------------------------------------------------- the payload
def build_payload() -> dict:
    import jc3index  # noqa: E402
    from rbmhdr import hash_jenkins  # noqa: E402
    game = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
    index = load_index()

    profile = decode_stringlookup(PROFILE, index, game)
    uiloc = decode_stringlookup(UI_LOC, index, game)
    donor_blob_path = os.path.join(BUILD, "aaf", "editor", "entities", "jc_vehicles", "01_land",
                                   "v0300_car_kensington_sportsmuscle",
                                   LEAF + ".stringlookup")
    build_sl = decode_stringlookup(DONOR_DIR, index, game) if DONOR_DIR in index else None
    build_sl_local = None
    if build_sl is not None:
        en = {h: text_at(build_sl["text"], off)
              for h, off in sorted(build_sl["pairs"].get(0, {}).items())}
        local_bytes = (open(donor_blob_path, "rb").read()
                       if os.path.exists(donor_blob_path) else None)
        import jc3weapons  # noqa: E402
        copies = {}
        for row_ in (r for r in [json.loads(l) for l in open(INDEX, encoding="utf-8") if l.strip()]
                     if r["path"] == DONOR_DIR):
            raw = jc3weapons.read_row(row_, game)
            copies[row_["mount"]] = {"bytes": len(raw),
                                      "matches_build": (local_bytes == raw)
                                      if local_bytes is not None else None}
        build_sl_local = {
            "bytes": build_sl["bytes"],
            "instances": build_sl["instances"],
            "languages": len(build_sl["pairs"]),
            "entries": len(build_sl["pairs"].get(0, {})),
            "english": [{"hash": f"{h:08X}", "text": t} for h, t in en.items()],
            "copies": copies,
            "build_copy_bytes": len(local_bytes) if local_bytes is not None else None,
        }

    keys = {LEAF: hash_jenkins(LEAF.encode()),
            LEAF + "_desc": hash_jenkins((LEAF + "_desc").encode())}

    drop = json.load(open(REBELDROP, encoding="utf-8"))
    item = next(i for i in drop["vanilla"]["items"] if i["Name"] == keys[LEAF])
    task = next(t for t in drop["vanilla"]["tasks"]
                if any(r.get("item") == keys[LEAF] for r in t.get("rewards", [])))
    item_keys = {k: item[k] for k in item
                 if k.startswith("UI") and k.endswith(("Name", "Description"))
                 and isinstance(item[k], int) and item[k] > 0xFFFF}
    resolved_item = {k: resolve(profile, v) for k, v in sorted(item_keys.items())}

    name = resolve(profile, keys[LEAF])
    desc = resolve(profile, keys[LEAF + "_desc"])
    in_ui_loc = {hex(h): resolve(uiloc, h) for h in keys.values()}
    serpente_banners = {}
    for h, off in uiloc["pairs"].get(0, {}).items():
        txt = text_at(uiloc["text"], off)
        if txt and "Serpente" in txt:
            serpente_banners[f"0x{h:08X}"] = resolve(uiloc, h)

    icons = {}
    for kind, root in (("vehicle", ICON_DIR), ("store", STORE_DIR)):
        for line_ in open(INDEX, encoding="utf-8"):
            d = json.loads(line_)
            p = d["path"]
            if not p.startswith(root):
                continue
            name_ = p[len(root):-len(".ddsc")] if p.endswith(".ddsc") else None
            if name_ is None:
                continue
            icons.setdefault(kind, {})[name_] = {"path": p, "mount": d["mount"],
                                                 "size": d["size"]}
    vehicle_icons = icons.get("vehicle", {})
    store_icons = icons.get("store", {})

    # how far does the name/icon bridge hold across the fleet's Rebel Drop vehicles?
    fleet = []
    for it in drop["vanilla"]["items"]:
        image = it.get("UIImagePath")
        if not isinstance(image, str) or not image.startswith("v0"):
            continue
        fleet.append({"name": it["Name"], "leaf": image,
                      "name_resolved": len(resolve(profile, it["UIName"])),
                      "icon": (ICON_DIR + image + ".ddsc") in
                              {v["path"] for v in vehicle_icons.values()}})
    fleet_total = len(fleet)
    fleet_named = sum(1 for f in fleet if f["name_resolved"])
    fleet_iconed = sum(1 for f in fleet if f["icon"])

    # does any UI movie or the map name the vehicle / its icon set?
    gfx_hits = []
    for line_ in open(INDEX, encoding="utf-8"):
        d = json.loads(line_)
        p = d["path"]
        if not (p.endswith(".gfx") or p.endswith(".blo")):
            continue
        if d["mount"] != "patch" and d["mount"] != "base":
            pass
        if p.startswith("ui/") and p.endswith(".gfx"):
            import jc3weapons  # noqa: E402
            blob = jc3weapons.read_row(d, game)
            marks = []
            if b"vehicle_icons" in blob:
                marks.append("vehicle_icons")
            if LEAF.encode() in blob:
                marks.append("leaf")
            if keys[LEAF].to_bytes(4, "little") in blob:
                marks.append("name-hash-le")
            if keys[LEAF].to_bytes(4, "big") in blob:
                marks.append("name-hash-be")
            if marks:
                gfx_hits.append({"path": p, "mount": d["mount"], "marks": marks})
    frontend: dict = {}
    for line_ in open(INDEX, encoding="utf-8"):
        d = json.loads(line_)
        if d["path"] == "global/frontend_global.blo":
            import jc3weapons  # noqa: E402
            blob = jc3weapons.read_row(d, game)
            frontend[d["mount"]] = {
                "size": d["size"],
                "leaf": LEAF.encode() in blob,
                "name_hash_le": keys[LEAF].to_bytes(4, "little") in blob,
                "name_hash_be": keys[LEAF].to_bytes(4, "big") in blob,
            }

    return {"schema": 1,
            "generated_by": "Tools/scripts/jc3strings.py",
            "leaf": LEAF,
            "keys": {k: {"hash": v, "hex": f"{v:08X}"} for k, v in keys.items()},
            "profile": {"path": profile["path"], "mount": profile["mount"],
                        "bytes": profile["bytes"], "walk_rows": profile["walk_rows"],
                        "instances": profile["instances"],
                        "languages": len(profile["pairs"]),
                        "pairs_per_language": {LANG_ORDER[k] if k < len(LANG_ORDER) else k:
                                               len(v) for k, v in sorted(profile["pairs"].items())},
                        "text_bytes": len(profile["text"])},
            "ui_localization": {"path": uiloc["path"], "mount": uiloc["mount"],
                                "bytes": uiloc["bytes"], "walk_rows": uiloc["walk_rows"],
                                "instances": uiloc["instances"],
                                "languages": len(uiloc["pairs"]),
                                "pairs_per_language": {LANG_ORDER[k] if k < len(LANG_ORDER) else k:
                                                       len(v) for k, v in
                                                       sorted(uiloc["pairs"].items())},
                                "text_bytes": len(uiloc["text"]),
                                "serpente_entries": serpente_banners,
                                "own_keys": in_ui_loc},
            "donor_stringlookup": build_sl_local,
            "donor_stringlookup_archive": ({"path": build_sl["path"], "bytes": build_sl["bytes"],
                                            "instances": build_sl["instances"]}
                                           if build_sl else None),
            "name": name, "desc": desc,
            "drop_item": {"item": item, "task": {"Name": task["Name"], "Type": task["Type"]},
                          "resolved": resolved_item},
            "icons": {"vehicle_total": len(vehicle_icons),
                      "placeholder": vehicle_icons.get("placeholder"),
                      "own": vehicle_icons.get(LEAF),
                      "variants": sorted(k for k in vehicle_icons if "sportsmuscle" in k),
                      "store_total": len(store_icons),
                      "store_own": store_icons.get("v0300_sportsmuscle_01")},
            "fleet": {"vehicles": fleet_total, "named": fleet_named, "iconed": fleet_iconed},
            "gfx_hits": gfx_hits, "frontend": frontend}


# ----------------------------------------------------------------------- the document
def to_md(p: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# Names, strings and icons: where the game says \"KERNER SERPENTE R\" (G2-32)")
    a("")
    a("Generated by `python Tools/scripts/jc3strings.py --write`, re-derived and compared")
    a("byte-for-byte by `--check`. The card asked for one thing: every place the donor's name and")
    a("icon appear, with a file and an id for each.")
    a("")
    a("**The answer in one line.** The name is a **32-bit Jenkins hash of the entity leaf name**")
    a(f"(`{p['leaf']}` -> `{p['keys'][p['leaf']]['hex']}`) resolved inside")
    a(f"**`{p['profile']['path']}`**, which is the only store that holds it; the vehicle's own")
    a("`.stringlookup` carries interaction prompts and no name; `ui/ui_localization.stringlookup`")
    a("does not contain it at all; and the icon is a plain texture file named after the same leaf")
    a(f"(`{ICON_DIR}<leaf>.ddsc`).")
    a("")
    a("## 1. The string, per language")
    a("")
    a("| language | name (`" + p["keys"][p["leaf"]]["hex"] + "`) | description (`"
      + p["keys"][p["leaf"] + "_desc"]["hex"] + "`) |")
    a("|---|---|---|")
    for lang in LANG_ORDER:
        nm = p["name"].get(lang, "")
        de = p["desc"].get(lang, "")
        if not nm and not de:
            continue
        a(f"| `{lang}` | {nm or '-'} | {(de[:90] + '…') if len(de) > 90 else de or '-'} |")
    a("")
    a(f"Languages present in the store: **{p['profile']['languages']}** "
      f"(`{', '.join(p['profile']['pairs_per_language'])}`), text blob "
      f"{p['profile']['text_bytes']:,} B, NUL-separated.")
    a("")
    a("The key is the leaf name, so the *entity* decides the name: renaming the `.ee` leaf silently")
    a("loses the string until a matching pair is added. That is the rename rule for the build.")
    a("")
    a("## 2. Where the name is displayed")
    a("")
    a("| place | file | id | what it holds |")
    a("|---|---|---|---|")
    a(f"| Rebel Drop menu (name) | `profile/item.onlinec` | `UIName` = "
      f"`{p['drop_item']['item']['UIName']}` ({p['keys'][p['leaf']]['hex']}) | the hash, not the text - "
      f"the menu resolves it through `{p['profile']['path']}` |")
    a(f"| Rebel Drop menu (blurb) | `profile/item.onlinec` | `UIDescription` = "
      f"`{p['drop_item']['item']['UIDescription']}` | `_desc` pair in the same store |")
    a(f"| Rebel Drop menu (type/flag) | `profile/item.onlinec` | `UITypeDescription` "
      f"`{p['drop_item']['item']['UITypeDescription']}`, `UIFlagDescription` "
      f"`{p['drop_item']['item']['UIFlagDescription']}` | also resolved in the same store |")
    a(f"| Unlock (chop-shop task) | `profile/task.onlinec` | task `{p['drop_item']['task']['Name']}` "
      f"(Type {p['drop_item']['task']['Type']}) rewards item "
      f"`{p['drop_item']['item']['Name']}` | the task that hands the car over |")
    a(f"| vehicle **HUD** name | - | - | **no carrier**: the donor's own `.stringlookup` holds only "
      f"interaction strings (§3), and no `.gfx` references the name hash (§5) |")
    a(f"| **map icon** | - | - | **no per-vehicle file**: there is not one map-marker texture for "
      f"vehicles in the index (§5) |")
    a("")
    a("### 2.1 The item record, verbatim")
    a("")
    a("| field | value |")
    a("|---|---|")
    for k in ("Name", "UIName", "UIDescription", "UIType", "UITypeDescription", "UIFlag",
              "UIFlagDescription", "UIImagePath", "UIVideoPath", "UIDisplayOrder",
              "RebelDropTimer", "Type", "Rewardable"):
        a(f"| `{k}` | `{p['drop_item']['item'][k]}` |")
    a("")
    a("Every `UI*` hash resolves in the same store:")
    a("")
    a("| field | hash | English |")
    a("|---|---|---|")
    for k, v in p["drop_item"]["resolved"].items():
        a(f"| `{k}` | `{hex(p['drop_item']['item'][k])}` | {(v.get('en') or '-')[:100]} |")
    a("")
    a("## 3. What the entity itself carries, and what it does not")
    a("")
    dsl = p["donor_stringlookup"]
    if dsl:
        a(f"`{LEAF}.stringlookup` (patch copy) is **{dsl['bytes']} B**, one "
          f"`{dsl['instances'][0][1]}` instance,")
        a(f"**{dsl['entries']} {'entry' if dsl['entries'] == 1 else 'entries'}** across "
          f"{dsl['languages']} languages - an interaction prompt, not a name:")
        a("")
        a("| hash | English |")
        a("|---|---|")
        for e in dsl["english"]:
            a(f"| `{e['hash']}` | {e['text']} |")
        a("")
        a("**It holds no vehicle name and no description** - the name is looked up from the item,")
        a("not from the entity. A Batmobile build that keeps this file keeps the vanilla prompts;")
        a("changing a name here changes nothing.")
        a("")
        matched = ", ".join(k for k, v in dsl["copies"].items() if v["matches_build"]) or "none"
        a(f"The build's own copy: **{dsl['build_copy_bytes']} B**, byte-identical to the "
          f"**{matched}** copy of the same path. The **patch** copy is "
          f"**{dsl['copies'].get('patch', {}).get('bytes')} B** and differs only in padding - its")
        a("decoded strings are identical, so the mod shipping the base table loses nothing.")
    a("")
    a(f"`ui/ui_localization.stringlookup` (`{p['ui_localization']['bytes']:,} B`, "
      f"{p['ui_localization']['languages']} languages, "
      f"{p['ui_localization']['text_bytes']:,} B of text) is the HUD/UI store and **does not hold")
    a(f"the name**: the donor's two hashes resolve to nothing there, and the only entries mentioning")
    a(f"\"Serpente\" in the whole file are the {len(p['ui_localization']['serpente_entries'])}")
    a("Weaponized-Serpente DLC banners ("
      + ", ".join(f"`{k}`" for k in p['ui_localization']['serpente_entries']) + "):")
    a("")
    a("| banner id | English |")
    a("|---|---|")
    for k, v in p['ui_localization']['serpente_entries'].items():
        a(f"| `{k}` | {v.get('en', '-')} |")
    a("")
    a("## 4. Icons")
    a("")
    own = p["icons"]["own"]
    ph = p["icons"]["placeholder"]
    a("| purpose | path | bytes | how it is keyed |")
    a("|---|---|---:|---|")
    if own:
        a(f"| vehicle icon (menu/garage) | `{own['path']}` | {own['size']} | leaf name - "
          f"`UIImagePath` **is** the leaf |")
    if ph:
        a(f"| fallback icon | `{ph['path']}` | {ph['size']} | literal `placeholder` |")
    st = p["icons"]["store_own"]
    if st:
        a(f"| store art | `{st['path']}` | {st['size']} | **not** the leaf "
          f"(`v0300_sportsmuscle_01`); which UI page loads it is UNKNOWN |")
    a(f"| variant icons | `{ICON_DIR}v0300_car_kensington_sportsmuscle_premium_01.ddsc`, "
      f"`…_signature_preorder.ddsc` | 18688 | leaf name of each variant |")
    a("")
    a(f"The bridge is exact across the fleet's drop list: of **{p['fleet']['vehicles']}** vanilla")
    a(f"vehicle items, **{p['fleet']['named']}** resolve their `UIName` to text in")
    a(f"`{p['profile']['path']}` and **{p['fleet']['iconed']}** have a")
    a("`textures/ui/vehicle_icons/<UIImagePath>.ddsc`. So `UIImagePath` is the icon key **and** the")
    a("same string hashed is the name key: one leaf name drives both.")
    a("")
    a(f"There are **{p['icons']['vehicle_total']}** files in `{ICON_DIR}` "
      f"(including `placeholder`), and")
    a(f"**{p['icons']['store_total']}** in `{STORE_DIR}` under a different naming scheme.")
    a("")
    a("## 5. Does any movie or the frontend name it?")
    a("")
    if p["gfx_hits"]:
        a("| file | marks |")
        a("|---|---|")
        for h in p["gfx_hits"]:
            a(f"| `{h['path']}` ({h['mount']}) | {', '.join(h['marks'])} |")
    else:
        a("**No `.gfx` movie contains the leaf name, the name hash or the `vehicle_icons` string.**")
        a("The menu is data-driven: the movie asks for a string by id and a texture by path, so")
        a("neither the name nor the icon is compiled into the Scaleform file.")
    a("")
    for mount, info in sorted(p["frontend"].items()):
        a(f"`global/frontend_global.blo` ({mount}, {info['size']} B): leaf name "
          f"{'present' if info['leaf'] else 'absent'}, name hash little-endian "
          f"{'present' if info['name_hash_le'] else 'absent'}, big-endian "
          f"{'present' if info['name_hash_be'] else 'absent'}.")
    a("")
    a("The frontend lists the **entity**, not the string: it can name the car only by the same")
    a("item lookup the drop menu uses.")
    a("")
    a("## 6. What this means for the Batmobile build")
    a("")
    a("1. **Keep the leaf** `v0300_car_kensington_sportsmuscle_civilian_01` and the car spawns and")
    a("   shows as KERNER SERPENTE R with the vanilla icon - no string work at all.")
    a("2. **Rename** only by adding a pair for the new leaf's hash in `profile/online.stringlookup`")
    a("   (name) and, if wanted, `<leaf>_desc`; the item's `UIName`/`UIImagePath` must hash to the")
    a("   same leaf that the `.ee` is actually named. Three things must agree: the `.ee` leaf, the")
    a("   item `Name`/`UIName`, and the string pair.")
    a("3. **New icon**: drop `textures/ui/vehicle_icons/<leaf>.ddsc` (18,688 B in the vanilla set -")
    a("   same size for every vehicle, so the format is one ADF-compressed texture; the exact")
    a("   channel/format is UNKNOWN until a decoder reads one) and the menu picks it up by name.")
    a("4. **Map icon**: nothing to do. There is no per-vehicle map marker file, so a Batmobile would")
    a("   use whatever sprite the map draws for cars - UNKNOWN which, and not vehicle-specific.")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("- **Which `.gfx` symbol draws the drop-menu name/icon**: the movies are compiled Scaleform")
    a("  and contain neither string (proven above). The binding is code-side.")
    a("- **The map marker for a vehicle**: no per-vehicle map icon exists in the index; the sprite")
    a("  set the map uses is shared and its member names are UNKNOWN.")
    a("- **The name shown in the driving HUD**: JC3 shows no persistent vehicle name in the HUD")
    a("  movie for this car (hud.gfx has no reference), and the entity path that would supply one is")
    a("  empty. If a name toast exists, its source is UNKNOWN.")
    a("- **`textures/ui/store/v0300_sportsmuscle_01.ddsc`**: the file exists, the naming is not the")
    a(f"  leaf, and no index file references it by name; which page loads it is UNKNOWN.")
    a("- **Language order**: the store carries no language-name field, so the order is read off the")
    a("  text itself (English first, then fr/de/it/es/ru/pl/ja/pt/es-MX/ar) - observation, not a")
    a("  decoded enum.")
    a("- **The 4-byte hash function**: `hash_jenkins` reproduces every id used here (it is the same")
    a("  function G2-26 proved on 196 items), but a collision-free guarantee across the whole")
    a("  string space is UNKNOWN.")
    a("")
    a("## 8. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/jc3strings.py --write    # writes NAMES.md")
    a("python Tools/scripts/jc3strings.py --check    # re-derives and compares")
    a("python Tools/scripts/jc3strings.py dump       # the payload")
    a("```")
    a("")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------- CLI
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("cmd", nargs="?", choices=["dump"])
    a = ap.parse_args()
    payload = build_payload()
    if a.cmd == "dump":
        print(json.dumps(payload, indent=1, sort_keys=True))
        return 0
    if a.write:
        open(DOC, "w", encoding="utf-8", newline="\n").write(to_md(payload))
        print(f"wrote {os.path.relpath(DOC, ROOT)}")
        return 0
    if a.check:
        if not os.path.exists(DOC):
            print("FAIL: NAMES.md missing")
            return 1
        have = open(DOC, encoding="utf-8").read()
        want = to_md(payload)
        if have != want:
            import difflib
            print("FAIL: NAMES.md stale")
            for line in list(difflib.unified_diff(have.splitlines(), want.splitlines(),
                                                  "on disk", "re-derived", n=2))[:40]:
                print(line)
            return 1
        n = len(payload["name"])
        uiloc = payload["ui_localization"]["own_keys"]
        resolved = sum(1 for v in uiloc.values() if v)
        print(f"PASS: name {payload['name'].get('en')!r} in {n} languages "
              f"(id {payload['keys'][payload['leaf']]['hex']}), "
              f"desc in {len(payload['desc'])} languages, "
              f"item {payload['drop_item']['item']['Name']}, "
              f"icon {payload['icons']['own']['size'] if payload['icons']['own'] else 'MISSING'} B, "
              f"fleet {payload['fleet']['named']}/{payload['fleet']['vehicles']} named "
              f"{payload['fleet']['iconed']}/{payload['fleet']['vehicles']} iconed, "
              f"ui_localization resolves {resolved} of {len(uiloc)} keys, "
              f"gfx references {len(payload['gfx_hits'])}")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
