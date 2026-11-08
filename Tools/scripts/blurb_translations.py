#!/usr/bin/env python
"""blurb_translations.py - proposed Rebel Drop blurb translations for the new car.

`Builds/bm-RC2/verify/strings.md` and `strings_languages.md` show the new car's blurb is the
**same English sentence in all 11 languages** while every vanilla vehicle blurb is translated.
This script does not touch the build. It:

  * reads the English blurb out of the built store at `hash_jenkins(leaf + "_desc")`;
  * reads three vanilla vehicle blurbs in all 11 languages, for register and length;
  * measures the vanilla maximum characters per language over every vehicle blurb present in
    all 11 lanes - that maximum is the length budget a proposal must fit;
  * records a machine-written proposal per non-English language, each labelled
    "machine-written proposal, needs native review";
  * checks the hash side: the pair key is `hash_jenkins(<leaf> + "_desc")`, so it is a property
    of the leaf, not of the text - the proposals all sit under the same hash, unchanged, in all
    11 lanes.

Read-only on the vanilla store and the build's store (`profile/online.stringlookup`); only the
two documents under `Working/Translation/` are written.

Usage:
  uv run python Tools/scripts/blurb_translations.py --write
  uv run python Tools/scripts/blurb_translations.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import v_strings_languages as V  # noqa: E402  load_store / text_at / LANG_ORDER
from rbmhdr import hash_jenkins  # noqa: E402

MASK = 0xFFFFFFFF
LEAF = "v0300_car_kensington_sportsmuscle_debug"
NAME_HASH = 0x60A5E7A4
BLURB_HASH = 0xF34BA8E8
LABEL = "machine-written proposal, needs native review"

# Three vanilla blurbs: a sports car (speed), a light tank (weapons + armour) and an armed
# helicopter (speed + weapons) - the three registers the Batmobile blurb mixes.
VANILLA_SAMPLES = [
    ("v0300_car_kensington_sportsmuscle_civilian_01", "sports car"),
    ("v0603_car_urga_smalltank_rebel_01", "light assault tank"),
    ("v2200_helicopter_capstone_assault_rebel_01", "assault helicopter"),
]

# Machine-written, no native reviewer has seen these. Proper names (Arkham Knight, Batmobile)
# stay in Latin script, as the vanilla prose keeps Kerner/Capstone/Urga.
PROPOSALS = {
    "en": "Arkham Knight's armoured Batmobile: pursuit speed, a battle-mode turret, and armour "
          "that shrugs off small arms.",
    "fr": "La Batmobile blindée d'Arkham Knight : vitesse de poursuite, une tourelle en mode "
          "combat et un blindage qui ignore les armes légères.",
    "de": "Das gepanzerte Batmobile von Arkham Knight: Verfolgungsgeschwindigkeit, ein Turm für "
          "den Kampfmodus und eine Panzerung, die Kleinwaffen abprallen lässt.",
    "it": "La Batmobile corazzata di Arkham Knight: velocità di inseguimento, una torretta in "
          "modalità combattimento e una corazza che respinge le armi leggere.",
    "es": "El Batmobile blindado de Arkham Knight: velocidad de persecución, una torreta en modo "
          "combate y un blindaje que resiste las armas ligeras.",
    "ru": "Бронированный Batmobile от Arkham Knight: скорость погони, турель в боевом режиме и "
          "броня, выдерживающая попадания стрелкового оружия.",
    "pl": "Opancerzony Batmobile Arkham Knight: prędkość pościgu, wieża w trybie bojowym i "
          "pancerz odporny na broń krótką.",
    "ja": "Arkham Knightの装甲Batmobile。追跡速度、バトルモードのターレット、小火器を寄せ付けない装甲を備える",
    "pt": "O Batmobile blindado de Arkham Knight: velocidade de perseguição, uma torreta em modo "
          "de combate e uma blindagem que resiste a armas ligeiras.",
    "es-MX": "El Batmobile blindado de Arkham Knight: velocidad de persecución, una torreta en "
             "modo combate y un blindaje que aguanta las armas ligeras.",
    "ar": "تتميز Batmobile المدرعة الخاصة بـArkham Knight بسرعة المطاردة، وبرج في وضع القتال، "
          "وتدريع يقاوم الأسلحة الخفيفة.",
}
NON_ENGLISH = [l for l in V.LANG_ORDER if l != "en"]

OUT_MD = os.path.join(ROOT, "Working", "Translation", "BLURB_TRANSLATIONS.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "BLURB_TRANSLATIONS.json")


def lane_text(store: dict, lang_index: int, h: int) -> str | None:
    return V.text_at(store["text"], store["pairs"][lang_index].get(h))


def all_languages(store: dict, h: int) -> dict:
    return {V.LANG_ORDER[i]: lane_text(store, i, h) for i in sorted(store["pairs"])}


def budgets(vanilla: dict) -> tuple[dict, int]:
    """Max characters per language over every vehicle blurb present in all 11 lanes."""
    keys = [hash_jenkins((leaf + "_desc").encode()) & MASK for leaf in V.load_vehicle_leaves()]
    maxima = {l: 0 for l in V.LANG_ORDER}
    counted = 0
    for h in keys:
        texts = all_languages(vanilla, h)
        if any(texts.get(l) is None for l in V.LANG_ORDER):
            continue
        counted += 1
        for l in V.LANG_ORDER:
            maxima[l] = max(maxima[l], len(texts[l]))
    return maxima, counted


def build() -> dict:
    vanilla = V.load_store(V.VAN)
    built = V.load_store(V.BUILT)
    maxima, counted = budgets(vanilla)

    english = lane_text(built, 0, BLURB_HASH)
    samples = []
    for leaf, kind in VANILLA_SAMPLES:
        h = hash_jenkins((leaf + "_desc").encode()) & MASK
        samples.append({"leaf": leaf, "kind": kind, "hash": h,
                        "texts": all_languages(vanilla, h)})

    pair_key = hash_jenkins((LEAF + "_desc").encode()) & MASK
    name_key = hash_jenkins(LEAF.encode()) & MASK
    lanes = {}
    for i in sorted(built["pairs"]):
        off = built["pairs"][i].get(BLURB_HASH)
        lanes[V.LANG_ORDER[i]] = {
            "hash_present": off is not None,
            "text_offset": off,
            "current_text": V.text_at(built["text"], off) if off is not None else None,
        }

    rows = []
    for lang in V.LANG_ORDER:
        text = PROPOSALS[lang]
        rows.append({
            "language": lang,
            "label": LABEL,
            "hash": f"{BLURB_HASH:08X}",
            "hash_unchanged": (hash_jenkins((LEAF + "_desc").encode()) & MASK) == BLURB_HASH,
            "chars": len(text),
            "max_vanilla_chars": maxima[lang],
            "fits": len(text) <= maxima[lang],
            "utf8_bytes": len(text.encode("utf-8")),
            "text": text,
            "vanilla_example_chars": None,
        })
        # what the same content costs in the closest vanilla sample, for context
        sample_len = samples[0]["texts"].get(lang)
        rows[-1]["vanilla_example_chars"] = len(sample_len) if sample_len else None

    return {
        "card": "Rebel Drop blurb translations (machine-written proposals)",
        "label": LABEL,
        "source": {
            "built_store": V.BUILT,
            "vanilla_store": V.VAN,
            "leaf": LEAF,
            "name_hash": f"{NAME_HASH:08X}",
            "blurb_hash": f"{BLURB_HASH:08X}",
            "pair_key_recomputed": f"{pair_key:08X}",
            "leaf_name_key_recomputed": f"{name_key:08X}",
            "english": english,
            "english_chars": len(english) if english else 0,
            "lanes": lanes,
            "lanes_carrying_the_same_english": sum(
                1 for v in lanes.values() if v["current_text"] == english),
        },
        "vanilla": {
            "blurbs_in_all_11_lanes": counted,
            "max_chars": maxima,
            "samples": samples,
        },
        "proposals": rows,
    }


def to_md(p: dict) -> str:
    s, v = p["source"], p["vanilla"]
    out = []
    w = out.append
    w("# Rebel Drop blurb - proposed translations for the 10 non-English languages")
    w("")
    w(f"**Every translation below is a {p['label']}.** No native speaker has reviewed any of them;")
    w("they are written to match the vanilla register decoded from the store, nothing more.")
    w("")
    w(f"Generated by `Tools/scripts/blurb_translations.py`; `--check` re-reads both stores and")
    w(f"rebuilds this page byte for byte. The build is **not** modified - only read.")
    w("")
    w("## 1. The English source")
    w("")
    w(f"> {s['english']}")
    w("")
    w(f"- {s['english_chars']} characters, key `{s['blurb_hash']}` = "
      f"`hash_jenkins(\"{s['leaf']}_desc\")` (recomputed: `{s['pair_key_recomputed']}`).")
    w(f"- the name key `{s['name_hash']}` recomputes as `{s['leaf_name_key_recomputed']}`.")
    w(f"- the built store carries this **same English string in "
      f"{s['lanes_carrying_the_same_english']}/11** lanes - the abnormality "
      "`strings_languages.md` measured.")
    w("")
    w("## 2. Vanilla register: three blurbs in all 11 languages")
    w("")
    w(f"Vehicle blurbs present in all 11 vanilla lanes: **{v['blurbs_in_all_11_lanes']}**. Three are")
    w("quoted in full so the tone and length can be compared directly. Vanilla blurbs are one or")
    w("two declarative sentences, third person, no marketing exclamation; they name the make/model,")
    w("list capability with a colon or \"and\", and close on a concrete spec (turret calibre, missile")
    w("type, top speed). Non-English runs longer than English in most languages - French, German,")
    w("Italian, Polish and Russian especially - while Japanese is far shorter (a compact form with")
    w("no spaces and no terminal period) and Spanish sits close to the English length.")
    w("")
    for smp in v["samples"]:
        w(f"### {smp['kind']} - `{smp['leaf']}` (key `{smp['hash']:08X}`)")
        w("")
        w("| lang | chars | text |")
        w("|---|---|---|")
        for lang in V.LANG_ORDER:
            t = smp["texts"].get(lang) or ""
            w(f"| `{lang}` | {len(t)} | {t} |")
        w("")
    w("## 3. Proposed translations")
    w("")
    w("| lang | max vanilla chars | proposal chars | fits | translation (machine-written proposal, needs native review) |")
    w("|---|---|---|---|---|")
    for r in p["proposals"]:
        w(f"| `{r['language']}` | {r['max_vanilla_chars']} | {r['chars']} | "
          f"{'yes' if r['fits'] else '**NO**'} | {r['text']} |")
    w("")
    w("`en` is the shipped string, repeated unchanged so the row set is complete. The ten")
    w("non-English rows are proposals.")
    w("")
    w("## 4. Key and length checks")
    w("")
    w("The store keys are **leaf-derived**, not text-derived: a pair's `Hash` is")
    w("`hash_jenkins(<leaf> + \"_desc\")`, and the text is bytes at a `TextOffset`. Replacing the")
    w("text therefore cannot move the key - and the proposals are filed under the same key in")
    w("every lane, which is what the vanilla store does too (one hash, 11 lane offsets).")
    w("")
    w("| lang | key | key recomputes | max vanilla chars | proposal chars | within budget |")
    w("|---|---|---|---|---|---|")
    for r in p["proposals"]:
        w(f"| `{r['language']}` | `{r['hash']}` | {'yes' if r['hash_unchanged'] else '**NO**'} | "
          f"{r['max_vanilla_chars']} | {r['chars']} | {'yes' if r['fits'] else '**NO**'} |")
    w("")
    w("Length budget = the longest vanilla vehicle blurb **in that language** (per-language, because")
    w("German/Russian/Polish run longer than English and Japanese runs shorter).")
    w("")
    w("## 5. What this does not settle")
    w("")
    w("- **Register inside each language is a judgement, not a decode.** No file says whether")
    w("  \"battle mode\" should be a borrowed English term, a marketing phrase, or a literal one;")
    w("  the proposals pick the reading closest to the three vanilla samples.")
    w("- **`Batmobile` and `Arkham Knight` are left in Latin script**, matching vanilla prose that")
    w("  keeps `Kerner`, `Capstone` and `Urga` untranslated. Whether the localisation team would")
    w("  transliterate them (e.g. `Бэтмобиль`) is UNKNOWN - no file has that decision. The name")
    w("  pair itself is `BATMOBILE` in all 11 lanes, so the blurb is the only place a transliteration")
    w("  could appear.")
    w("- **Gender/case of the proper noun** (`La Batmobile`, `Das Batmobile`) follows common usage in")
    w("  each language; no vanilla string names a Batmobile, so there is no in-file oracle.")
    w("- The length budget is the vanilla maximum, not an engine limit. The store's text blob is")
    w("  NUL-separated with per-string offsets, so a longer string would still fit the format.")
    w("")
    return "\n".join(out)


def to_json(p: dict) -> str:
    return json.dumps(p, ensure_ascii=False, indent=1) + "\n"


def write() -> None:
    p = build()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_md(p))
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(to_json(p))
    print(f"wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.basename(OUT_JSON)}")
    print(f"{len(p['proposals'])} rows, {p['source']['lanes_carrying_the_same_english']}/11 lanes "
          "still carrying the English string")


def check() -> None:
    p = build()
    bad = 0

    def ok(cond: bool, msg: str) -> None:
        nonlocal bad
        print(f"{'PASS' if cond else 'FAIL'} {msg}")
        bad += not cond

    s, v = p["source"], p["vanilla"]
    ok(bool(s["english"]) and s["english_chars"] == 111,
       f"English blurb read from the built store ({s['english_chars']} chars)")
    ok(s["lanes_carrying_the_same_english"] == 11,
       "all 11 lanes still carry the same English string (the thing being fixed)")
    ok(s["pair_key_recomputed"] == s["blurb_hash"] == "F34BA8E8",
       f"blurb key = hash_jenkins(leaf_desc) = {s['pair_key_recomputed']}")
    ok(s["leaf_name_key_recomputed"] == s["name_hash"] == "60A5E7A4",
       f"name key = hash_jenkins(leaf) = {s['leaf_name_key_recomputed']}")
    ok(all(l["hash_present"] for l in s["lanes"].values()),
       "the blurb key is present in all 11 lanes of the built store")
    ok(v["blurbs_in_all_11_lanes"] > 0, f"{v['blurbs_in_all_11_lanes']} vanilla blurbs set the budget")
    ok(all(len(smp["texts"].get(l) or "") > 0 for smp in v["samples"] for l in V.LANG_ORDER),
       "the three vanilla samples resolve in all 11 languages")
    ok(set(PROPOSALS) == set(V.LANG_ORDER), "one proposal per language lane")
    ok(all(r["hash_unchanged"] for r in p["proposals"]),
       "every proposal sits under the unchanged key F34BA8E8")
    ok(all(r["fits"] for r in p["proposals"]),
       "every proposal fits the per-language vanilla maximum")
    ok(all("\x00" not in r["text"] for r in p["proposals"]),
       "no proposal contains a NUL (would truncate the store's text blob)")
    ok(PROPOSALS["en"] == s["english"], "the en row is the shipped English string, unchanged")
    ok(all(r["label"] == LABEL for r in p["proposals"]),
       "every row carries the machine-written label")

    with open(OUT_MD, encoding="utf-8") as f:
        same_md = f.read() == to_md(p)
    with open(OUT_JSON, encoding="utf-8") as f:
        same_json = f.read() == to_json(p)
    ok(same_md, f"{os.path.relpath(OUT_MD, ROOT)} re-derives byte for byte")
    ok(same_json, f"{os.path.basename(OUT_JSON)} re-derives byte for byte")
    print(f"{'PASS' if not bad else 'FAIL'}: blurb translations {bad} failure(s)")
    raise SystemExit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    write() if a.write else check()


if __name__ == "__main__":
    main()
