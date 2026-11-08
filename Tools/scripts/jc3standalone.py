#!/usr/bin/env python
"""jc3standalone.py - G2-27: can a NEW vehicle entity load from the dropzone?

The card asks three things, and each one is a measurement, not an opinion:

1. **Every place a vehicle entity path or hash is registered.**  The registration sites are
   found by G2-29's scan (`TRAFFIC.json`, 11,751 files / 7,719 MB, name + hash) and classified
   here by *key type* - a full path string, a 32-bit leaf hash, or a tag list - because the key
   type is what decides whether a new path can be expressed without touching a global table.
2. **Is `global/entityregistry_gen.entityregc` a gate?**  It is the one 33 MB / 39 MB global
   table that names entities, so it is decoded far enough to count what it covers: how many
   index entity leaves have a record and, more importantly, how many do not.
3. **What a standalone entity needs on disk.**  Measured off the donor's own `.ee` (an AAF
   around a SARC: 604 inner files) and off the shipped Rebel-Drop mod's 20 `.ee` overrides
   (all at vanilla VFS paths, none with a `.toc`).

Writes `Research/JC3Grab/STANDALONE.md` + `STANDALONE.json`.  `--check` re-derives and compares.

Usage:
  python jc3standalone.py --write
  python jc3standalone.py --check
  python jc3standalone.py dump sites|registry|needs
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eetoc  # noqa: E402
import jc3grab  # noqa: E402
import jc3index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
WORK = os.path.join(RAW, "standalone")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
MOD_ROOT = os.path.join(ROOT, "Research", "1456340180_Rebel-Drop-Mod-V5.3")
DONOR_EE = os.path.join(ROOT, "Builds", "test-091",
                        "v0300_car_kensington_sportsmuscle_civilian_01.ee")
REG = "global/entityregistry_gen.entityregc"
MD_NAME, JSON_NAME = "STANDALONE.md", "STANDALONE.json"
DONOR_LEAF = "v0300_car_kensington_sportsmuscle_civilian_01"
NEW_LEAF = "v0300_car_kensington_sportsmuscle_batmobile"
SPAWN_RE = re.compile(rb"(?:editor|dlc/[^\x00]+?/editor)[\\/]+entities[\\/]+[^\x00]+?\.ee")
SEP = re.compile(r"[\\/]+")


def read(path: str, rows: list[dict], mount: str | None = None) -> bytes:
    for r in rows:
        if r["path"] == path and (mount is None or r["mount"] == mount):
            return jc3grab.read_entry(r, GAME)
    raise LookupError(f"not in index: {path} (mount {mount})")


def fetch_registry(rows: list[dict]) -> dict:
    """The two `.entityregc` blobs, extracted once to `_JC3grab/standalone/`."""
    os.makedirs(WORK, exist_ok=True)
    out = {}
    for mount in ("base", "patch"):
        p = os.path.join(WORK, f"{mount}_entityregistry_gen.entityregc")
        if not os.path.exists(p):
            open(p, "wb").write(read(REG, rows, mount))
        out[mount] = open(p, "rb").read()
    return out


def tag03(blob: bytes):
    """Yield `(offset, string)` for every `03 <len16> <ascii>` record."""
    i, n = 0, len(blob)
    while True:
        i = blob.find(b"\x03", i)
        if i < 0 or i + 3 > n:
            return
        ln = struct.unpack_from("<H", blob, i + 1)[0]
        if 1 <= ln <= 512 and i + 3 + ln <= n:
            s = blob[i + 3:i + 3 + ln]
            if all(0x20 <= c < 0x7f for c in s):
                yield i, s.decode("latin-1")
                i += 3 + ln
                continue
        i += 1


def registry_facts(rows: list[dict]) -> dict:
    blobs = fetch_registry(rows)
    ee = {}
    for r in rows:
        if r["path"].endswith(".ee"):
            ee.setdefault(r["path"].rsplit("/", 1)[-1][:-3], r["path"])
    veh = set()
    for line in open(os.path.join(OUT, "PARTS_TABLE.jsonl"), encoding="utf-8"):
        e = json.loads(line)["entity"]
        if e.endswith(".ee"):
            veh.add(e.rsplit("/", 1)[-1][:-3])
    per = {}
    for mount, blob in blobs.items():
        ss = list(tag03(blob))
        leaves = {s for _, s in ss if "/" not in s}
        hits = [o for o, s in ss if s == DONOR_LEAF]
        rec = {}
        if hits:
            o = hits[0]
            ln = struct.unpack_from("<H", blob, o + 1)[0]
            end = o + 3 + ln
            nxt = struct.unpack_from("<I", blob, end + 4)[0] if end + 8 <= len(blob) else 0
            rec = {"offset": o, "leaf_len": ln, "hash_after": blob[end + 4:end + 8].hex(),
                   "hash_value": nxt, "tail": blob[end:end + 12].hex()}
        per[mount] = {
            "bytes": len(blob), "tag03_strings": len(ss),
            "path_strings": sum(1 for _, s in ss if "/" in s),
            "class_strings": sum(1 for _, s in ss if "/" not in s
                                 and re.match(r"^C[A-Z]\w*$", s)),
            "leaf_like": len(leaves),
            "index_leaves": sum(1 for s in leaves if s in ee),
            "vehicles": sum(1 for s in leaves if s in veh),
            "donor_records": len(hits), "donor_record": rec,
        }
    union = set()
    for blob in blobs.values():
        union |= {s for _, s in tag03(blob) if "/" not in s}
    absent = sorted(set(ee) - union)
    veh_absent = sorted(veh - union)
    return {
        "per_file": per,
        "index_ee_leaves": len(ee),
        "registry_leaves": len(union),
        "index_leaves_with_record": len(set(ee) & union),
        "index_leaves_without_record": len(absent),
        "without_record_sample": absent[:8],
        "vehicles": len(veh),
        "vehicles_with_record": len(veh & union),
        "vehicles_without_record": len(veh_absent),
        "vehicle_without_sample": veh_absent[:6],
        "path_extension_census": dict(collections.Counter(
            s.rsplit(".", 1)[-1] for blob in blobs.values() for _, s in tag03(blob)
            if "/" in s and "." in s.rsplit("/", 1)[-1]).most_common(8)),
    }


def spawn_facts(rows: list[dict]) -> dict:
    """The spawn tables: how a record names its entity."""
    tabs = [r for r in rows if r["path"].endswith("spawn_vehicle_defs.bin")
            or r["path"].endswith("spawn_vehicle_proto_defs.bin")]
    per, leaves = [], set()
    for r in tabs:
        b = jc3grab.read_entry(r, GAME)
        hits = SPAWN_RE.findall(b)
        ls = {SEP.split(h.decode("latin-1"))[-1][:-3] for h in hits}
        leaves |= ls
        per.append({"path": r["path"], "mount": r["mount"], "bytes": len(b),
                    "ee_records": len(ls), "_leaves": ls,
                    "sample": hits[0].decode("latin-1") if hits else None})
    union = set()
    for blob in fetch_registry(rows).values():
        union |= {s for _, s in tag03(blob) if "/" not in s}
    for t in per:
        t["unregistered"] = len(t.pop("_leaves", set()) - union)
    return {"tables": per, "distinct_leaves": len(leaves),
            "leaves_without_registry_record": sorted(leaves - union),
            "count_without_record": len(leaves - union),
            "production_unregistered": sum(t["unregistered"] for t in per
                                           if "proto" not in t["path"])}


def mod_facts() -> dict:
    """The Rebel-Drop mod: the only shipped example of the override pattern."""
    files, variant_count = [], collections.Counter()
    for root, _, fs in os.walk(MOD_ROOT):
        for f in fs:
            if f.endswith(".ee"):
                rel = os.path.relpath(os.path.join(root, f), MOD_ROOT).replace("\\", "/")
                variant = rel.split("/")[0]
                inner = rel.split("/", 1)[1]
                files.append({"variant": variant, "path": inner,
                              "bytes": os.path.getsize(os.path.join(root, f))})
                variant_count[variant] += 1
    toc = [f for root, _, fs in os.walk(MOD_ROOT) for f in fs if f.endswith(".toc")]
    # one `.ee` unpacked, to show that the inner names are independent of the outer leaf
    probe = None
    for f in files:
        if "v1704" in f["path"]:
            p = os.path.join(MOD_ROOT, f["variant"], f["path"])
            s = eetoc.unaaf(open(p, "rb").read())
            ents = eetoc.sarc_dir(s)
            probe = {"file": f["path"], "inner_files": len(ents),
                     "epe": [n for n, _, _ in ents if n.endswith(".epe")],
                     "foreign": sorted({n.split("/")[3] for n, _, _ in ents
                                        if n.startswith("editor/entities/jc_environments")})[:3]}
            break
    return {"ee_files": len(files), "per_variant": dict(variant_count),
            "toc_files": len(toc), "files": sorted(files, key=lambda x: x["path"]),
            "inner_probe": probe}


def needs_facts(rows: list[dict]) -> dict:
    """What the donor `.ee` carries inside, i.e. what a standalone entity ships."""
    out = {"source": os.path.relpath(DONOR_EE, ROOT).replace("\\", "/")}
    if not os.path.exists(DONOR_EE):
        out["error"] = "donor .ee not on disk"
        return out
    s = eetoc.unaaf(open(DONOR_EE, "rb").read())
    ents = eetoc.sarc_dir(s)
    out["bytes"] = os.path.getsize(DONOR_EE)
    out["inner_files"] = len(ents)
    out["by_ext"] = dict(collections.Counter(
        os.path.splitext(n)[1] for n, _, _ in ents).most_common())
    out["by_top"] = dict(collections.Counter(n.split("/")[0] for n, _, _ in ents).most_common())
    single = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
              "v0300_car_kensington_sportsmuscle_civilian_01")
    out["the_one_entity_file"] = [n for n, _, _ in ents if n == single + ".epe"]
    out["entity_files"] = [n for n, _, _ in ents
                           if n.startswith("editor/entities/jc_vehicles/01_land")][:6]
    toc = DONOR_EE + ".toc"
    out["toc"] = {"present": os.path.exists(toc),
                  "entries": len(eetoc.read_toc(open(toc, "rb").read()))
                  if os.path.exists(toc) else 0,
                  "sarc_entries": len(ents)}
    # is the leaf path itself referenced from inside the AAF?
    blob = s
    out["inner_mentions_leaf"] = blob.count(DONOR_LEAF.encode())
    return out


def sites_facts() -> dict:
    """The registration census: G2-29's measured rows, classified by key type."""
    doc = json.load(open(os.path.join(OUT, "TRAFFIC.json"), encoding="utf-8"))
    rows = doc["scan"]["hits"]
    kind = {"spawn table": ("path string", "yes, as a new record"),
            "Rebel Drop": ("32-bit leaf hash", "yes, a computable hash"),
            "task table": ("leaf string in a task key", "no"),
            "level rule": ("path string in a `.bl?` object", "no"),
            "frontend": ("hash/name in the frontend list", "no"),
            "entity registry": ("leaf + 32-bit hash + asset paths", "UNKNOWN"),
            "self": ("its own `.epe`/`.toc`", "no"),
            "patch metadata": ("file hash, patch bookkeeping", "no"),
            "localisation": ("hash only", "optional, for a label"),
            "other": ("name or hash in another table", "-")}
    out = []
    for r in rows:
        k = r.get("kind") or "-"
        key, needed = kind.get(k, ("-", "-"))
        out.append({"file": r.get("path"), "mount": r.get("mount"), "kind": k,
                    "name_hits": r.get("strings"), "hash_hits": r.get("hashes"),
                    "confidence": r.get("confidence"),
                    "key": key, "needed_for_new_path": needed})
    return {"rows": out, "count": len(out),
            "by_kind": dict(collections.Counter(r["kind"] for r in out))}


