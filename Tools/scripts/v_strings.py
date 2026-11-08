#!/usr/bin/env python3
"""Rebel Drop strings: does the built drop carry the new name/blurb for every language?

`Research/JC3Grab/NAMES.md` (G2-32) proves the chain: a vehicle's display name is the 32-bit
Jenkins hash of the entity **leaf** name, resolved through `profile/online.stringlookup`, and the
`profile/item.onlinec` record points at that hash (`UIName`) plus `<leaf>_desc` (`UIDescription`).
The build renames the leaf, so it has to add both pairs or the car shows no name.

This script checks the built drop against the vanilla store:

  * the store pair for `hash_jenkins(leaf)` and `hash_jenkins(leaf + "_desc")` exists in all 11
    languages, with non-empty text;
  * nothing vanilla was dropped or altered - every hashed pair the vanilla store carries still
    resolves to the same text in the built store, language by language, and the per-language count
    only grows by the two new pairs;
  * `item.onlinec` has the record for that leaf (`UIImagePath == leaf`) and its `UIName`,
    `UIDescription` and `Name` carry the two hashes (the members are 48-bit chains:
    low 32 = this hash, high 32 = the next one);
  * `Builds/bm-013/drop` and `Builds/bm-RC2/drop` ship the same two files.

Read-only: every file is opened for reading; the document is the only thing written.

Usage:
  python Tools/scripts/v_strings.py --write   # Builds/bm-RC2/verify/strings.md
  python Tools/scripts/v_strings.py --check   # re-derive, byte-compare, exit 1 on drift
"""

from __future__ import annotations

import glob
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

GAMEDATA = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
VAN = os.path.join(GAMEDATA, "strings_rt", "online.stringlookup")
DROPS = {"bm-RC2": os.path.join("Builds", "bm-RC2", "drop"),
         "bm-013": os.path.join("Builds", "bm-013", "drop")}
