"""jc3_palette_hash.py - what 0x6187A56B is, and which asset it points at (G3-09 review follow-up).

The review of G3-09 found two 32-bit words side by side in the donor's own `.epe`
(`0x6187A56B` at `0x266`, `0xC023BA54` at `0x26a`) and concluded that `0x6187A56B` is "the
Jenkins hash of `palette`" and `0xC023BA54` the hash of the palette module's VFS path.

This tool tests that reading against the bytes and against every name space the project has:

  1. the two words are located in the `.epe` **inside the archived `.ee`** (the bytes the game
     loads) and in the loose unpacked copy, and the offsets are asserted, not assumed;
  2. `rbmhdr.hash_jenkins` - the archive-path hash, already proved against 78,907 VFS paths -
     is applied to the candidate names that sit *beside* the colour data in the entity: the
     module type word `palette` and the palette module's own path.  Variants (case, NUL,
     extension, leaf-only) are printed to show the recipe is not being fitted;
  3. the `.ee`'s **own SARC directory** is hashed entry by entry: a value word that equals a
     hash of one of the container's own file names is resolved to that file by the container,
     not by a dictionary.  The pair is cross-checked against a second module slot (`damage`)
     whose name hash and value hash are already decoded in the project;
  4. the value is then searched as a raw `u32` and as a hash in every name space that could
     have a reverse table: the 78,907-row VFS index, the 181,740-key JCMR dictionary, all 88
     archive `.tab` files, and every `.epe`/`.ee`/`.vmodc`/`.blo`/`.tab` file under
     `E:/Modding/_gamedata/JC3grab`;
  5. the asset the pair resolves to is decoded (`jc3adf`), and each tint is re-read from its
     own file bytes at `0x94 + 0x50*k` so the table and the bytes are two independent reads.

Everything is read-only: no game process, no build, no edit to another task's files.

Usage
    python Tools/scripts/jc3_palette_hash.py --write
    python Tools/scripts/jc3_palette_hash.py --check
    python Tools/scripts/jc3_palette_hash.py --dump
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
import jc3adf  # noqa: E402
import jc3index  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "PALETTE_HASH.md")
INDEX = os.path.join(OUT, "INDEX.jsonl")
DICTIONARY = os.path.join(ROOT, "Tools", "JCMR-src", "assets", "jc3", "dictionary.json")
GAMEDATA = r"E:/Modding/_gamedata/JC3grab"
GAME = jc3index.DEFAULT_GAME
BUNDLE = bm_rc.DIR + bm_rc.OLD + ".ee"
LOOSE_EPE = os.path.join(
    GAMEDATA,
    "b13b/unpacked/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
    "v0300_car_kensington_sportsmuscle_civilian_01.epe")

# The two words the review reports, in the order they sit in the file.
PAIR_OFF = 0x266
NAME_HASH = 0x6187A56B
VALUE_HASH = 0xC023BA54
# A second, already-decoded module slot in the same `.epe` (B-09: the root `damage` hash).
DAMAGE_NAME_HASH = 0x4F489F01
DAMAGE_VALUE = 670155287

PALETTE_PATH = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
                "modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc")
# Name candidates come from the file names beside the colour data, never from memory.
CANDIDATES = [
    ("module word", "palette"),
    ("module word, capitalised", "Palette"),
    ("module word, upper", "PALETTE"),
    ("module word + extension", "palette.vmodc"),
    ("palette module leaf", "v0300_car_kensington_sportsmuscle_palette"),
    ("palette module leaf + extension", "v0300_car_kensington_sportsmuscle_palette.vmodc"),
    ("palette module path", PALETTE_PATH),
    ("damage module word", "damage"),
]
SCAN_EXT = (".epe", ".ee", ".vmodc", ".blo", ".tab", ".stringlookup")


def words(blob: bytes, value: int) -> list[int]:
    """Every offset of `value` as a little-endian u32."""
    pat = struct.pack("<I", value)
    out, i = [], blob.find(pat)
    while i >= 0:
        out.append(i)
        i = blob.find(pat, i + 1)
    return out


def bundle():
    raw = eetoc.unaaf(bm_rc.vfs(BUNDLE))
    return raw, eetoc.sarc_dir(raw)


def palette_entries(blob: bytes) -> dict:
    """The 10 tint records, decoded with jc3adf (no value is taken from a note)."""
    a = jc3adf.Adf(blob)
    rows = {p: v for p, _t, v in jc3adf.walk(a)}
    tints, i = [], 0
    while f"tints[{i}].name.string" in rows:
        p = f"tints[{i}]"
        tints.append({
            "index": i,
            "name": rows.get(p + ".name.string"),
            "occurrence": rows.get(p + ".occurrence"),
            "rgb": [rows.get(f"{p}.tint_r.{c}") for c in "RGBA"],
            "gloss": rows.get(p + ".specular_gloss"),
            "metallic": rows.get(p + ".metallic"),
            "coat": rows.get(p + ".clear_coat"),
        })
        i += 1
    return {"types": sorted(t["name"] for t in a.types.values()), "total": a.total,
            "instances": len(a.instances), "tints": tints}


def build() -> dict:
    doc: dict = {"bundle": BUNDLE}
    raw, ents = bundle()
    names = [e[0] for e in ents]
    doc["inner_count"] = len(ents)

    # ---- 1. the .epe, from the archive and from the loose copy ----------------------------
    epe_name, epe_off, epe_size = next(e for e in ents if e[0].endswith(".epe"))
    epe = raw[epe_off:epe_off + epe_size]
    doc["epe"] = {"path": epe_name, "bytes": len(epe_size and epe),
                  "sha256": hashlib.sha256(epe).hexdigest()}
    copies = [{"where": "archive (.ee inner SARC)", "bytes": len(epe), "off": epe_off,
               "size": epe_size, "sha256": hashlib.sha256(epe).hexdigest()}]
    if os.path.exists(LOOSE_EPE):
        loose = open(LOOSE_EPE, "rb").read()
        copies.append({"where": "loose unpack (b13b)", "bytes": len(loose), "off": None,
                       "size": None, "sha256": hashlib.sha256(loose).hexdigest()})
    for c in copies:
        blob = epe if c["off"] is not None else open(LOOSE_EPE, "rb").read()
        c["name_word_at"] = words(blob, NAME_HASH)
        c["value_word_at"] = words(blob, VALUE_HASH)
        c["pair_at"] = [o for o in c["name_word_at"]
                        if struct.unpack_from("<I", blob, o + 4)[0] == VALUE_HASH]
    doc["copies"] = copies
    doc["pair_offset"] = copies[0]["pair_at"][0] if copies[0]["pair_at"] else None
    pair_ok = doc["pair_offset"] == PAIR_OFF
    # the raw 12 bytes around the pair, quoted so the reader can check the alignment
    start = PAIR_OFF - 8
    doc["pair_bytes"] = {"from": start, "hex": epe[start:PAIR_OFF + 16].hex(" ")}

    # ---- 2. hash the candidate names ----------------------------------------------------
    cand = []
    for label, name in CANDIDATES:
        h = hash_jenkins(name.encode())
        cand.append({"label": label, "name": name, "hash": h,
                     "is_name": h == NAME_HASH, "is_value": h == VALUE_HASH})
    doc["candidates"] = cand
    name_ok = hash_jenkins(b"palette") == NAME_HASH
    value_ok = hash_jenkins(PALETTE_PATH.encode()) == VALUE_HASH

    # ---- 3. resolve the value against the .ee's own directory ---------------------------
    inner = {}
    for n, o, s in ents:
        inner.setdefault(hash_jenkins(n.encode()), []).append((n, o, s))
    resolved = inner.get(VALUE_HASH, [])
    damage_resolved = inner.get(DAMAGE_VALUE, [])
    doc["inner_resolve"] = {
        "value": [{"name": n, "off": o, "size": s} for n, o, s in resolved],
        "damage": [{"name": n, "off": o, "size": s} for n, o, s in damage_resolved],
    }
    # how many 4-byte words of the .epe name one of the container's own files (the mechanism)
    ref_hits = []
    for o in range(0, len(epe) - 3, 4):
        h = struct.unpack_from("<I", epe, o)[0]
        if h in inner:
            ref_hits.append({"off": o, "hash": h, "name": inner[h][0][0]})
    doc["module_refs"] = ref_hits
    doc["damage_pair"] = {
        "name_at": words(epe, DAMAGE_NAME_HASH),
        "value_at": words(epe, DAMAGE_VALUE)[:4],
        "name_hash_ok": hash_jenkins(b"damage") == DAMAGE_NAME_HASH,
    }

    # ---- 4. every name space that could hold a reverse table ---------------------------
    seen, index_hits = set(), []
    for line in open(INDEX, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        p = r["path"]
        if p in seen:
            continue
        seen.add(p)
        h = hash_jenkins(p.encode())
        if h in (NAME_HASH, VALUE_HASH):
            index_hits.append({"hash": h, "path": p, "archive": r["archive"],
                               "offset": r["offset"], "size": r["size"]})
    doc["index"] = {"paths": len(seen), "hits": index_hits}

    dict_hits = []
    if os.path.exists(DICTIONARY):
        d = json.load(open(DICTIONARY, encoding="utf-8"))
        for p in d:
            h = hash_jenkins(p.encode())
            if h in (NAME_HASH, VALUE_HASH):
                dict_hits.append({"hash": h, "path": p})
        doc["dictionary"] = {"keys": len(d), "hits": dict_hits}

    tabs = sorted(_walk_ext(GAME, (".tab",)))
    tab_hits = []
    for t in tabs:
        try:
            table = jc3index.read_tab(t)
        except SystemExit:
            continue
        for h in (NAME_HASH, VALUE_HASH):
            if h in table:
                off, size = table[h]
                tab_hits.append({"tab": os.path.relpath(t, GAME).replace("\\", "/"),
                                 "hash": h, "offset": off, "size": size})
    doc["tabs"] = {"files": len(tabs), "hits": tab_hits}

    scan, scan_hits = 0, []
    for path in _walk_ext(GAMEDATA, SCAN_EXT):
        try:
            blob = open(path, "rb").read()
        except OSError:
            continue
        scan += 1
        hits = [(h, o) for h in (NAME_HASH, VALUE_HASH) for o in words(blob, h)]
        if hits:
            scan_hits.append({"file": os.path.relpath(path, GAMEDATA).replace("\\", "/"),
                              "bytes": len(blob),
                              "hits": sorted((h, o) for h, o in hits)})
    doc["gamedata"] = {"files": scan, "ext": list(SCAN_EXT),
                       "hits": sorted(scan_hits, key=lambda r: r["file"])}

    # ---- 5. the asset itself -----------------------------------------------------------
    pal = None
    if resolved:
        pname, poff, psize = resolved[0]
        blob = raw[poff:poff + psize]
        pal = palette_entries(blob)
        pal.update({"path": pname, "off": poff, "size": psize,
                    "sha256": hashlib.sha256(blob).hexdigest()})
        # re-read every tint from its own bytes: R at 0x94 + 0x50*k, then A/gloss/metallic/coat
        rows = []
        for k in range(len(pal["tints"])):
            base = 0x94 + 0x50 * k
            vals = struct.unpack_from("<7f", blob, base)
            t = pal["tints"][k]
            rows.append({"index": k, "offset": base,
                         "bytes_rgba_gloss_metallic_coat": list(vals),
                         "matches_adf": (abs(vals[0] - t["rgb"][0]) < 1e-6
                                         and abs(vals[4] - t["gloss"]) < 1e-6
                                         and abs(vals[5] - t["metallic"]) < 1e-6
                                         and abs(vals[6] - t["coat"]) < 1e-6)})
        pal["byte_rows"] = rows
        black = next((t for t in pal["tints"] if t["name"] == "Black"), None)
        pal["black"] = black
        if black is not None:
            b = blob[0x94 + 0x50 * black["index"]:0x94 + 0x50 * black["index"] + 4]
            pal["black_bytes"] = {"offset": 0x94 + 0x50 * black["index"],
                                  "hex": b.hex(" "), "float": struct.unpack("<f", b)[0]}
        pal["metallic_one"] = [t["index"] for t in pal["tints"] if t["metallic"] == 1.0]
    doc["palette"] = pal

    # ---- 6. base rate: random names must not collide with the .epe ---------------------
    rng = random.Random(20261104)
    alphabet = "abcdefghijklmnopqrstuvwxyz_0123456789"
    blobs = {"epe": epe}
    if pal is not None:
        blobs["palette"] = raw[pal["off"]:pal["off"] + pal["size"]]
    rate = {}
    for key, blob in blobs.items():
        hits = 0
        for _ in range(400):
            s = "".join(rng.choice(alphabet) for _ in range(rng.randint(4, 40)))
            hits += len(words(blob, hash_jenkins(s.encode())))
        rate[key] = {"names": 400, "hits": hits, "bytes": len(blob)}
    doc["base_rate"] = rate

    doc["oracles"] = [
        ("the pair sits at 0x266/0x26a in the archived .epe", pair_ok),
        ("both words also occur in the loose unpacked copy at the same relative pair",
         bool(copies[1]["pair_at"]) if len(copies) > 1 else False),
        ("hash_jenkins('palette') == 0x6187A56B", name_ok),
        ("hash_jenkins(<palette module path>) == 0xC023BA54", value_ok),
        ("exactly one name in the candidate table hits the name word",
         sum(1 for c in cand if c["is_name"]) == 1),
        ("the .ee's own directory resolves 0xC023BA54 to the palette module",
         bool(resolved) and resolved[0][0] == PALETTE_PATH),
        ("the same shape resolves the damage slot (0x4F489F01 -> 670155287)",
         bool(damage_resolved) and hash_jenkins(b"damage") == DAMAGE_NAME_HASH),
        ("no VFS index path hashes to either word", not index_hits),
        ("no archive .tab carries either word as a name hash", not tab_hits),
        ("every scanned tint equals its own bytes at 0x94 + 0x50*k",
         pal is not None and all(r["matches_adf"] for r in pal["byte_rows"])),
        ("the palette's ADF header total equals its length",
         pal is not None and pal["total"] == pal["size"]),
        ("400 random names hit neither the .epe nor the palette",
         all(v["hits"] == 0 for v in rate.values())),
    ]
    return doc


def _walk_ext(root: str, exts: tuple[str, ...]):
    for dirpath, _dirs, files in os.walk(root):
        for fn in files:
            if fn.lower().endswith(exts):
                yield os.path.join(dirpath, fn)


# --------------------------------------------------------------------------- render
def _f(v) -> str:
    return "0.000000" if v is None else f"{v:.6f}"


def render(d: dict) -> str:
    p = d["palette"]
    black = p["black"] if p else None
    L: list[str] = []
    a = L.append
    a("# The palette reference in the Serpente entity (G3-09 review follow-up)")
    a("")
    a("The review of G3-09 rejected that card's claim *\"no `.rbm`, `.epe` or `.vmodc` of the "
      "entity names the palette, so the binding is engine-side\"* and pointed at two 32-bit "
      "words in the donor's own `.epe`. This card checks those words in the bytes, names them "
      "with the project's own hash function, resolves the one that is a path hash, and decodes "
      "the asset. Nothing was launched, built, or written outside this card's files.")
    a("")
    a("## 1. Answer")
    a("")
    a("**`0x6187A56B` is not the palette.** It is `hash_jenkins(\"palette\")`, the *name* of the "
      "module slot; the word immediately after it, **`0xC023BA54`, is the asset reference**: "
      "`hash_jenkins` of the palette module's full VFS path. The asset is")
    a("")
    a("```")
    a(PALETTE_PATH)
    a("```")
    a("")
    a(f"a **{p['size'] if p else 0}-byte ADF v4** file holding the vehicle's "
      f"{len(p['tints']) if p else 0} tint records.")
    if black:
        a("")
        a(f"`Black` is entry {black['index']}: RGB ({_f(black['rgb'][0])}, {_f(black['rgb'][1])}, "
          f"{_f(black['rgb'][2])}) with gloss {_f(black['gloss'])}, metallic "
          f"{_f(black['metallic'])}, coat {_f(black['coat'])} - `0.2` per channel, stored as a "
          "float in the file.")
    a("")
    a("So the pairing the review found is real, but its label needs one correction: the palette "
      "*hash* is `0xC023BA54` (the value); `0x6187A56B` is the hash of the word `palette`, i.e. "
      "the key the entity files its palette module under. Both statements are decoded below.")
    a("")
    a("## 2. Verifying the offset in the actual `.epe` bytes")
    a("")
    a(f"The `.epe` is the one **inside the archived `.ee`** (`{d['epe']['path']}`, "
      f"{d['epe']['bytes']} B, sha256 `{d['epe']['sha256'][:16]}…`), read through `bm_rc.vfs` + "
      f"`eetoc.unaaf` + `eetoc.sarc_dir`; a loose unpacked copy is checked as a second witness.")
    a("")
    a("| copy | bytes | `0x6187A56B` at | `0xC023BA54` at | adjacent pair |")
    a("|---|---:|---|---|---|")
    for c in d["copies"]:
        a(f"| {c['where']} | {c['bytes']} | "
          f"{', '.join(hex(x) for x in c['name_word_at']) or 'absent'} | "
          f"{', '.join(hex(x) for x in c['value_word_at']) or 'absent'} | "
          f"{', '.join(hex(x) for x in c['pair_at']) or 'absent'} |")
    a("")
    a(f"Bytes around the pair (from `{hex(d['pair_bytes']['from'])}`):")
    a("")
    a("```")
    a(d["pair_bytes"]["hex"])
    a("```")
    a("")
    once = all(len(c["name_word_at"]) == 1 and len(c["value_word_at"]) == 1
               for c in d["copies"] if c["off"] is not None)
    a(("Each word occurs exactly once in that file and the two are adjacent, in that order, so "
       "the pair is one record rather than two coincidences: a `u32` pair at "
       f"`{hex(d['pair_offset']) if d['pair_offset'] is not None else '?'}`.")
      if once else
      "The words are not unique in that file; the offsets above are every occurrence and the "
      "pair is the adjacent one.")
    a("")
    a("## 3. Naming the words with `hash_jenkins`")
    a("")
    a("`rbmhdr.hash_jenkins` is Gibbed's `StringHelpers.HashJenkins` ported byte for byte; "
      "`jc3index.py` uses it to name archive `.tab` entries and it is the same function "
      "`MODLOG` records as matching 78,907 VFS paths. Candidates are the module word and the "
      "file names beside the colour data - no name was taken from memory.")
    a("")
    a("| label | string | `hash_jenkins` | is the name word | is the value word |")
    a("|---|---|---|---|---|")
    for c in d["candidates"]:
        nm = c["name"] if len(c["name"]) <= 62 else c["name"][:59] + "…"
        a(f"| {c['label']} | `{nm}` | `{c['hash']:08X}` | "
          f"{'**yes**' if c['is_name'] else ''} | {'**yes**' if c['is_value'] else ''} |")
    a("")
    a("Exactly one candidate hits each word, and the nearest variants (capitalised, upper, "
      "with `.vmodc`, leaf only) miss - the recipe is not being fitted to the target.")
    a("")
    a("## 4. Resolved by the `.ee`'s own directory, not by a table")
    a("")
    a(f"The vehicle's `.ee` contains {d['inner_count']} inner files. Hashing each of their names "
      "and looking the two words up resolves the *value* word to a file the container actually "
      "ships:")
    a("")
    a("| lookup | hash | inner file | offset | size |")
    a("|---|---|---|---:|---:|")
    for r in d["inner_resolve"]["value"]:
        a(f"| value word | `0x{VALUE_HASH:08X}` | `{r['name']}` | {r['off']} | {r['size']} |")
    for r in d["inner_resolve"]["damage"]:
        a(f"| damage slot | `{DAMAGE_VALUE}` | `{r['name']}` | {r['off']} | {r['size']} |")
    a("")
    a(f"The second slot is the control: `0x{DAMAGE_NAME_HASH:08X}` is "
      f"`hash_jenkins(\"damage\")` ({'match' if d['damage_pair']['name_hash_ok'] else 'MISMATCH'}) "
      "and its value resolves the same way, so the record shape is *(module name hash, module "
      "path hash)*, exactly as `MODLOG`/B-09 describe the root `damage` hash. The file the "
      "`damage` slot names is the shared health module `lave_health_medium.vmodc`, i.e. the "
      "entity's damage model.")
    a("")
    refs = d["module_refs"]
    by_mod: dict[str, list[int]] = {}
    for r in refs:
        by_mod.setdefault(r["name"].rsplit("/", 1)[-1], []).append(r["off"])
    a(f"Scanning every 4-byte word of the `.epe` against the container's name hashes resolves "
      f"**{len(refs)}** module references across **{len(by_mod)}** distinct files - the "
      "mechanism is not a one-off. Counted per file, first offset shown:")
    a("")
    a("| module file | refs | first offset |")
    a("|---|---:|---|")
    for nm, offs in sorted(by_mod.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        a(f"| `{nm}` | {len(offs)} | `{hex(min(offs))}` |")
    a("")
    a("## 5. Where the two words are **not** (every name space searched)")
    a("")
    a("| space | size | `0x6187A56B` | `0xC023BA54` |")
    a("|---|---:|---:|---:|")
    a(f"| VFS index (`INDEX.jsonl`, unique paths) | {d['index']['paths']} | "
      f"{sum(1 for h in d['index']['hits'] if h['hash'] == NAME_HASH)} | "
      f"{sum(1 for h in d['index']['hits'] if h['hash'] == VALUE_HASH)} |")
    if "dictionary" in d:
        a(f"| JCMR dictionary (`dictionary.json`, keys) | {d['dictionary']['keys']} | "
          f"{sum(1 for h in d['dictionary']['hits'] if h['hash'] == NAME_HASH)} | "
          f"{sum(1 for h in d['dictionary']['hits'] if h['hash'] == VALUE_HASH)} |")
    a(f"| archive `.tab` name tables | {d['tabs']['files']} files | "
      f"{sum(1 for h in d['tabs']['hits'] if h['hash'] == NAME_HASH)} | "
      f"{sum(1 for h in d['tabs']['hits'] if h['hash'] == VALUE_HASH)} |")
    a(f"| `_gamedata/JC3grab` raw `.epe`/`.ee`/`.vmodc`/`.blo`/`.tab`/`.stringlookup` | "
      f"{d['gamedata']['files']} files | "
      f"{sum(1 for r in d['gamedata']['hits'] for h, _o in r['hits'] if h == NAME_HASH)} | "
      f"{sum(1 for r in d['gamedata']['hits'] for h, _o in r['hits'] if h == VALUE_HASH)} |")
    a("")
    a("The zeroes are the finding, not a gap: the palette module is **packed inside the "
      "vehicle's own `.ee`**, so no archive `.tab` and no index row can name it. The value "
      "resolves only by recipe (hashing the path) and by the container's own directory - which "
      "is exactly how the engine finds it, since JC3 addresses by hash.")
    a("")
    a("Raw `u32` hits under `_gamedata/JC3grab` (offsets are in the hit file):")
    a("")
    a("| file | bytes | hits |")
    a("|---|---:|---|")
    for r in d["gamedata"]["hits"]:
        hs = ", ".join(f"`0x{h:08X}`@{hex(o)}" for h, o in r["hits"])
        a(f"| `{r['file']}` | {r['bytes']} | {hs} |")
    a("")
    a("Two further copies under `_gamedata/JC3grab/rc_merge` (this project's build staging) carry "
      "the name word at `0x296` followed by `0x4EDB05EF`, not the palette path hash. They are "
      "merged-graph variants and this card does not interpret them.")
    a("")
    a(f"Base rate: 400 random 4-40 character names produce "
      f"{d['base_rate']['epe']['hits']} hits in the {d['base_rate']['epe']['bytes']}-byte `.epe` "
      f"and {d['base_rate'].get('palette', {}).get('hits', 0)} in the palette, so the matches "
      "above are not what random 32-bit words do in these files.")
    a("")
    a("## 6. The asset, decoded")
    a("")
    if p:
        a(f"`{p['path']}` - **{p['size']} B**, sha256 `{p['sha256'][:16]}…`, ADF v4, "
          f"header total {p['total']} (equals its length), {p['instances']} instance, types "
          f"`{'`, `'.join(p['types'])}`.")
        a("")
        a("| # | name | occurrence | R = G = B | A | gloss | metallic | coat |")
        a("|---:|---|---:|---|---:|---:|---:|---:|")
        for t in p["tints"]:
            a(f"| {t['index']} | {t['name']} | {int(t['occurrence'])} | "
              f"({_f(t['rgb'][0])}, {_f(t['rgb'][1])}, {_f(t['rgb'][2])}) | "
              f"{_f(t['rgb'][3])} | {_f(t['gloss'])} | {_f(t['metallic'])} | {_f(t['coat'])} |")
        a("")
        if black:
            a(f"**JC3 `Black` is entry {black['index']}**: `tint_r/g/b` "
              f"({_f(black['rgb'][0])}, {_f(black['rgb'][1])}, {_f(black['rgb'][2])}), and the "
              f"four bytes at `{hex(p['black_bytes']['offset'])}` are "
              f"`{p['black_bytes']['hex']}` = `{p['black_bytes']['float']:.8f}f`, i.e. **0.2** "
              "stored as a float - the value is in the file, not inferred.")
            a("")
        a("Byte check - each record re-read from its own `0x94 + 0x50*k` (7 floats: R, G, B, A, "
          "gloss, metallic, coat) and compared with the ADF walk:")
        a("")
        a("| # | offset | floats from bytes | equals ADF |")
        a("|---:|---|---|---|")
        for r in p["byte_rows"]:
            v = ", ".join(f"{x:.6f}" for x in r["bytes_rgba_gloss_metallic_coat"])
            a(f"| {r['index']} | `{hex(r['offset'])}` | {v} | {'yes' if r['matches_adf'] else 'NO'} |")
        a("")
        a(f"`metallic = 1.0` in records {', '.join(str(i) for i in p['metallic_one'])} "
          f"({len(p['metallic_one'])} of {len(p['tints'])}) - the number the review counted, "
          "re-read here from the bytes.")
        a("")
    else:
        a("The value word did not resolve to a file inside the container, so no asset could be "
          "decoded. Every place searched is in section 5.")
    a("")
    a("## 7. Claims in `COLOUR.md` that this refutes")
    a("")
    a("`COLOUR.md` was not edited. These are the statements the bytes above contradict, with the "
      "part of that file they live in:")
    a("")
    a("| # | `COLOUR.md` says | measured |")
    a("|---|---|---|")
    a("| 1 | §4: *\"No `.rbm`, `.epe` or `.vmodc` of the entity names the palette, so the "
      "binding is engine-side (spawn/vehicle-system), not an asset reference.\"* | the entity's "
      "own `.epe` carries `hash_jenkins(\"palette\")` followed by the palette module's path "
      "hash at `0x266`; the palette **is** an asset reference of the entity |")
    a("| 2 | §6 UNKNOWN 2: *\"The palette -> block binding is not in any of the 566 files.\"* | "
      "it is in the `.epe`, one of those 566 files; the ASCII scan used to test it cannot see a "
      "hash by construction |")
    a("| 3 | §4/check 9: *\"no file in the bundle references the palette except the palette "
      "itself\"* | the check asserts the false statement, so `--check` passing does not cover it |")
    a("| 4 | §4: *\"the five 'metallic' tints\"* | eight records carry `metallic = 1.0` "
      f"({len(p['metallic_one']) if p else '?'} of {len(p['tints']) if p else '?'}); that card's "
      "own table is right and its prose is not |")
    a("| 5 | §4/check 11: *\"77 floats … for the 10 tints plus the palette root's own default "
      "record\"* | the seven `palette.*` offsets are the seven `tints[9].*` offsets; there is no "
      "11th record (the file declares one instance) |")
    a("| 6 | §5 prose: *\"no file in JC3's index is named for … a time of day\"* | that card's "
      "own table counts `time_of_day` = 2 (`msub_time_of_day.gdc`/`.gsc`) |")
    a("| 7 | §5 table rows `sky` 3,364 / `sun` 31 as lighting evidence | substring counts whose "
      "own examples are false positives (`…_skyshield_…`, `…_boatsunk_…`) |")
    a("")
    a("One correction to the review itself, for the record: it gives the `.epe` as 109,526 B, "
      "which is the **archive** size; the loose unpacked copy under `_gamedata/b13b` is "
      f"{d['copies'][1]['bytes'] if len(d['copies']) > 1 else '?'} B. The pair is at `0x266` in "
      "both, so the finding stands, but the two files are not the same bytes.")
    a("")
    a("## 8. Oracles")
    a("")
    a("Each line is recomputed from the source bytes by `--check`; the document is only written "
      "when all pass.")
    a("")
    for label, ok in d["oracles"]:
        a(f"- **{'PASS' if ok else 'FAIL'}** {label}")
    a("")
    a("## 9. What is still UNKNOWN")
    a("")
    a("1. **Which tint the engine selects for a given spawn, and whether it copies that tint "
      "into the CarPaintMM dynamic float4s.** The `.epe` says *which palette module* the entity "
      "uses; it carries no selected index, and the palette's `occurrence` field is 100 for every "
      "record. The coupling to the block lives in the render/material code, not in these files. "
      "Tried: the `.epe` property table (one int per module slot, no index), the palette bytes "
      "(no selector), and the dynamic payload of the paint blocks (`COLOUR.md` §1, identical on "
      "blocks 6/7/8).")
    a("2. **The 0.2/0.45 relationship.** `Black` is `(0.2, 0.2, 0.2)` with gloss 0 / metallic 0 "
      "/ coat 1; the paint blocks' own override triple is `(0.4, 1, 1)`. No file maps one to the "
      "other, so no write-back is claimed.")
    a("3. **Whether other vehicles use the same palette path hash.** This card checks one "
      "entity. A fleet-wide census of `(palette name hash, value hash)` pairs across all vehicle "
      "`.epe` files is a separate measurement and is not claimed here.")
    a("")
    a("## 10. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/jc3_palette_hash.py --write")
    a("python Tools/scripts/jc3_palette_hash.py --check")
    a("```")
    a("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_const", dest="mode", const="write")
    g.add_argument("--check", action="store_const", dest="mode", const="check")
    g.add_argument("--dump", action="store_const", dest="mode", const="dump")
    args = ap.parse_args()
    doc = build()
    text = render(doc)
    bad = [label for label, ok in doc["oracles"] if not ok]
    if args.mode == "dump":
        print(json.dumps({k: v for k, v in doc.items() if k != "oracles"}, indent=1, default=str)[:20000])
        return 0
    if args.mode == "write":
        if bad:
            print("REFUSING to write, failing oracles:", bad)
            return 2
        os.makedirs(os.path.dirname(MD), exist_ok=True)
        open(MD, "w", encoding="utf-8", newline="\n").write(text)
        print(f"wrote {MD}")
        print(f"  name word 0x{NAME_HASH:08X} at 0x{doc['pair_offset']:x}"
              if doc["pair_offset"] is not None else "  pair not found")
        print(f"  value word 0x{VALUE_HASH:08X} -> "
              f"{doc['inner_resolve']['value'][0]['name'] if doc['inner_resolve']['value'] else 'UNRESOLVED'}")
        print(f"  palette {doc['palette']['size'] if doc['palette'] else 0} B, "
              f"{len(doc['palette']['tints']) if doc['palette'] else 0} tints")
        print(f"  oracles {sum(1 for _, ok in doc['oracles'] if ok)}/{len(doc['oracles'])}")
        return 0
    # check
    if not os.path.exists(MD):
        print("no document to check:", MD)
        return 2
    cur = open(MD, encoding="utf-8", newline="").read()
    if bad:
        print("FAIL oracles:", bad)
        return 1
    if cur.replace("\r\n", "\n") != text:
        import difflib
        diff = list(difflib.unified_diff(cur.replace("\r\n", "\n").splitlines(),
                                         text.splitlines(), "on disk", "recomputed", n=2))
        print("FAIL md differs from a fresh decode:")
        print("\n".join(diff[:60]))
        return 1
    print(f"OK {sum(1 for _, ok in doc['oracles'] if ok)}/{len(doc['oracles'])} oracles, "
          f"{doc['palette']['size']} B palette, {len(doc['palette']['tints'])} tints, md byte-identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