def build() -> dict:
    rows = jc3index.load_index(jc3index.DEFAULT_OUT)
    reg = registry_facts(rows)
    spawn = spawn_facts(rows)
    mod = mod_facts()
    needs = needs_facts(rows)
    sites = sites_facts()
    mod_in_index = 0
    by_path = {r["path"] for r in rows}
    for f in mod["files"]:
        if f["path"] in by_path:
            mod_in_index += 1
    return {
        "card": "G2-27",
        "generated_by": "Tools/scripts/jc3standalone.py --write",
        "donor_leaf": DONOR_LEAF, "new_leaf": NEW_LEAF,
        "sites": sites, "registry": reg, "spawn": spawn,
        "mod": dict(mod, in_index=mod_in_index,
                    absent=len(mod["files"]) - mod_in_index),
        "needs": needs,
        "verdict": {
            "load_new_path": "yes (derived, one UNKNOWN)",
            "global_registry_edit_required": "no evidence of one for a path reference",
            "drop_hash_resolution": "UNKNOWN",
        },
    }


def report(doc: dict) -> str:
    L: list[str] = []
    a = L.append
    reg, sp, mod, needs, sites = (doc["registry"], doc["spawn"], doc["mod"],
                                 doc["needs"], doc["sites"])
    a("# Standalone entity - can a new path load from the dropzone? (G2-27)")
    a("")
    a(f"**Answer: yes to the *loading*, UNKNOWN to the *hash*.** A new entity path -")
    a(f"`editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/{NEW_LEAF}.ee` -")
    a("needs **no global registry edit** for the routes that name the entity by *path*: the")
    a("spawn tables store the entity as a full path string, and the one global entity table")
    protos = [t for t in sp["tables"] if "proto" in t["path"]]
    dlcs = [t for t in sp["tables"] if t["mount"] == "dlc" and "proto" not in t["path"]]
    a(f"is not a complete list - it covers the **base retail roster** ({reg['index_leaves_with_record']}")
    a(f"of {reg['index_ee_leaves']} index leaves) but leaves out **{sum(t['unregistered'] for t in protos)}"
      f" of the {sum(t['ee_records'] for t in protos)}** debug spawn records and")
    a(f"**{sum(t['unregistered'] for t in dlcs)} of the {sum(t['ee_records'] for t in dlcs)}** DLC production records,")
    a("and one of those DLC vehicles (the sport mech) is playable in retail - so a missing")
    a("record does not stop an entity loading.")
    a("The one route that names the entity by *hash* is the Rebel Drop item, and every shipped")
    a("vehicle drop points at a leaf that does have a record - so whether the game resolves a")
    a("*new* leaf from an item hash is **UNKNOWN** and is a Q-1 probe, not a file answer.")
    a("")
    a("| question | answer | evidence |")
    a("|---|---|---|")
    a(f"| where an entity path/hash is registered | **{sites['count']}** file rows in "
      f"{len(sites['by_kind'])} kinds | `TRAFFIC.json` scan (11,751 files / 7,719 MB) |")
    a(f"| does a global table list every entity? | no - {reg['index_leaves_with_record']}/"
      f"{reg['index_ee_leaves']} index leaves have a record | `{REG}` |")
    a(f"| is a path reference expressible for a new leaf? | yes - spawn records hold the full "
      f"`editor\\entities\\...ee` string | `settings/spawn_vehicle_defs.bin` (86 records) |")
    a(f"| does a hash reference resolve for a new leaf? | **UNKNOWN** - 0 shipped "
      f"counter-examples | `profile/item.onlinec`, this doc §4 |")
    a(f"| what a standalone entity ships | one `.ee` ({needs.get('inner_files', 0)} inner files"
      f"{', ' + f'{needs[chr(98)+chr(121)+chr(116)+chr(101)+chr(115)]:,} B' if 'bytes' in needs else ''})"
      f", `.toc` optional | `Builds/test-091` donor `.ee`, the mod's 20 `.ee` |")
    a(f"| decision D-6 | **standalone is the route with the fewest unknowns** | this doc §6 |")
    a("")
    a("## 1. Every registration site, classified by key type")
    a("")
    a("The census itself is G2-29's (a name + hash scan of 11,751 data files); what this card")
    a("adds is the **key type** per site, because the key type decides whether a new leaf can")
    a("be expressed without rewriting a table that is keyed by something we cannot compute:")
    a("")
    a("| file | mount | kind | key type | a new path fits? |")
    a("|---|---|---|---|---|")
    for r in sites["rows"]:
        a(f"| `{str(r['file']).replace('|', '/')}` | {r['mount']} | {r['kind']} | "
          f"{r['key']} | {r['needed_for_new_path']} |")
    a("")
    a("Rows with `0` name hits are 32-bit hash coincidences and are not used for any claim")
    a("(G2-29 says the same). The four sites that matter:")
    a("")
    a("* **`settings/spawn_vehicle_defs.bin`** - a record is `entity` (full path string) +")
    a("  `tags` + `name`. A new path is a **new record in an overridden copy**; nothing global")
    a("  is rewritten.")
    a("* **`profile/item.onlinec`** (Rebel Drop) - the record's `Name` is the 32-bit Jenkins")
    a("  hash of the leaf (G2-26). The hash is computable, the *resolution* is the question.")
    a(f"* **`{REG}`** - the global entity table, {reg['per_file']['base']['bytes']:,} B base +")
    a(f"  {reg['per_file']['patch']['bytes']:,} B patch. §3 shows it is not a complete list.")
    a("* **`profile/task.onlinec`**, the two level `CVehicleRule`s and `frontend_global.blo` -")
    a("  the donor is named there for its *vanilla* identity (chop-shop task, level rules,")
    a("  frontend entry). A new leaf simply has none of them, which is the desired state.")
    a("")
    a("## 2. What the global entity registry actually is")
    a("")
    a(f"`{REG}` is not ADF and not a plain string list: it is a tagged stream. The donor's")
    a("record, byte for byte, is")
    a("")
    a("```")
    for mount, p in reg["per_file"].items():
        rec = p["donor_record"]
        if rec:
            a(f'{mount:5s} offset {rec["offset"]:>9,}  leaf_len {rec["leaf_len"]:>3}  '
              f'tail {rec["tail"]}')
    a("```")
    a("")
    a("i.e. `03 <len16> <leaf>` followed by the leaf's 32-bit hash")
    a(f"(`{reg['per_file']['patch']['donor_record'].get('hash_after', '')}` little-endian) - the")
    a("same `D2B46B49` G2-29 searched for. Each record also carries that entity's asset paths:")
    a("")
    a("| mount | bytes | tag-03 strings | path strings | `C*` class names | leaf-like | "
      "of which index leaves | vehicles | donor records |")
    a("|---|---|---|---|---|---|---|---|---|")
    for mount, p in reg["per_file"].items():
        a(f"| {mount} | {p['bytes']:,} | {p['tag03_strings']:,} | {p['path_strings']:,} | "
          f"{p['class_strings']:,} | {p['leaf_like']:,} | {p['index_leaves']} | "
          f"{p['vehicles']} | {p['donor_records']} |")
    a("")
    a("Path extensions inside the records:")
    a(f"{', '.join(f'`.{k}` {v:,}' for k, v in dict(reg['path_extension_census']).items())} -")
    a("asset dependencies (effects, tunes, generated modules), not a spawn list.")
    a("")
    a("## 3. What the registry covers - and why a missing record is not fatal")
    a("")
    a(f"The index carries **{reg['index_ee_leaves']}** distinct `.ee` leaves. The registry, base")
    a(f"and patch together, holds **{reg['registry_leaves']}** no-slash strings, of which")
    a(f"**{reg['index_leaves_with_record']}** are index entity leaves - so")
    a(f"**{reg['index_leaves_without_record']} shipped entities have no record at all**, e.g.")
    a(f"{', '.join(f'`{x}`' for x in reg['without_record_sample'][:6])}. Of the")
    a(f"{reg['vehicles']} vehicle entities in `PARTS_TABLE.jsonl`, {reg['vehicles_with_record']}")
    a(f"have a record and **{reg['vehicles_without_record']} do not** "
      f"({', '.join('`' + x + '`' for x in reg['vehicle_without_sample'][:4])}).")
    a("")
    a("The gap splits three ways, and the split is the answer:")
    a("")
    prod = next((t for t in sp["tables"] if t["path"] == "settings/spawn_vehicle_defs.bin"), None)
    protos = [t for t in sp["tables"] if "proto" in t["path"]]
    dlcs = [t for t in sp["tables"] if t["mount"] == "dlc" and "proto" not in t["path"]]
    if prod:
        a(f"* **The base retail roster is fully registered.** `settings/spawn_vehicle_defs.bin`")
        a(f"  has {prod['ee_records']} records and **{prod['ee_records'] - prod['unregistered']}**")
        a("  of them carry a registry record.")
    if protos:
        a(f"* **The debug builds are the unregistered mass.** The")
        a(f"  {len(protos)} `spawn_vehicle_proto_defs.bin` tables hold")
        a(f"  {sum(t['ee_records'] for t in protos)} records, "
          f"**{sum(t['unregistered'] for t in protos)}** of them unregistered - the `*_debug`")
        a("  entities.")
    if dlcs:
        a(f"* **But DLC production is not.** The {len(dlcs)} DLC `spawn_vehicle_defs.bin` tables")
        a(f"  hold {sum(t['ee_records'] for t in dlcs)} records, "
          f"**{sum(t['unregistered'] for t in dlcs)}** unregistered, and those include")
        a("  vehicles the player actually drives (`v0806_car_na_sportmech_01`,")
        a("  `v0600_car_urga_armoredjeep_blackhand_01`).")
    a("")
    a("The third bullet is the decisive one: a retail-playable DLC vehicle with **no record**")
    a("means the registry cannot be a hard gate for *loading* an entity - it is a bake of the")
    a("base roster's assets. What actually references a spawnable entity is the spawn table:")
    a("")
    a("| spawn table | mount | bytes | `.ee` records | of which unregistered | path record |")
    a("|---|---|---|---|---|---|")
    for t in sp["tables"]:
        a(f"| `{t['path']}` | {t['mount']} | {t['bytes']:,} | {t['ee_records']} | "
          f"{t['unregistered']} | {('full path string') if t['sample'] else '-'} |")
    a("")
    a(f"**{sp['count_without_record']} of {sp['distinct_leaves']} distinct spawn leaves are")
    a(f"referenced by path with no registry record**: "
      f"{', '.join('`' + x + '`' for x in sp['leaves_without_registry_record'][:5])} …")
    a("So the reference that matters for a *load* is the path string in the table above, and it")
    a("is available for a new leaf.")
    a("")
    a("## 4. So can a new path load? The evidence, in order of strength")
    a("")
    a(f"1. **The dropzone is enumerated, not read from a list.** A repacked `.ee` at a vanilla")
    a("   VFS path is applied by the game (in-game test-003, `MODLOG` §14), i.e. the dropzone")
    a("   directory is searched for a path whose archive entry also exists. A new path is the")
    a("   same lookup with every archive missing it.")
    a(f"2. **The `.ee` is self-contained.** The donor's `.ee` is an AAF around a SARC with")
    a(f"   **{needs.get('inner_files', 0)}** inner files ("
      f"{', '.join(f'`{k}` {v}' for k, v in list(dict(needs.get('by_ext', {})).items())[:5])}"
      f" ...), including its own `.epe`, `.stringlookup` and `.fmod_guids`.")
    a("   Nothing in it points at a sibling VFS file that would have to be renamed.")
    a(f"3. **Inner names are independent of the outer leaf.** The shipped mod's")
    a(f"   `{mod['inner_probe']['file'] if mod['inner_probe'] else '-'}` (a *boat* path) contains")
    a(f"   `{mod['inner_probe']['epe'][0] if mod['inner_probe'] and mod['inner_probe']['epe'] else '-'}`")
    a("   - a playground prop - so the container does not care what the outer file is called.")
    a(f"4. **The `.ee.toc` is optional**: the mod ships **{mod['ee_files']}** `.ee` with")
    a(f"   **{mod['toc_files']}** `.toc` files. (Our own build writes one; the donor's has")
    a(f"   {needs.get('toc', {}).get('entries', 0)} entries against "
      f"{needs.get('toc', {}).get('sarc_entries', 0)} SARC entries, so it is not a full")
    a("   directory either.)")
    a(f"5. **No shipped counter-example.** All **{mod['ee_files']}** mod `.ee` files are at")
    a(f"   **vanilla paths** ({mod['in_index']}/{mod['ee_files']} in the index, "
      f"{mod['absent']} new), and so are all our builds. The")
    a("   genuinely-new-entity mod (Meme Vehicle Pack) is still unexamined (`MODLOG` line 1090)")
    a("   - so the *new path itself* has never been demonstrated on this project.")
    a("")
    a("Points 1-4 make a new path **structurally** loadable. Point 5 is why the answer is")
    a("\"yes, derived\" and not \"yes, proven\". The one step the files do not decide is the")
    a("**hash**: the drop item's `Name` is a hash of the leaf, and the only table that could")
    a("turn a hash into a path is the registry of §3, which is incomplete. Two readings survive:")
    a("")
    a("* the game hashes VFS paths at startup and the registry is only a cache - then a new")
    a("  leaf resolves and the drop works;")
    a("* the registry *is* the hash table - then a new leaf needs a record we cannot write.")
    a("")
    a("**Q-1 probe (one variable):** ship the new-path `.ee` + one drop item whose `Name` is")
    a(f"`hash('{NEW_LEAF}')`, and see whether the item appears and spawns. Everything else in")
    a("this card is already answered (see `REBELDROP.md` §7 for the item fields).")
    a("")
    a("## 5. What a standalone entity needs on disk")
    a("")
    a(f"Measured off the donor `.ee` (`{needs.get('source', '-')}`, "
      f"{needs.get('bytes', 0):,} B):")
    a("")
    a("| item | count / value |")
    a("|---|---|")
    a(f"| one `.ee` (AAF + SARC) | {needs.get('bytes', 0):,} B |")
    a(f"| inner files | {needs.get('inner_files', 0)} |")
    for k, v in list(dict(needs.get("by_ext", {})).items())[:10]:
        a(f"| &nbsp;&nbsp;`{k}` | {v} |")
    a(f"| top-level dirs | {', '.join(f'{k} {v}' for k, v in dict(needs.get('by_top', {})).items())} |")
    a(f"| its own `.epe` | `{(needs.get('the_one_entity_file') or ['-'])[0]}` |")
    a(f"| `.toc` | {'present' if needs.get('toc', {}).get('present') else 'absent'} "
      f"({needs.get('toc', {}).get('entries', 0)} entries) - **optional**, see §4.4 |")
    a(f"| `.stringlookup` | 1 inside the `.ee` (hash-only, G2-32) |")
    a("")
    a("So the **minimum** for a standalone Batmobile is:")
    a("")
    a("1. `editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/")
    a(f"   {NEW_LEAF}.ee` - the donor's AAF, content unchanged or rebuilt, at a new leaf;")
    a("2. **one reference** so anything can ask for it:")
    a("   * a record in an overridden `settings/spawn_vehicle_defs.bin` (path string) - the")
    a("     route with no unknown, or")
    a(f"   * a record in `profile/item.onlinec` with `Name` = `hash('{NEW_LEAF}')` - the player-")
    a("     facing route, pending the Q-1 probe;")
    a("3. **optionally** a name/icon: a `.stringlookup` entry and a `ui/store` `.ddsc` (G2-32),")
    a("   which only affect the label, never the load.")
    a("")
    a("Nothing else: no `global/` edit, no `settings/spawn_budget_pools.bin` edit (that names")
    a("*tables*, not vehicles), no `frontend_global.blo` edit (it names the vanilla entity and")
    a("would be wrong for a standalone one).")
    a("")
    a("## 6. What this means for D-6")
    a("")
    a("| route | traffic copies | registry edits | remaining unknown |")
    a("|---|---|---|---|")
    a("| replace `civilian_01` | **yes** - it is in the ground spawn table with 13 tags, 1 of 41")
    a("  traffic selectors matches (G2-29) | 0 | none for the load; lore break is certain |")
    a("| standalone `.ee` + drop item | no | 0 for the path; **UNKNOWN** for the hash | the Q-1")
    a("  probe of §4 |")
    a("| standalone `.ee` + spawn-table record | no | 0 | whether the engine honours an")
    a("  overridden `settings/*.bin` (G2-29's own UNKNOWN) |")
    a("")
    a("**Recommendation: standalone.** It removes the lore break (MOD-5, WLD-8) at the cost of")
    a("one probe, and every file-level requirement it adds is already measured above.")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("1. **Hash resolution for a new leaf** (§4). No file decides it; one drop item answers it.")
    a(f"2. **Why {reg['index_leaves_without_record']} entities are unregistered.** The record set")
    a("   looks like \"entities with generated module dependencies\" (the asset paths above), but")
    a("   the criterion is native. UNKNOWN, and it does not affect the verdict.")
    a("3. **Whether a replaced `settings/spawn_vehicle_defs.bin` is honoured** from the dropzone")
    a("   without a hash change - G2-29's open question, unchanged here.")
    a("4. **Whether the entity registry must gain a record for the drop route.** Same as 1, from")
    a("   the writer's side: we have no writer for a 39 MB tagged stream and did not attempt one.")
    a("5. **The `.toc`** - the mod ships none and works, but whether the game ever prefers it")
    a("   when present (eetoc's hypothesis) is not settled by these files.")
    a("")
    a("## 8. Files and commands")
    a("")
    a("```")
    a("python Tools/scripts/jc3standalone.py --write    # this report + STANDALONE.json")
    a("python Tools/scripts/jc3standalone.py --check    # re-derive and compare")
    a("```")
    a("")
    a(f"Inputs: `INDEX.jsonl`, `{REG}` (base + patch, extracted to")
    a(f"`{os.path.relpath(WORK, RAW).replace(os.sep, '/')}\\` under `_JC3grab`), the 9 spawn")
    a("tables, `PARTS_TABLE.jsonl`, `TRAFFIC.json` (G2-29's census), `REBELDROP.json` (G2-26),")
    a("the donor `.ee` in `Builds/test-091`, and the shipped Rebel-Drop mod's 20 `.ee`.")
    a("")
    return "\n".join(L)