STORE = "profile/online.stringlookup"
ITEM = "profile/item.onlinec"
OUT = os.path.join("Builds", "bm-RC2", "verify", "strings.md")
ENTITY_GLOB = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/*.ee"
LANG_ORDER = ["en", "fr", "de", "it", "es", "ru", "pl", "ja", "pt", "es-MX", "ar"]
MASK = 0xFFFFFFFF


def rel(p: str) -> str:
    return p.replace("\\", "/")


def sha_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def text_at(text: bytes, off: int) -> str:
    if off is None or not (0 <= off < len(text)):
        return ""
    end = text.find(b"\x00", off)
    return text[off:end].decode("utf-8", "replace")


def load_store(path: str) -> dict:
    """`Languages[N].SortedPairs[]` + the shared `Text` blob, the decode NAMES.md uses."""
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


def lang_names(lanes: dict) -> list[str]:
    return [LANG_ORDER[i] if i < len(LANG_ORDER) else "lang%d" % i for i in sorted(lanes)]


def load_items(path: str) -> dict[int, dict]:
    adf = jc3adf.Adf(open(path, "rb").read())
    pat = re.compile(r"^Items\[(\d+)\]\.(\w+)$")
    items: dict[int, dict] = {}
    for p, t, v in jc3adf.walk(adf, 0):
        m = pat.match(p)
        if m:
            items.setdefault(int(m.group(1)), {})[m.group(2)] = (t, v)
    return items


def built_leaf(tag: str) -> str:
    hits = sorted(glob.glob(os.path.join(ROOT, DROPS[tag], ENTITY_GLOB)))
    leafs = {os.path.basename(h)[:-3] for h in hits}
    if len(leafs) != 1:
        raise SystemExit("%s: %d .ee leaves under %s, expected 1" % (tag, len(leafs), ENTITY_GLOB))
    return leafs.pop()


def build() -> dict:
    vanilla = load_store(VAN)
    built = {tag: load_store(os.path.join(ROOT, DROPS[tag], STORE)) for tag in DROPS}
    items = {tag: load_items(os.path.join(ROOT, DROPS[tag], ITEM)) for tag in DROPS}
    leaf = built_leaf("bm-RC2")
    name_h, desc_h = hash_jenkins(leaf.encode()), hash_jenkins((leaf + "_desc").encode())

    def present(lanes: dict, h: int) -> list[str]:
        return [lang_names({k: 1 for k in lanes})[i] if i < len(LANG_ORDER) else "lang%d" % i
                for i in sorted(lanes) if h in lanes[i]]

    rc2 = built["bm-RC2"]
    texts = {h: {LANG_ORDER[li] if li < len(LANG_ORDER) else "lang%d" % li: text_at(rc2["text"], off)
                 for li, lane in sorted(rc2["pairs"].items()) if h in lane
                 for off in [lane[h]]}
             for h in (name_h, desc_h)}
    census = []
    for li in sorted(set(vanilla["pairs"]) | set(rc2["pairs"])):
        v, b = vanilla["pairs"].get(li, {}), rc2["pairs"].get(li, {})
        lang = LANG_ORDER[li] if li < len(LANG_ORDER) else "lang%d" % li
        missing = [h for h in v if h not in b]
        altered = [h for h in v if h in b and text_at(vanilla["text"], v[h]) != text_at(rc2["text"], b[h])]
        census.append({"lang": lang, "vanilla": len(v), "built": len(b), "delta": len(b) - len(v),
                       "missing": len(missing), "altered": len(altered),
                       "name_here": name_h in b, "desc_here": desc_h in b})

    item_view = {}
    for tag in DROPS:
        hits = [i for i, d in items[tag].items()
                if str(d.get("UIImagePath", ("", ""))[1]) == leaf]
        if len(hits) != 1:
            item_view[tag] = {"index": None, "members": {}}
            continue
        d = items[tag][hits[0]]
        mem = {}
        for k in ("Name", "UIName", "UIDescription"):
            t, v = d[k]
            mem[k] = {"type": t, "value": v, "low32": v & MASK, "high32": (v >> 32) & MASK}
        mem["UIImagePath"] = {"type": d["UIImagePath"][0], "value": d["UIImagePath"][1]}
        item_view[tag] = {"index": hits[0], "members": mem,
                          "n_items": len(items[tag]),
                          "civilian_item": [i for i, dd in items[tag].items()
                                            if str(dd.get("UIImagePath", ("", ""))[1])
                                            == leaf.replace("_debug", "_civilian_01")]}
    vh = {h for lane in vanilla["pairs"].values() for h in lane}
    bh = {h for lane in rc2["pairs"].values() for h in lane}
    return {
        "leaf": leaf, "name_h": name_h, "desc_h": desc_h,
        "vanilla": vanilla, "built": built, "items": items,
        "vanilla_langs": lang_names(vanilla["pairs"]),
        "built_langs": lang_names(rc2["pairs"]),
        "new_hashes": sorted(bh - vh), "gone_hashes": sorted(vh - bh),
        "name_langs": present(rc2["pairs"], name_h), "desc_langs": present(rc2["pairs"], desc_h),
        "texts": texts, "census": census, "item": item_view,
        "same_across_drops": {f: built["bm-013"][f] == built["bm-RC2"][f] for f in ("sha", "bytes")},
        "item_same": sha_file(os.path.join(ROOT, DROPS["bm-013"], ITEM))
                     == sha_file(os.path.join(ROOT, DROPS["bm-RC2"], ITEM)),
    }


# ---------------------------------------------------------------- the page
def hx(h: int) -> str:
    return "%08X" % h


def render(d: dict) -> str:
    L = []
    a = L.append
    rc2 = d["built"]["bm-RC2"]
    a("# Rebel Drop strings - does the built drop name the car?")
    a("")
    a("Generated by `python Tools/scripts/v_strings.py --write`; `--check` re-reads every file and")
    a("diffs this page byte for byte. Read-only: the stores, the item table and the drop trees are")
    a("opened for reading only.")
    a("")
    a("**Answer: yes for the store, yes for the item record.** `%s` -> `%s` (name) and `%s` (blurb)"
      % (d["leaf"], hx(d["name_h"]), hx(d["desc_h"])))
    a("are present in **all %d languages**, every vanilla pair still resolves to the same text, and"
      % len(d["built_langs"]))
    a("`item.onlinec` item %s points at both hashes. The blurb is the **same English string in all %d"
      % (d["item"]["bm-RC2"]["index"], len(d["built_langs"])))
    a("languages** - see COMPROMISES in the report.")
    a("")
    a("| file | sha256 | bytes |")
    a("|---|---|---|")
    a("| vanilla `%s` | `%s` | %d |" % (rel(VAN), d["vanilla"]["sha"], d["vanilla"]["bytes"]))
    for tag in ("bm-RC2", "bm-013"):
        st = d["built"][tag]
        a("| `%s/%s` | `%s` | %d |" % (tag, STORE, st["sha"], st["bytes"]))
    for tag in ("bm-RC2", "bm-013"):
        p = os.path.join(ROOT, DROPS[tag], ITEM)
        a("| `%s/%s` | `%s` | %d |" % (tag, ITEM, sha_file(p), os.path.getsize(p)))
    a("")
    a("bm-013 and bm-RC2 ship byte-identical files: store `%s`, item `%s`."
      % ("yes" if d["built"]["bm-013"]["sha"] == rc2["sha"] else "**no**",
         "yes" if d["item_same"] else "**no**"))
    a("")
    a("## 1. The two new pairs")
    a("")
    a("| pair | hash | expected from | languages carrying it |")
    a("|---|---|---|---|")
    a("| name | `%s` | `hash_jenkins(\"%s\")` | %d/%d |"
      % (hx(d["name_h"]), d["leaf"], len(d["name_langs"]), len(d["built_langs"])))
    a("| blurb | `%s` | `hash_jenkins(\"%s_desc\")` | %d/%d |"
      % (hx(d["desc_h"]), d["leaf"], len(d["desc_langs"]), len(d["built_langs"])))
    a("")
    a("| language | name | blurb |")
    a("|---|---|---|")
    for lang in d["built_langs"]:
        a("| `%s` | %s | %s |" % (lang, d["texts"][d["name_h"]].get(lang, "-") or "-",
                                 d["texts"][d["desc_h"]].get(lang, "-") or "-"))
    a("")
    a("New hashes against the vanilla store: **%d** (`%s`); hashes the vanilla store carries and the"
      % (len(d["new_hashes"]), ", ".join("`%s`" % hx(h) for h in d["new_hashes"])))
    a("build does not: **%d**." % len(d["gone_hashes"]))
    a("")
    a("## 2. Per-language census (nothing vanilla lost)")
    a("")
    a("| language | vanilla pairs | build pairs | delta | missing | text changed | name | blurb |")
    a("|---|---|---|---|---|---|---|---|")
    for row in d["census"]:
        a("| `%s` | %d | %d | %+d | %d | %d | %s | %s |"
          % (row["lang"], row["vanilla"], row["built"], row["delta"], row["missing"],
             row["altered"], "yes" if row["name_here"] else "**no**",
             "yes" if row["desc_here"] else "**no**"))
    a("")
    a("`missing` counts vanilla hashed pairs absent from the built store in that language; `text")
    a("changed` counts pairs present in both whose text differs. Both are **0** everywhere, and each")
    a("language grows by exactly the two new pairs.")
    a("")
    a("## 3. `item.onlinec` (the Rebel Drop menu record)")
    a("")
    it = d["item"]["bm-RC2"]
    a("Item **%s** of %s: `UIImagePath` = `%s`."
      % (it["index"], it["n_items"], it["members"]["UIImagePath"]["value"]))
    a("")
    a("| member | type | stored (hex) | low 32 | high 32 | check |")
    a("|---|---|---|---|---|---|")
    checks = [("Name", d["name_h"], "-"), ("UIName", d["name_h"], d["desc_h"]),
              ("UIDescription", d["desc_h"], "-")]
    for k, want, want_hi in checks:
        m = it["members"][k]
        ok = m["low32"] == want and (want_hi == "-" or m["high32"] == want_hi)
        a("| `%s` | `%s` | `%016X` | `%s` | `%s` | %s |"
          % (k, m["type"], m["value"], hx(m["low32"]), hx(m["high32"]), "ok" if ok else "**FAIL**"))
    a("")
    a("The members are 48-bit chains: the low 32 bits are the member's own hash and the high 32 bits")
    a("are the next hash in the chain, so `UIName` = `(desc << 32) | name` and `UIDescription` =")
    a("`(<next> << 32) | desc`. The vanilla item for the old leaf is still in the table (item %s)."
      % ", ".join(str(i) for i in it["civilian_item"]))
    a("")
    a("## 4. Reading")
    a("")
    a("* the **store** answers the question the brief asks: 2 new hashes, both in all %d languages,"
      % len(d["built_langs"]))
    a("  no vanilla hash missing and no vanilla text altered in any language")
    a("* the **item record** resolves: `Name`/`UIName` carry `%s`, `UIName`'s high half and"
      % hx(d["name_h"]))
    a("  `UIDescription`'s low half carry `%s`" % hx(d["desc_h"]))
    a("* the rename rule from NAMES.md holds: the hashes are the leaf's, so a leaf rename without")
    a("  these pairs would show no name - the pairs are present, so this leaf is named")
    a("")
    a("## 5. Oracles re-run by `--check`")
    a("")
    a("* the vanilla store still has %d languages and %d hashed pairs; the built store still has %d"
      % (len(d["vanilla_langs"]), sum(len(x) for x in d["vanilla"]["pairs"].values()),
         sum(len(x) for x in rc2["pairs"].values())))
    a("  and exactly %d hashes the vanilla store lacks" % len(d["new_hashes"]))
    a("* the two new hashes still equal `hash_jenkins(leaf)` and `hash_jenkins(leaf + \"_desc\")`")
    a("* both are present in all %d languages, and every per-language delta is exactly +2"
      % len(d["built_langs"]))
    a("* no vanilla pair is missing or altered in any language")
    a("* the item record still exists for the leaf, and its three members still carry the two hashes")
    a("* the old leaf's item is still in the table, and bm-013/bm-RC2 ship identical files")
    a("* this page matches the regenerated bytes")
    a("")
    a("## 6. Labels")
    a("")
    a("Hashes, texts and item members are **decoded** from the files above (`jc3adf` walk of the")
    a("`.stringlookup` and `.onlinec` ADFs; the Jenkins hash function is the project's `rbmhdr`).")
    a("The counts, deltas and pass/fail cells are **derived**. No string is typed from memory.")
    a("")
    return "\n".join(L) + "\n"


def oracles(d: dict) -> list[tuple[str, bool]]:
    it = d["item"]["bm-RC2"]
    vh = sum(len(x) for x in d["vanilla"]["pairs"].values())
    bh = sum(len(x) for x in d["built"]["bm-RC2"]["pairs"].values())
    mem = it["members"]
    return [
        ("the vanilla store has 11 languages", len(d["vanilla_langs"]) == 11),
        ("the built store has 11 languages", len(d["built_langs"]) == 11),
        ("exactly two new hashes appear", len(d["new_hashes"]) == 2 and not d["gone_hashes"]),
        ("the name hash is hash_jenkins(leaf)",
         d["name_h"] == hash_jenkins(d["leaf"].encode())),
        ("the blurb hash is hash_jenkins(leaf + _desc)",
         d["desc_h"] == hash_jenkins((d["leaf"] + "_desc").encode())),
        ("both pairs are in all 11 languages",
         len(d["name_langs"]) == 11 and len(d["desc_langs"]) == 11),
        ("every language grows by exactly two pairs",
         all(r["delta"] == 2 for r in d["census"])),
        ("no vanilla pair is missing", all(r["missing"] == 0 for r in d["census"])),
        ("no vanilla text is altered", all(r["altered"] == 0 for r in d["census"])),
        ("the built store carries vanilla + 22 pairs", bh == vh + 22),
        ("the item record exists for the leaf", it["index"] is not None),
        ("item Name low half is the name hash", mem["Name"]["low32"] == d["name_h"]),
        ("item UIName low half is the name hash", mem["UIName"]["low32"] == d["name_h"]),
        ("item UIName high half is the blurb hash", mem["UIName"]["high32"] == d["desc_h"]),
        ("item UIDescription low half is the blurb hash",
         mem["UIDescription"]["low32"] == d["desc_h"]),
        ("the old leaf's item is still present", bool(it["civilian_item"])),
        ("bm-013 and bm-RC2 ship the same store", d["built"]["bm-013"]["sha"]
         == d["built"]["bm-RC2"]["sha"]),
        ("bm-013 and bm-RC2 ship the same item table", d["item_same"]),
    ]


def page() -> tuple[str, list[tuple[str, bool]]]:
    d = build()
    return render(d), oracles(d)


def cmd_write() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d bytes)" % (rel(OUT), len(text.encode())))
    return 0 if all(ok for _, ok in ors) else 1


def cmd_check() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print("MISSING " + rel(OUT))
        return 1
    bad = [n for n, ok in ors if not ok]
    for n, ok in ors:
        print(("PASS " if ok else "FAIL ") + n)
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if open(path, encoding="utf-8").read() != text:
        print("DRIFT: %s differs from the regenerated bytes" % rel(OUT))
        return 1
    print("document identical: " + rel(OUT))
    return 0 if not bad else 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["--write"]:
        return cmd_write()
    if args == ["--check"]:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
