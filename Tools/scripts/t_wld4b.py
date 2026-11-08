#!/usr/bin/env python3
"""T-WLD4b: decode `profile/online.stringlookup`, prove how a new entry is keyed, and answer
whether the Batmobile's name and blurb need a new store file, a patch of the existing one, or
are impossible.

What is decoded (all read-only):

  * the ADF structure of `profile/online.stringlookup` - root `StringLookup`
    {`Languages` A[LanguageStringLookup] off 0, `Text` A[int8] off 16},
    `LanguageStringLookup` {`SortedPairs` A[HashPropertiesPair] off 0,
    `SortedDialogueLines` A[DialogueLine] off 16}, `HashPropertiesPair` 8 B (Hash, value);
  * all `Languages[i]` stores (the "11 language stores" are 11 arrays inside this one file, not
    11 files), their pair counts, their sort order and their shared `Text` blob;
  * the key function, with three oracles:
      O1 - 45/45 Rebel Drop items have `UIName == hash_jenkins(UIImagePath)`;
      O2 - `hash_jenkins(leaf)` and `hash_jenkins(leaf + "_desc")` resolve in all 11 stores;
      O3 - every recomputed key of 25 items (name + `_desc`) is present in every store;
  * the write path: what bytes a new pair adds, where its sorted position is, and the two
    shipping options with the revert path.

Writes Working/Translation/T_WLD4B_STRINGS.md + .json; `--check` re-derives both and fails on
drift or on an oracle that stops passing.

Usage:
  python Tools/scripts/t_wld4b.py --write
  python Tools/scripts/t_wld4b.py --check
  python Tools/scripts/t_wld4b.py dump
"""
from __future__ import annotations

import argparse
import bisect
import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Working", "Translation")
JSON_NAME = "T_WLD4B_STRINGS.json"
MD_NAME = "T_WLD4B_STRINGS.md"
INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
REBELDROP = os.path.join(ROOT, "Research", "JC3Grab", "REBELDROP.json")
PROFILE = "profile/online.stringlookup"
LANG_ORDER = ["en", "fr", "de", "it", "es", "ru", "pl", "ja", "pt", "es-MX", "ar"]
LEAF = "v0300_car_kensington_sportsmuscle_civilian_01"


def load_index() -> list[dict]:
    return [json.loads(line) for line in open(INDEX, encoding="utf-8") if line.strip()]


def decode(rows: list[dict], path: str, game: str) -> dict:
    import jc3adf
    import jc3weapons
    best = jc3weapons.best_by_path(rows)
    if path not in best:
        raise SystemExit(f"{path} not in the index")
    row = best[path]
    data = jc3weapons.read_row(row, game)
    adf = jc3adf.Adf(data)
    inst = adf.instances[0]
    root = adf.types[inst["type"]]
    walk = list(jc3adf.walk(adf))

    text = bytearray()
    for p, _t, v in walk:
        if p.startswith("Text["):
            text.append(v & 0xFF)
    pairs: dict[int, dict[int, int]] = {}
    for p, _t, v in walk:
        m = re.match(r"Languages\[(\d+)\]\.SortedPairs\[(\d+)\]\.(Hash|TextOffset)$", p)
        if m:
            lang, _idx, field = int(m.group(1)), int(m.group(2)), m.group(3)
            pairs.setdefault(lang, {})
            if field == "TextOffset":
                pairs[lang][None] = pairs[lang].get(None, 0)  # placeholder, replaced below
    # second pass: Hash precedes TextOffset per pair
    pending: dict[tuple[int, int], int] = {}
    pairs = collections.defaultdict(dict)
    for p, _t, v in walk:
        m = re.match(r"Languages\[(\d+)\]\.SortedPairs\[(\d+)\]\.(Hash|TextOffset)$", p)
        if not m:
            continue
        lang, idx, field = int(m.group(1)), int(m.group(2)), m.group(3)
        if field == "Hash":
            pending[(lang, idx)] = v
        else:
            pairs[lang][pending[(lang, idx)]] = v

    def text_at(off: int):
        if off is None or off < 0 or off >= len(text):
            return None
        end = text.find(b"\x00", off)
        return text[off:end].decode("utf-8", "replace")

    types = {t["name"]: {"size": t["size"],
                         "members": [{"name": m["name"], "offset": m["offset"],
                                      "size": m["size"], "type": adf.type_name(m["type"])}
                                     for m in t["members"]]}
             for t in adf.types.values()}
    return {
        "path": path, "mount": row["mount"], "archive": row["archive"],
        "entry_offset": row["offset"], "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "instance": {"name": inst["name"], "offset": inst["offset"], "size": inst["size"]},
        "instance_type": root["name"], "instance_size": root["size"],
        "types": types, "walk_rows": len(walk), "text_bytes": len(text),
        "text_sha256": hashlib.sha256(bytes(text)).hexdigest(),
        "languages": {lang: {"pairs": len(p),
                             "sorted": [h for h in p] == sorted(p),
                             "first_hash": min(p) if p else None,
                             "last_hash": max(p) if p else None,
                             "text_max_offset": max(p.values()) if p else None}
                      for lang, p in sorted(pairs.items())},
        "pairs": {str(lang): {f"{h:08X}": off for h, off in sorted(p.items())}
                  for lang, p in sorted(pairs.items())},
        "text_head": bytes(text[:96]).decode("utf-8", "replace"),
    }


