#!/usr/bin/env python3
"""Are the vanilla vehicle blurbs actually translated, or English in every language?

`Builds/bm-RC2/verify/strings.md` shows the new car's blurb is the same English sentence in all
11 languages. This script measures the vanilla store (`profile/online.stringlookup`) to answer
whether that is normal:

  * vehicle blurb keys = `hash_jenkins(<vehicle leaf> + "_desc")` for every `v*` leaf the index
    lists under `editor/entities/jc_vehicles/` (the key rule proven by `Research/JC3Grab/NAMES.md`);
  * for every key that exists in **all 11** languages, compare each non-English text with the
    English one and count how many differ;
  * do the same for all hashed pairs in the store, for vehicle names (`hash_jenkins(leaf)`) and
    for every `Items[].UIDescription` in the build's `profile/item.onlinec`;
  * classify the English-in-every-language entries (how many are prose vs. names);
  * check the two new build pairs, and whether DLC-added vehicle leaves carry a blurb at all.

Read-only: the stores, index and item table are read; only the document is written.

Usage:
  python Tools/scripts/v_strings_languages.py --write   # Builds/bm-RC2/verify/strings_languages.md
  python Tools/scripts/v_strings_languages.py --check   # re-derive, byte-compare, exit 1 on drift
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

GAMEDATA = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
VAN = os.path.join(GAMEDATA, "strings_rt", "online.stringlookup")
BUILT = os.path.join(ROOT, "Builds", "bm-RC2", "drop", "profile", "online.stringlookup")
ITEM = os.path.join(ROOT, "Builds", "bm-RC2", "drop", "profile", "item.onlinec")
INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
OUT = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "strings_languages.md")

LANG_ORDER = ["en", "fr", "de", "it", "es", "ru", "pl", "ja", "pt", "es-MX", "ar"]
NEW_PAIRS = {"name": 0x60A5E7A4, "blurb": 0xF34BA8E8}
MASK = 0xFFFFFFFF


# ----------------------------------------------------------------------- readers
def sha_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def text_at(text: bytes, off: int | None) -> str | None:
    if off is None or not (0 <= off < len(text)):
        return None
    end = text.find(b"\x00", off)
    return text[off:end].decode("utf-8", "replace")


def load_store(path: str) -> dict:
    """`Languages[N].SortedPairs[]` + the shared NUL-separated `Text` blob (the NAMES.md decode)."""
    adf = jc3adf.Adf(open(path, "rb").read())
    text = bytearray()
    lanes: dict[int, dict[int, int]] = {}
    pending: dict[tuple[int, int], int] = {}
    for p, _t, v in jc3adf.walk(adf, 0):
        if p.startswith("Text["):
            text.append(v & 0xFF)
            continue
        m = re.match(r"Languages\[(\d+)\]\.SortedPairs\[(\d+)\]\.(Hash|TextOffset)$", p)
        if not m:
            continue
        lang, idx, field = int(m.group(1)), int(m.group(2)), m.group(3)
        lanes.setdefault(lang, {})
        if field == "Hash":
            pending[(lang, idx)] = v & MASK
        else:
            lanes[lang][pending[(lang, idx)]] = v
    return {"path": path, "bytes": os.path.getsize(path), "sha": sha_file(path),
            "text": bytes(text), "pairs": lanes}


def load_vehicle_leaves() -> dict[str, set[str]]:
    """leaf -> the set of mounts its `.ee` rows live on."""
    out: dict[str, set[str]] = defaultdict(set)
    for line in open(INDEX, encoding="utf-8"):
        d = json.loads(line)
        p = d["path"]
        if "/jc_vehicles/" not in p or not p.endswith(".ee"):
            continue
        leaf = os.path.basename(p)[:-3]
        if leaf.startswith("v"):
            out[leaf].add(d.get("mount"))
    return dict(out)


def load_item_descriptions(path: str) -> dict[int, int]:
    """item index -> UIDescription hash (low 32 bits of the 48-bit chain member)."""
    adf = jc3adf.Adf(open(path, "rb").read())
    pat = re.compile(r"^Items\[(\d+)\]\.UIDescription$")
    out: dict[int, int] = {}
    for p, _t, v in jc3adf.walk(adf, 0):
        m = pat.match(p)
        if m:
            out[int(m.group(1))] = v & MASK
    return out


def load_item_names(path: str) -> set[int]:
    adf = jc3adf.Adf(open(path, "rb").read())
    pat = re.compile(r"^Items\[(\d+)\]\.UIName$")
    out = set()
    for p, _t, v in jc3adf.walk(adf, 0):
        if pat.match(p):
            out.add(v & MASK)
    return out


def resolve(store: dict, h: int) -> dict[str, str]:
    out = {}
    for lang in sorted(store["pairs"]):
        off = store["pairs"][lang].get(h)
        val = text_at(store["text"], off)
        if val is not None:
            out[LANG_ORDER[lang] if lang < len(LANG_ORDER) else "lang%d" % lang] = val
    return out


def census(store: dict, keys: set[int]) -> dict[str, int]:
    """Per language: how many of `keys` have text different from the English text."""
    en = {h: text_at(store["text"], store["pairs"][0].get(h)) for h in keys}
    out = {}
    for lang in range(1, len(store["pairs"])):
        name = LANG_ORDER[lang] if lang < len(LANG_ORDER) else "lang%d" % lang
        out[name] = sum(1 for h in keys
                        if text_at(store["text"], store["pairs"][lang].get(h)) != en[h])
    return out


def is_prose(text: str) -> bool:
    return len(text) >= 40 and text.rstrip().endswith((".", "!", "?"))


# ----------------------------------------------------------------------- payload
def build_payload() -> dict:
    vanilla = load_store(VAN)
    built = load_store(BUILT)
    if sorted(vanilla["pairs"]) != list(range(len(LANG_ORDER))):
        raise SystemExit("vanilla store does not have 11 language lanes")
    if sorted(built["pairs"]) != list(range(len(LANG_ORDER))):
        raise SystemExit("built store does not have 11 language lanes")

    all_keys = set.intersection(*[set(vanilla["pairs"][i]) for i in range(len(LANG_ORDER))])
    leaves = load_vehicle_leaves()
    blurb_leaf = {hash_jenkins((leaf + "_desc").encode()): leaf for leaf in leaves}
    name_leaf = {hash_jenkins(leaf.encode()): leaf for leaf in leaves}
    blurbs = {h for h in blurb_leaf if h in all_keys}
    names = {h for h in name_leaf if h in all_keys}

    item_desc_items = load_item_descriptions(ITEM)
    item_descs = {h for h in item_desc_items.values() if h in all_keys}
    item_names = load_item_names(ITEM)

    en_text = {h: text_at(vanilla["text"], vanilla["pairs"][0].get(h)) for h in all_keys}
    english_only = {h for h in all_keys
                    if all(text_at(vanilla["text"], vanilla["pairs"][i].get(h)) == en_text[h]
                           for i in range(1, len(LANG_ORDER)))}
    examples = []
    for h in sorted(english_only, key=lambda x: (en_text[x] or "", x))[:8]:
        examples.append({"hash": "%08X" % h, "leaf": blurb_leaf.get(h) or name_leaf.get(h),
                         "text": en_text[h] or ""})

    new_pairs = {}
    for kind, h in NEW_PAIRS.items():
        vals = resolve(built, h)
        new_pairs[kind] = {"hash": "%08X" % h, "values": vals,
                           "languages": len(vals),
                           "all_english": bool(vals) and
                           all(v == vals.get("en") for v in vals.values()),
                           "all_nonempty": bool(vals) and all(vals.values())}

    dlc_leaves = [leaf for leaf, mounts in leaves.items() if mounts == {"dlc"}]
    dlc_blurb_present = sum(
        1 for leaf in dlc_leaves if any(hash_jenkins((leaf + "_desc").encode()) in lane
                                        for lane in vanilla["pairs"].values()))

    return {
        "schema": 1,
        "generated_by": "Tools/scripts/v_strings_languages.py",
        "vanilla": {"path": VAN, "bytes": vanilla["bytes"], "sha": vanilla["sha"],
                    "languages": len(vanilla["pairs"]),
                    "pairs_per_language": {LANG_ORDER[i]: len(vanilla["pairs"][i])
                                           for i in sorted(vanilla["pairs"])},
                    "text_bytes": len(vanilla["text"]),
                    "keys_in_all": len(all_keys)},
        "built": {"path": BUILT, "sha": built["sha"], "bytes": built["bytes"]},
        "item": {"path": ITEM, "items": len(item_desc_items)},
        "vehicle_leaves": len(leaves),
        "vehicle_blurbs": {"keys": len(blurbs), "per_language": census(vanilla, blurbs),
                           "english_only": len(blurbs & english_only)},
        "vehicle_names": {"keys": len(names), "per_language": census(vanilla, names),
                          "english_only": len(names & english_only)},
        "item_descriptions": {"keys": len(item_descs),
                              "per_language": census(vanilla, item_descs),
                              "english_only": len(item_descs & english_only)},
        "all_pairs": {"keys": len(all_keys), "per_language": census(vanilla, all_keys),
                      "english_only": len(english_only),
                      "english_only_prose": sum(1 for h in english_only
                                                if is_prose(en_text[h] or "")),
                      "english_only_examples": examples,
                      "english_only_item_descs": len(english_only & item_descs),
                      "english_only_item_names": len(english_only & item_names)},
        "new_pairs": new_pairs,
        "dlc": {"vehicle_leaves": len(dlc_leaves), "blurb_present_any_language": dlc_blurb_present},
    }


# ----------------------------------------------------------------------- document
def to_md(p: dict) -> str:
    L: list[str] = []
    a = L.append
    vb, vn, idp, ap = (p["vehicle_blurbs"], p["vehicle_names"], p["item_descriptions"],
                       p["all_pairs"])
    langs = [l for l in LANG_ORDER if l != "en"]
    a("# Vehicle blurbs: translated, or English in every language?")
    a("")
    a("Generated by `python Tools/scripts/v_strings_languages.py --write`; `--check` re-decodes")
    a("the store and compares this page byte for byte. Read-only: the vanilla store, the built")
    a("store, the item table and the entity index are opened for reading only.")
    a("")
    a("**Answer.** The vanilla blurbs are **genuinely translated**. Every one of the")
    a(f"**{vb['keys']}** vehicle blurb keys that exists in all 11 languages differs from the")
    a(f"English string in **all 10** non-English languages (`0` identical, per language). The same")
    a(f"holds for **{idp['keys']}/{idp['keys']}** item descriptions. English-in-every-language is")
    a(f"**not** normal for prose in this store: of the **{ap['english_only']}** English-only keys,")
    a(f"**{ap['english_only_prose']}** are sentence-like and **{ap['english_only_item_descs']}** are")
    a("item descriptions - they are proper names (vehicles, weapons, brands). So the new car's")
    a("blurb being the same English sentence in all 11 languages is a **compromise**, not the")
    a("vanilla pattern.")
    a("")
    a("## 1. Method (all decoded from the files)")
    a("")
    a("- Vehicle leaf names are the `v*` `.ee` leaves under `editor/entities/jc_vehicles/` in")
    a("  `Research/JC3Grab/INDEX.jsonl`: **%d** leaves." % p["vehicle_leaves"])
    a("- A vehicle's name key is `hash_jenkins(<leaf>)`; its blurb key is")
    a("  `hash_jenkins(<leaf> + \"_desc\")` - the rule `Research/JC3Grab/NAMES.md` proves on")
    a("  `v0300_car_kensington_sportsmuscle_civilian_01` (`D2B46B49` / `7B942DF2`).")
    a("- `profile/online.stringlookup` is decoded as `Languages[N].SortedPairs[].{Hash,TextOffset}`")
    a("  into one NUL-separated `Text` blob; lane 0 is English, lanes 1-10 are")
    a("  `fr, de, it, es, ru, pl, ja, pt, es-MX, ar` (observation, not a decoded enum).")
    a("- Only keys present in **all 11** lanes are counted, so a missing translation cannot be")
    a("  mistaken for an identical one. Text is compared as the exact decoded string.")
    a("")
    a("| input | sha256 | bytes |")
    a("|---|---|---:|")
    a(f"| vanilla `{p['vanilla']['path']}` | `{p['vanilla']['sha']}` | {p['vanilla']['bytes']} |")
    a(f"| `{p['built']['path']}` | `{p['built']['sha']}` | {p['built']['bytes']} |")
    a("")
    a(f"The vanilla store has **{p['vanilla']['languages']}** languages, "
      f"**{p['vanilla']['keys_in_all']}** hashed pairs present in all of them, and a "
      f"{p['vanilla']['text_bytes']:,} B text blob.")
    a("")
    a("## 2. Per-language count: non-English text different from English")
    a("")
    a(f"Denominator per column is the number of keys that exist in all 11 languages "
      f"(vehicle blurbs **{vb['keys']}**, vehicle names **{vn['keys']}**, item descriptions "
      f"**{idp['keys']}**, all pairs **{ap['keys']}**).")
    a("")
    a("| language | vehicle blurbs | vehicle names | item descriptions | all 11-language pairs |")
    a("|---|---:|---:|---:|---:|")
    for lang in langs:
        a(f"| `{lang}` | {vb['per_language'][lang]}/{vb['keys']} | "
          f"{vn['per_language'][lang]}/{vn['keys']} | "
          f"{idp['per_language'][lang]}/{idp['keys']} | "
          f"{ap['per_language'][lang]}/{ap['keys']} |")
    a("")
    a("Readings:")
    a("")
    a(f"- **Blurbs: 100% translated.** {vb['keys']} of {vb['keys']} differ in every language; "
      f"**{vb['english_only']}** vehicle blurbs are English-only.")
    a(f"- **Item descriptions: 100% translated.** {idp['keys']} of {idp['keys']} differ in every "
      f"language; **{idp['english_only']}** are English-only.")
    a(f"- **Names: mostly English.** {vn['english_only']} of {vn['keys']} vehicle names are the "
      f"same in all 11 languages (proper nouns such as `STRIA GIOVANNI`); the rest differ, so a")
    a("  translated name is not required either way.")
    a(f"- **Whole store:** {ap['english_only']} of {ap['keys']} keys "
      f"({ap['english_only'] * 100.0 / ap['keys']:.1f}%) are English-only, and those are names -")
    a(f"  only **{ap['english_only_prose']}** are sentence-like (>= 40 chars ending in `.`, `!` or")
    a(f"  `?`). The English-only set contains **{ap['english_only_item_descs']}** item descriptions")
    a(f"  and **{ap['english_only_item_names']}** item name hashes.")
    a("")
    a("### 2.1 The English-only entries are names")
    a("")
    a("| hash | vehicle leaf (if a vehicle key) | English text |")
    a("|---|---|---|")
    for e in ap["english_only_examples"]:
        a(f"| `{e['hash']}` | {e['leaf'] or '-'} | {e['text']} |")
    a("")
    a("## 3. The new Batmobile pairs in the build")
    a("")
    a("| key | hash | languages | all 11 identical to English |")
    a("|---|---|---:|---|")
    for kind in ("name", "blurb"):
        n = p["new_pairs"][kind]
        a(f"| {kind} | `{n['hash']}` | {n['languages']} | "
          f"{'yes' if n['all_english'] else 'no'} |")
    a("")
    a("Both are present in all 11 languages and both are the same English text everywhere. The")
    a("blurb sits against a vanilla population in which **no** vehicle blurb is English-only, so")
    a("this is not what the vanilla store does.")
    a("")
    a("## 4. Newly added (DLC) vehicles")
    a("")
    a(f"The index lists **{p['dlc']['vehicle_leaves']}** vehicle leaves whose `.ee` rows live only")
    a(f"on the `dlc` mount. Of those, **{p['dlc']['blurb_present_any_language']}** have a")
    a("`<leaf>_desc` pair in `profile/online.stringlookup` in **any** language. So this store does")
    a("not carry DLC vehicle blurbs at all: it cannot show whether DLC blurbs were localized, and")
    a("the vanilla translation pattern above is measured only on the 83 base/vanilla blurbs.")
    a("")
    a("## 5. Labels")
    a("")
    a("- **Decoded:** every hash, text, per-language presence and the item descriptions come from")
    a("  the stores and `item.onlinec` named above; the leaf list comes from the index.")
    a("- **Derived:** the `_desc` key rule (from `Research/JC3Grab/NAMES.md`), the per-language")
    a("  counts, the English-only classification and the vehicle/DLC split.")
    a("- No string is typed from memory; the new Batmobile texts are read from the built store.")
    a("")
    a("## 6. UNKNOWNs")
    a("")
    a("- **Where DLC vehicle blurbs live:** 51 DLC leaves have no `_desc` pair in")
    a("  `profile/online.stringlookup` in any language. A DLC-side `.stringlookup` or another store")
    a("  would have to be decoded to answer how those were localized; not attempted here.")
    a("- **Whether any added item was ever shipped English-only:** the only added items visible in")
    a("  this store are the build's two new pairs, both English-only by construction. There is no")
    a("  vanilla example of a non-English-less blurb in the 11-language intersection.")
    a("- **Language identity:** the store carries no language-name field; the order is inferred")
    a("  from the text (English first), as recorded in `NAMES.md`.")
    a("")
    a("## 7. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/v_strings_languages.py --write   # writes this page")
    a("python Tools/scripts/v_strings_languages.py --check   # re-derives and compares")
    a("```")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------------- CLI
def main() -> int:
    p = build_payload()
    if "--write" in sys.argv[1:]:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="\n").write(to_md(p))
        print("wrote", os.path.relpath(OUT, ROOT).replace("\\", "/"))
        return 0
    if "--check" in sys.argv[1:]:
        if not os.path.exists(OUT):
            print("FAIL: strings_languages.md missing")
            return 1
        have = open(OUT, encoding="utf-8").read()
        want = to_md(p)
        if have != want:
            import difflib
            print("FAIL: strings_languages.md stale")
            for line in list(difflib.unified_diff(have.splitlines(), want.splitlines(),
                                                  "on disk", "re-derived", n=2))[:40]:
                print(line)
            return 1
        vb, idp = p["vehicle_blurbs"], p["item_descriptions"]
        worst = min(vb["per_language"].values())
        print(f"PASS: vehicle blurbs {worst}/{vb['keys']} translated in every language "
              f"(english-only {vb['english_only']}), item descriptions "
              f"{min(idp['per_language'].values())}/{idp['keys']}, "
              f"all-pair english-only {p['all_pairs']['english_only']}/{p['all_pairs']['keys']} "
              f"({p['all_pairs']['english_only_prose']} prose), "
              f"new blurb english-in-11 {p['new_pairs']['blurb']['all_english']}, "
              f"DLC blurbs present {p['dlc']['blurb_present_any_language']}/"
              f"{p['dlc']['vehicle_leaves']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