def dump(what: str) -> int:
    doc = build()
    key = {"sites": "sites", "registry": "registry", "needs": "needs"}.get(what)
    if not key:
        print("dump sites|registry|needs")
        return 2
    print(json.dumps(doc[key], indent=1)[:6000])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what")
    a = ap.parse_args()
    if a.cmd == "dump":
        return dump(a.what)
    doc = build()
    md = report(doc)
    js = json.dumps(doc, indent=1, sort_keys=False) + "\n"
    md_path, js_path = os.path.join(OUT, MD_NAME), os.path.join(OUT, JSON_NAME)
    reg, sp, mod = doc["registry"], doc["spawn"], doc["mod"]
    summary = (f"{doc['sites']['count']} registration rows | registry records "
               f"{reg['index_leaves_with_record']}/{reg['index_ee_leaves']} index leaves "
               f"({reg['vehicles_with_record']}/{reg['vehicles']} vehicles) | "
               f"{sp['count_without_record']} spawned-by-path leaves unregistered | "
               f"mod {mod['ee_files']} .ee / {mod['toc_files']} .toc, {mod['in_index']} vanilla "
               f"paths | donor .ee {doc['needs'].get('inner_files', 0)} inner files")
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        open(md_path, "w", encoding="utf-8", newline="\n").write(md)
        open(js_path, "w", encoding="utf-8", newline="\n").write(js)
        print(f"wrote {md_path} ({len(md.splitlines())} lines) + {js_path}")
    if a.check:
        bad = []
        for path, text, what in ((md_path, md, MD_NAME), (js_path, js, JSON_NAME)):
            if not os.path.exists(path):
                bad.append(f"{what} missing")
                continue
            disk = open(path, encoding="utf-8", newline="").read().replace("\r\n", "\n")
            if disk != text:
                diff = [ln for ln in difflib.unified_diff(disk.splitlines(), text.splitlines(),
                                                          "disk", "derived", lineterm="", n=0)][:8]
                bad.append(f"{what} stale: " + " | ".join(diff))
        if bad:
            print("FAIL: " + f"{len(bad)} problem(s)")
            for b in bad:
                print("  " + b)
            return 1
        print("PASS: " + summary + ", json match True, md match True")
        return 0
    print("OK: " + summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