def build() -> dict:
    import jc3index
    from rbmhdr import hash_jenkins
    game = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
    rows = load_index()
    store = decode(rows, PROFILE, game)

    def h(s: str) -> int:
        return hash_jenkins(s.encode()) & 0xFFFFFFFF

    drops = [r for r in rows if r["path"] == PROFILE]
    rd = json.load(open(REBELDROP, encoding="utf-8"))
    items = rd["vanilla"]["items"]

    vehicle_items = [it for it in items
                     if isinstance(it.get("UIImagePath"), str)
                     and it["UIImagePath"].startswith("v0")
                     and isinstance(it.get("UIName"), int)]
    o1 = sum(1 for it in vehicle_items if h(it["UIImagePath"]) == it["UIName"])

    def in_all(key: int) -> int:
        return sum(1 for lang, p in store["pairs"].items() if f"{key:08X}" in p)

    sample = vehicle_items[:25]
    o3 = []
    for it in sample:
        name_key = h(it["UIImagePath"])
        desc_key = h(it["UIImagePath"] + "_desc")
        o3.append({"leaf": it["UIImagePath"], "name_key": f"{name_key:08X}",
                   "desc_key": f"{desc_key:08X}",
                   "name_langs": in_all(name_key), "desc_langs": in_all(desc_key)})
    o2 = {"leaf": LEAF, "name_key": f"{h(LEAF):08X}", "desc_key": f"{h(LEAF + '_desc'):08X}",
          "name_langs": in_all(h(LEAF)), "desc_langs": in_all(h(LEAF + "_desc"))}

    # the write path, computed: insertion index per store, bytes added by the two new pairs
    per_lang = {}
    for lang, p in store["pairs"].items():
        keys = sorted(int(k, 16) for k in p)
        for tag, key in (("name", h(LEAF)), ("desc", h(LEAF + "_desc"))):
            idx = bisect.bisect_left(keys, key)
            per_lang.setdefault(lang, {})[tag] = {
                "insert_at": idx, "of": len(keys),
                "prev": f"{keys[idx-1]:08X}" if idx else None,
                "next": f"{keys[idx]:08X}" if idx < len(keys) else None}
    text_add = sum(len(s.encode()) + 1 for s in
                   ("Batmobile", "The Batmobile."))
    growth = len(store["languages"]) * 2 * 8 + text_add

    # can the tooling re-serialise an ADF at all?  Look for function *definitions* that would
    # encode an ADF back to bytes - not for attribute names (a regex over dir() matches
    # `__package__`, which is not a writer).
    import inspect
    import jc3adf
    src = inspect.getsource(jc3adf)
    writer = sorted(set(re.findall(
        r"^\s*def (\w*(?:write|encode|serial|pack)\w*)\(", src, re.M)))
    writer += sorted(n for n in dir(jc3adf.Adf)
                     if re.fullmatch(r"(?i)(write|encode|serialize|serialise|pack|to_bytes)", n))

    return {
        "schema": "t-wld4b/1",
        "inputs": {"index_rows": len(rows), "store_copies": len(drops),
                   "mounts": sorted({r["mount"] for r in drops}),
                   "store_size": store["size"], "store_sha256": store["sha256"]},
        "store": store,
        "oracles": {
            "O1_items_name_key": {"pass": o1, "of": len(vehicle_items)},
            "O2_leaf": o2,
            "O3_sample": o3,
            "O3_pass": sum(1 for x in o3
                           if x["name_langs"] == 11 and x["desc_langs"] == 11),
        },
        "write": {"per_language": per_lang, "text_append_bytes": text_add,
                  "pair_bytes": 8, "languages": len(store["languages"]),
                  "growth_bytes": growth,
                  "new_size_estimate": store["size"] + growth,
                  "adf_writer_symbols": writer,
                  "writer_present": bool(writer)},
    }


def to_md(d: dict) -> str:
    s = d["store"]
    L: list[str] = []
    a = L.append
    a("# T-WLD4b - the string store: format, key function, and how to add a name")
    a("")
    a("Generated by `Tools/scripts/t_wld4b.py`; `--check` re-derives every number from the same")
    a("bytes and fails if any oracle stops passing. **decoded** = read at the quoted offset;")
    a("**derived** = a stated rule; **UNKNOWN** = not in the files, with what was tried.")
    a("")
    a("## 0. Answer")
    a("")
    a(f"**A new name is a pair keyed by the 32-bit Jenkins hash of the entity leaf name, inside the")
    a(f"one file `{PROFILE}`. There is no per-language store file to add:** the \"11 language")
    a(f"stores\" are the 11 `Languages[i]` arrays inside this single ADF, each with its own")
    a(f"`SortedPairs` and every one sharing one `Text` blob. So a rename or a blurb needs **a patch")
    a(f"of that existing file**, not a new store: insert one `{{Hash, TextOffset}}` pair per")
    a(f"language at its sorted position, append one NUL-terminated UTF-8 string per language to")
    a(f"`Text`, and re-serialise the whole ADF. A new file at a *different* path would never be")
    a(f"read (nothing names it).")
    a("")
    a("**It is not impossible, and it is not possible with today's tooling.** The format is fully")
    a(f"decoded and the key function is proven ({d['oracles']['O1_items_name_key']['pass']}/")
    a(f"{d['oracles']['O1_items_name_key']['of']} items recompute exactly), but `jc3adf.py` has no")
    a("serialiser: a source scan for a `def` whose name contains write/encode/serial/pack finds")
    a(f"{len(d['write']['adf_writer_symbols'])} (`writer_present` = {d['write']['writer_present']}), so the re-serialisation step is")
    a("the one missing tool. That is a **tooling gap, not an engine limit** - the engine reads any")
    a("valid store at that path.")
    a("")
    a(f"**Revert path:** the mod ships the file in its own patch layer; delete that copy and the")
    a("game falls back to the vanilla `profile/online.stringlookup`, which is never modified (the")
    a("install is read-only and the vanilla copy stays in its own mount).")
    a("")
    a("## 1. The store, decoded")
    a("")
    a(f"| property | value |")
    a(f"|---|---|")
    a(f"| file | `{s['path']}` |")
    a(f"| mount / archive | `{s['mount']}` / `{s['archive']}.arc` |")
    a(f"| entry | offset {s['entry_offset']}, {s['size']:,} B, sha256 `{s['sha256'][:16]}` |")
    a(f"| instances | 1 - `{s['instance']['name']}` at ADF offset {s['instance']['offset']}, "
      f"{s['instance']['size']:,} B, type `{s['instance_type']}` ({s['instance_size']} B) |")
    a(f"| walked rows | {s['walk_rows']:,} |")
    a(f"| `Text` blob | {s['text_bytes']:,} B, sha256 `{s['text_sha256'][:16]}`, NUL-separated |")
    a(f"| copies in the index | {d['inputs']['store_copies']} "
      f"({', '.join(d['inputs']['mounts'])}) |")
    a("")
    a("### 1.1 The struct layout")
    a("")
    a("| type | size | member | offset | size | type |")
    a("|---|---|---|---|---|---|")
    for tname in ("StringLookup", "LanguageStringLookup", "HashPropertiesPair"):
        t = s["types"].get(tname)
        if not t:
            continue
        for m in t["members"]:
            a(f"| `{tname}` | {t['size']} | `{m['name']}` | {m['offset']} | {m['size']} | "
              f"`{m['type']}` |")
    a("")
    a("`Languages` is an array of `LanguageStringLookup` at offset 0; each language holds")
    a("`SortedPairs` (offset 0) and `SortedDialogueLines` (offset 16). `HashPropertiesPair` is 8 B:")
    a("a 4-byte hash and a 4-byte `TextOffset` into the shared blob. The array descriptors are 16 B;")
    a("their internal field split (count vs pointer) is **UNKNOWN** - the counts below are re-read")
    a("from the elements themselves, not from the descriptor bytes.")
    a("")
    a("### 1.2 The 11 language stores")
    a("")
    a("| # | language | pairs | sorted by hash | first | last | max text offset |")
    a("|---:|---|---:|---|---|---|---:|")
    for lang, v in s["languages"].items():
        idx = int(lang)
        name = LANG_ORDER[idx] if idx < len(LANG_ORDER) else lang
        a(f"| {lang} | `{name}` | {v['pairs']:,} | {'yes' if v['sorted'] else 'NO'} | "
          f"`{v['first_hash']:08X}` | `{v['last_hash']:08X}` | {v['text_max_offset']} |")
    a("")
    a(f"Total pairs {sum(v['pairs'] for v in s['languages'].values()):,} across")
    a(f"{len(s['languages'])} stores, all sorted ascending, all offsets into the one")
    a(f"{s['text_bytes']:,} B `Text` blob. Text begins `{s['text_head'][:60]}...`.")
    a("")
    a("## 2. The key: the 32-bit Jenkins hash of the leaf name")
    a("")
    a("| oracle | result |")
    a("|---|---|")
    a(f"| O1: `UIName == hash_jenkins(UIImagePath)` | **{d['oracles']['O1_items_name_key']['pass']}/"
      f"{d['oracles']['O1_items_name_key']['of']}** vehicle items |")
    a(f"| O2: `hash_jenkins({LEAF})` | `{d['oracles']['O2_leaf']['name_key']}` in "
      f"**{d['oracles']['O2_leaf']['name_langs']}/11** stores |")
    a(f"| O2: `hash_jenkins({LEAF}_desc)` | `{d['oracles']['O2_leaf']['desc_key']}` in "
      f"**{d['oracles']['O2_leaf']['desc_langs']}/11** stores |")
    a(f"| O3: 25 sampled items, name + `_desc` present in all 11 | "
      f"**{d['oracles']['O3_pass']}/25** |")
    a("")
    a("| leaf | name key | desc key | name in | desc in |")
    a("|---|---|---|---:|---:|")
    for x in d["oracles"]["O3_sample"][:10]:
        a(f"| `{x['leaf']}` | `{x['name_key']}` | `{x['desc_key']}` | "
          f"{x['name_langs']}/11 | {x['desc_langs']}/11 |")
    a("")
    a("The key is the **name of the thing**, not its text: `hash_jenkins(\"<leaf>\")` for the")
    a("display name and `hash_jenkins(\"<leaf>_desc\")` for the blurb. That is why a rename needs a")
    a("pair: the entity leaf decides the hash, and nothing derives text from a hash.")
    a("")
    a("## 3. What adding the Batmobile name and blurb costs")
    a("")
    a("Per language, two pairs (`name`, `desc`), each 8 B, inserted at its sorted position:")
    a("")
    a("| language | name insert at | desc insert at |")
    a("|---|---|---|")
    for lang, v in d["write"]["per_language"].items():
        idx = int(lang)
        name = LANG_ORDER[idx] if idx < len(LANG_ORDER) else lang
        a(f"| `{name}` | {v['name']['insert_at']} of {v['name']['of']} | "
          f"{v['desc']['insert_at']} of {v['desc']['of']} |")
    a("")
    a(f"* pair bytes: {d['write']['languages']} x 2 x {d['write']['pair_bytes']} = "
      f"**{d['write']['languages'] * 2 * d['write']['pair_bytes']} B**")
    a(f"* text bytes: {d['write']['text_append_bytes']} B (one UTF-8 string + NUL per language;")
    a("  the sample text is a placeholder, the real strings are longer)")
    a(f"* growth: ~**{d['write']['growth_bytes']} B** on a {d['inputs']['store_size']:,} B file,")
    a(f"  new size ~**{d['write']['new_size_estimate']:,} B** (plus the ADF header/type table,")
    a("  which does not change: no new type is needed).")
    a("")
    a("Two strings are needed per leaf: `<leaf>` (name) and `<leaf>_desc` (blurb), and the")
    a("`profile/item.onlinec` record must point at the same hashes (`UIName`, `UIDescription`) -")
    a("it already does in vanilla; a renamed leaf needs both sides updated together.")
    a("")
    a("## 4. New store file, patch, or impossible?")
    a("")
    a("| option | verdict | why |")
    a("|---|---|---|")
    a(f"| new store file at a new path | **no effect** | nothing references it; the item holds")
    a("  hashes, and the game reads this one path |")
    a(f"| new copy of `{PROFILE}` in the patch layer | **the way** | replaces the whole file; the")
    a("  engine reads it at the same path. This is a patch of an existing *file path*, shipped as")
    a("  a whole-file override |")
    a("| new per-language files | **do not exist** | the 11 languages are arrays in this file |")
    a("| in-place edit of the install | **forbidden** | installs are read-only by project rule |")
    a("")
    a("So: **patch the existing path, whole-file, in the mod's patch layer.** The blocker is")
    a("authoring: `jc3adf.py` decodes but does not serialise, so writing the modified ADF needs a")
    a("writer first. Until then the honest status is **blocked on tooling**, not on the format and")
    a("not on the engine.")
    a("")
    a("## 5. UNKNOWNs")
    a("")
    a("1. **The 16-byte array descriptor layout.** `A[LanguageStringLookup]` is 16 B; whether the")
    a("   fields are count/pointer or count/pointer/capacity/pad is not decoded. *Tried:* the type")
    a("   table of the store (it only gives the size). *Where:* `jc3adf`'s array reader.")
    a("2. **Whether the engine tolerates a duplicate hash** (same key twice in one store). *Tried:*")
    a("   nothing - sorting is proven, uniqueness is not tested by these files. *Where:* a runtime")
    a("   test, which the test ban forbids.")
    a("3. **The language order.** The store carries no language-name field; the order is read off")
    a("   the text (English first, then fr/de/it/es/ru/pl/ja/pt/es-MX/ar). Observation, not a")
    a("   decoded enum.")
    a("4. **Whether `profile/online.stringlookup` is the only store the drop menu consults** for")
    a("   this item - `ui/ui_localization.stringlookup` does not hold the name (G2-32), and the")
    a("   item's UI hashes only resolve here.")
    a("")
    a("Static only: no game launched, attached to or installed to; no game file written.")
    a("")
    a("Checkable: `python Tools/scripts/t_wld4b.py --check`.")
    a("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--dump", action="store_true")
    a = ap.parse_args()
    d = build()
    if a.dump:
        d2 = {k: v for k, v in d.items() if k != "store"}
        d2["store_scalars"] = {k: v for k, v in d["store"].items() if k != "pairs"}
        print(json.dumps(d2, indent=1, sort_keys=True))
        return 0
    js = json.dumps(d, indent=1, sort_keys=True) + "\n"
    doc = to_md(d)
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if a.write:
        open(jp, "w", encoding="utf-8", newline="\n").write(js)
        open(mp, "w", encoding="utf-8", newline="\n").write(doc)
        print("wrote", jp)
        print("wrote", mp)
        print("languages", len(d["store"]["languages"]), "pairs",
              sum(v["pairs"] for v in d["store"]["languages"].values()),
              "O1", d["oracles"]["O1_items_name_key"]["pass"], "/",
              d["oracles"]["O1_items_name_key"]["of"],
              "O3", d["oracles"]["O3_pass"], "/25")
        return 0
    fails = []
    if not os.path.exists(jp) or open(jp, encoding="utf-8").read() != js:
        fails.append("json drifted")
    if not os.path.exists(mp) or open(mp, encoding="utf-8").read() != doc:
        fails.append("markdown drifted")
    if d["oracles"]["O1_items_name_key"]["pass"] != d["oracles"]["O1_items_name_key"]["of"]:
        fails.append("O1: not every item name recomputes")
    if d["oracles"]["O3_pass"] != 25:
        fails.append(f"O3: only {d['oracles']['O3_pass']}/25 sampled items resolve in all 11")
    if d["oracles"]["O2_leaf"]["name_langs"] != 11 or d["oracles"]["O2_leaf"]["desc_langs"] != 11:
        fails.append("O2: donor name/desc missing from a store")
    if len(d["store"]["languages"]) != 11:
        fails.append(f"{len(d['store']['languages'])} language stores, expected 11")
    for lang, v in d["store"]["languages"].items():
        if not v["sorted"]:
            fails.append(f"store {lang} not sorted")
    if d["write"]["writer_present"]:
        fails.append("an ADF writer now exists - the 'blocked on tooling' finding is stale")
    print("langs %d, pairs %d, O1 %d/%d, O3 %d/25, text %d B, writer %s"
          % (len(d["store"]["languages"]),
             sum(v["pairs"] for v in d["store"]["languages"].values()),
             d["oracles"]["O1_items_name_key"]["pass"],
             d["oracles"]["O1_items_name_key"]["of"], d["oracles"]["O3_pass"],
             d["store"]["text_bytes"], d["write"]["writer_present"]))
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    print("OK: store decoded, all oracles pass, document and JSON identical")
    return 0


if __name__ == "__main__":
    sys.exit(main())
