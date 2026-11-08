#!/usr/bin/env python
"""jc3traffic.py - G2-29: every spawn site for the donor, and whether AI drives it there.

Reads the archive index (`Research/JC3Grab/INDEX.jsonl`) and the archives **read-only**, then:

1. scans every index entry whose extension is a data/registry/script type (tier A) and every
   level/level-logic/entity-module (tier B) for the donor's entity path, name and 32-bit path
   hash, so "which files can spawn it" is a census and not an opinion;
2. parses `settings/spawn_vehicle_defs.bin` (and every other `spawn_*_defs.bin`, base/patch/DLC)
   into records - spawn pool key, entity path, tag list, entity name - and prints the donor's own
   record with its tags;
3. parses the traffic-rule block of `global/global.blo`: rule names, the tag lists they select on,
   the driver seats and the AI behaviour trees they spawn, then tests the donor's tag list against
   every selector in that file (required tags present, `-tag` exclusions absent);
4. records the other spawn sites that name the donor: the Rebel Drop item (`profile/item.onlinec`),
   the chop-shop task (`profile/task.onlinec`), level `CVehicleRule` objects and the frontend list.

Writes Research/JC3Grab/TRAFFIC.md + TRAFFIC.json. `--check` rebuilds and asserts; `--fast` skips
the tier-B scan (levels/entities, ~7 GB) and says so in the output.

Usage:
  python jc3traffic.py --write
  python jc3traffic.py --check
  python jc3traffic.py --check --fast
  python jc3traffic.py dump records|rules|hits|profile
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
sys.path.insert(0, HERE)
import jc3grab  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

JSON_NAME = "TRAFFIC.json"
MD_NAME = "TRAFFIC.md"
INDEX = os.path.join(OUT, "INDEX.jsonl")
GAME = os.environ.get("JC3_GAME", jc3grab.DEFAULT_GAME)

DONOR_NAME = "v0300_car_kensington_sportsmuscle_civilian_01"
DONOR_DIR = "v0300_car_kensington_sportsmuscle"
SPAWN_FILE = "settings/spawn_vehicle_defs.bin"
RULES_FILE = "global/global.blo"

# Tier A: data / registry / script containers - cheap, and the only place a spawn list can live.
SCAN_A = (".bin", ".onlinec", ".gsc", ".gdc", ".btc", ".entityregc", ".stringlookup", ".epe",
          ".toc", ".vmodc", ".physicsc", ".gadfc", ".mdic", ".wtunec", ".ctunec", ".effc",
          ".pfxc", ".trim", ".lua", ".defc", ".pfs", ".revolutionc", ".destc")
# Tier B: levels, level logic and entity modules - where a *placed* car would be named.
SCAN_B = (".bl", ".blo", ".ee")
PRINTABLE = re.compile(rb"[\x20-\x7e]{3,}")
TAG_SPLIT = re.compile(r"[,\s]+")
# A spawn-pool key is a `word|word|word` string whose first word is a real word. Random binary also
# contains `|`, so `9|Y` would otherwise pass (it did, in the first run).
GROUP_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,}(?:\|[A-Za-z0-9_]+)+$")
# Rule names in global.blo: `<n>[b]_CamelCase` for the numbered civilian rules, or anything ending
# in `Rule`/`Rule<n>` (faction rules). The numbered ones carry no "Rule" suffix in the game's data.
RULE_RE = re.compile(r"^(?:\d\d[b]?_[A-Za-z0-9]+|[A-Za-z0-9_]*TrafficRule\d*)$")
OTHER_RULE_RE = re.compile(r"^[A-Za-z0-9_]*Rule\d*$")


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def digest(data: bytes) -> dict:
    return {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def strings(data: bytes) -> list[tuple[int, str]]:
    """Printable runs with offsets; leading `P` pad bytes (4-byte string alignment) stripped."""
    out = []
    for m in PRINTABLE.finditer(data):
        off, s = m.start(), m.group().decode("latin-1")
        while off % 4 and s.startswith("P") and ("|" in s or s[1:].startswith("editor")):
            off, s = off + 1, s[1:]
        out.append((off, s))
    return out


def resolved(path: str, rows: list[dict]) -> dict:
    row = jc3grab.resolve(path, rows)
    if row is None:
        raise SystemExit(f"FAIL: {path} not in the index")
    return row


# ---------------------------------------------------------------- spawn tables
def spawn_records(data: bytes) -> list[dict]:
    """Every `path -> tags -> name` record, grouped by the nearest preceding `a|b|c` pool key."""
    ss = strings(data)
    recs: list[dict] = []
    group = ""  # a key belongs to the record that follows it, then it is spent
    for i, (off, s) in enumerate(ss):
        if GROUP_RE.fullmatch(s) and not s.endswith(".ee"):
            group = s
            continue
        if not s.endswith(".ee") or "entities" not in s:
            continue
        base = os.path.basename(s.replace("\\", "/"))[:-3]
        tags: list[str] = []
        name = ""
        for j in (i + 1, i + 2):
            if j >= len(ss):
                break
            if ss[j][1] == base:
                name = base
                tags = [t for t in TAG_SPLIT.split(" ".join(x for _, x in ss[i + 1:j])) if t]
                break
        recs.append({"group": group, "path": s.replace("\\", "/"), "name": name or base,
                     "tags": tags, "offset": off})
        group = ""
    return recs


def parse_spawn_files(rows: list[dict]) -> dict:
    files = []
    for row in rows:
        b = os.path.basename(row["path"])
        if b.startswith("spawn_") and b.endswith("_defs.bin"):
            files.append(row)
    tables = {}
    for row in files:
        data = jc3grab.read_entry(row, GAME)
        recs = spawn_records(data)
        tables[row["path"]] = {
            "path": row["path"], "mount": row["mount"], "size": row["size"],
            "records": len(recs),
            "groups": sorted({r["group"] for r in recs if r["group"]}),
            "v0300": [{"name": r["name"], "tags": r["tags"], "group": r["group"],
                       "path": r["path"], "offset": r["offset"]}
                      for r in recs if r["name"].startswith("v0300_")],
            "digest": digest(data),
        }
    return tables


def main_table(tables: dict) -> dict:
    """The ground-vehicle table the player's traffic comes from, resolved base vs patch."""
    rows = [t for p, t in tables.items() if p == SPAWN_FILE]
    if not rows:
        raise SystemExit(f"FAIL: {SPAWN_FILE} missing from the index")
    return rows[0]


# ---------------------------------------------------------------- traffic rules
def rules_from(blo: bytes, vocab: set[str]) -> dict:
    ss = strings(blo)
    rule_names = [{"name": s, "offset": off} for off, s in ss
                  if RULE_RE.fullmatch(s)
                  and not s.startswith(("ai/", "evt", "tit", "hud", "fas", "tel", "graphs/"))]
    other_rules = sorted({s for _, s in ss
                          if OTHER_RULE_RE.fullmatch(s)
                          and not RULE_RE.fullmatch(s)})
    selectors = []
    for off, s in ss:
        tokens = [t for t in TAG_SPLIT.split(s) if t]
        if not (1 <= len(tokens) <= 8):
            continue
        if not all(re.fullmatch(r"-?[A-Za-z0-9_]+", t) for t in tokens):
            continue
        known = {t.lstrip("-").lower() for t in tokens}
        if not (known & vocab):
            continue
        nxt = next((r for r in rule_names if r["offset"] > off), None)
        selectors.append({"text": s, "tokens": tokens, "offset": off,
                          "next_rule": nxt["name"] if nxt else "",
                          "unknown": sorted(t.lstrip("-").lower() for t in tokens
                                            if t.lstrip("-").lower() not in vocab)})
    seats = [s for _, s in ss if s in ("SpawnSeat", "Driver", "Passenger", "Gunner")]
    bts = sorted({s for _, s in ss if s.startswith("ai/bts/")})
    return {"rule_names": rule_names, "selectors": selectors,
            "seat_names": sorted(set(seats)), "bts": bts, "other_rules": other_rules,
            "impostor": sorted({s for _, s in ss if "Impostor" in s})}


def matches(selector: dict, tags: set[str]) -> dict:
    need = [t for t in selector["tokens"] if not t.startswith("-")]
    deny = [t[1:] for t in selector["tokens"] if t.startswith("-")]
    missing = [t for t in need if t.lower() not in tags]
    hit = [t for t in deny if t.lower() in tags]
    return {"selector": selector["text"], "offset": selector["offset"],
            "next_rule": selector["next_rule"], "requires": need, "excludes": deny,
            "missing": missing, "denied_present": hit,
            "ok": not missing and not hit}


# ---------------------------------------------------------------- the scan
def classify(path: str, donor: str) -> tuple[str, str]:
    b = os.path.basename(path)
    if b.startswith("spawn_") and b.endswith("_defs.bin"):
        return "spawn table", "a record in a spawn-definition table"
    if path.endswith(".entityregc"):
        return "entity registry", "lists the entity, not a spawn"
    if b == "patchmetadata.bin":
        return "patch metadata", "lists the file as changed by the patch"
    if path.startswith("profile/"):
        if b == "item.onlinec":
            return "Rebel Drop", "an item in the Rebel Drop list"
        if b == "task.onlinec":
            return "task table", "a task key naming the vehicle (chop shop)"
        if b.endswith(".stringlookup"):
            return "localisation", "name lookup only"
        return "profile", "profile data"
    if b == "frontend_global.blo":
        return "frontend", "named in the frontend's vehicle list"
    if path.endswith(".blo"):
        return "level rule", "a CVehicleRule in a level's logic object"
    if donor in path or DONOR_DIR in path:
        return "self", "the entity's own file"
    return "other", "unclassified"


def ext_census(rows: list[dict], exts: set[str]) -> dict:
    """What was *not* read, by type, so the census can state its own boundary."""
    out: dict[str, dict] = {}
    for r in rows:
        e = os.path.splitext(r["path"])[1].lower() or "(none)"
        if e in exts:
            continue
        slot = out.setdefault(e, {"files": 0, "bytes": 0})
        slot["files"] += 1
        slot["bytes"] += r["size"]
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["bytes"]))


def scan(rows: list[dict], deep: bool) -> dict:
    exts = set(SCAN_A) | (set(SCAN_B) if deep else set())
    targets = [r for r in rows if os.path.splitext(r["path"])[1].lower() in exts]
    needle = DONOR_NAME.encode()
    h = (hash_jenkins(DONOR_NAME.encode()) & 0xFFFFFFFF)
    pats = (h.to_bytes(4, "little"), h.to_bytes(4, "big"))
    hits = []
    failed = []
    for row in targets:
        try:
            data = jc3grab.read_entry(row, GAME)
        except Exception as exc:  # noqa: BLE001
            failed.append(f"{row['path']}: {exc}")
            continue
        n = data.count(needle)
        k = sum(1 for p in pats if p in data)
        if not n and not k:
            continue
        kind, note = classify(row["path"], DONOR_NAME)
        hits.append({"path": row["path"], "mount": row["mount"], "size": row["size"],
                     "strings": n, "hashes": k, "kind": kind, "note": note,
                     "confidence": "name" if n else "hash only (may be a coincidence)"})
    order = {"spawn table": 0, "level rule": 1, "Rebel Drop": 2, "task table": 3,
             "frontend": 4, "entity registry": 5, "localisation": 6, "patch metadata": 7,
             "self": 8, "profile": 9, "other": 10}
    hits.sort(key=lambda x: (order.get(x["kind"], 9), -x["strings"], x["path"]))
    return {"extensions": sorted(exts), "files": len(targets),
            "bytes": sum(r["size"] for r in targets), "deep": deep,
            "not_scanned": ext_census(rows, exts),
            "needle": DONOR_NAME, "hash": f"{h:08X}", "hits": hits, "failed": failed}


# ---------------------------------------------------------------- donors and profiles
def donor_ai(rows: list[dict]) -> dict:
    """The donor's own AI module, if the index carries one (an index fact, not an assumption)."""
    mods = sorted(r["path"] for r in rows
                  if r["path"].startswith(f"editor/entities/jc_vehicles/01_land/{DONOR_DIR}/modules/")
                  and r["path"].endswith(".vmodc"))
    ai = [p for p in mods if "/ai/" in p]
    return {"modules": mods, "ai": ai}


def donor_identity() -> dict:
    return {"name": DONOR_NAME, "directory": DONOR_DIR,
            "path": f"editor/entities/jc_vehicles/01_land/{DONOR_DIR}/{DONOR_NAME}.ee",
            "path_hash": f"{hash_jenkins(('editor/entities/jc_vehicles/01_land/' + DONOR_DIR + '/' + DONOR_NAME + '.ee').encode()) & 0xFFFFFFFF:08X}",
            "name_hash": f"{hash_jenkins(DONOR_NAME.encode()) & 0xFFFFFFFF:08X}"}


def profile_keys(rows: list[dict], path: str) -> dict:
    row = resolved(path, rows)
    data = jc3grab.read_entry(row, GAME)
    ss = [s for _, s in strings(data)]
    keys = sorted({s for s in ss if DONOR_NAME in s and s != DONOR_NAME})
    names = sum(1 for s in ss if s == DONOR_NAME)
    return {"path": row["path"], "mount": row["mount"], "size": row["size"],
            "digest": digest(data), "name_count": names, "keys": keys}


def build(deep: bool = True) -> dict:
    rows = [json.loads(ln) for ln in read(INDEX).splitlines() if ln.strip()]
    tables = parse_spawn_files(rows)
    main = main_table(tables)
    donor_rec = next((r for r in main["v0300"] if r["name"] == DONOR_NAME), None)
    if donor_rec is None:
        raise SystemExit("FAIL: donor not in settings/spawn_vehicle_defs.bin")

    # the tag vocabulary is the data's own: every tag written in any spawn table
    vocab: set[str] = set()
    for path, t in tables.items():
        data = jc3grab.read_entry(resolved(path, rows), GAME)
        for rec in spawn_records(data):
            vocab.update(x.lower() for x in rec["tags"])

    rules_row = resolved(RULES_FILE, rows)
    rules_data = jc3grab.read_entry(rules_row, GAME)
    r = rules_from(rules_data, vocab)
    tags = {t.lower() for t in donor_rec["tags"]}
    sel = [matches(s, tags) for s in r["selectors"]]
    ok = [m for m in sel if m["ok"]]

    return {
        "inputs": {"INDEX.jsonl": digest(read(INDEX).encode()),
                   SPAWN_FILE: dict(main["digest"]),
                   RULES_FILE: digest(rules_data)},
        "donor": donor_identity(),
        "donor_modules": donor_ai(rows),
        "scan": scan(rows, deep),
        "spawn": {"main": {"path": main["path"], "mount": main["mount"], "size": main["size"],
                           "records": main["records"], "groups": main["groups"],
                           "pool_counts": _pools(main, rows), "v0300": main["v0300"],
                           "keyed_records": _keyed(main, rows),
                           "tag_pairs": _tag_pairs(main, rows)},
                  "tables": {p: {"mount": t["mount"], "size": t["size"],
                                 "records": t["records"], "groups": len(t["groups"]),
                                 "v0300": [x["name"] for x in t["v0300"]]}
                             for p, t in tables.items()},
                  "donor_record": donor_rec,
                  "tag_counts": _tag_counts(main, rows),
                  "vocabulary_size": len(vocab)},
        "rules": {"path": rules_row["path"], "mount": rules_row["mount"],
                  "size": rules_row["size"], "rule_names": r["rule_names"],
                  "selectors": r["selectors"], "seat_names": r["seat_names"],
                  "bts": r["bts"], "impostor": r["impostor"],
                  "other_rules": r["other_rules"],
                  "donor_matches": ok, "donor_misses": len(sel) - len(ok),
                  "selector_count": len(sel)},
        "profiles": {"item": profile_keys(rows, "profile/item.onlinec"),
                     "task": profile_keys(rows, "profile/task.onlinec")},
    }


def _main_records(main: dict, rows: list[dict]) -> list[dict]:
    return spawn_records(jc3grab.read_entry(resolved(main["path"], rows), GAME))


def _tag_pairs(main: dict, rows: list[dict]) -> dict:
    """How the two civilian tags co-occur, so the md can say it as a count and not a slogan."""
    recs = _main_records(main, rows)
    low = [{t.lower() for t in r["tags"]} for r in recs]
    return {"records": len(recs),
            "ambient": sum(1 for t in low if "ambient" in t),
            "liberated": sum(1 for t in low if "liberated" in t),
            "ambient_and_liberated": sum(1 for t in low if {"ambient", "liberated"} <= t),
            "traffic_tagged": sum(1 for t in low if any(x.endswith("_traffic") for x in t)),
            "liberated_without_ambient": sum(1 for t in low if "liberated" in t
                                             and "ambient" not in t)}


def _keyed(main: dict, rows: list[dict]) -> int:
    return sum(1 for rec in _main_records(main, rows) if rec["group"])


def _pools(main: dict, rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for rec in _main_records(main, rows):
        if rec["group"]:
            counts[rec["group"]] = counts.get(rec["group"], 0) + 1
    return dict(sorted(counts.items()))


def _tag_counts(main: dict, rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for rec in _main_records(main, rows):
        for t in rec["tags"]:
            counts[t] = counts.get(t, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _pool_counts(main: dict, rows: list[dict]) -> dict:
    """How many records carry each key. Most records carry none - the donation record does not."""
    counts: dict[str, int] = {}
    for rec in _main_records(main, rows):
        counts[rec["group"]] = counts.get(rec["group"], 0) + 1
    return dict(sorted(counts.items()))


# ---------------------------------------------------------------- markdown
def fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, list):
        return ", ".join(fmt(x) for x in v) if v else "-"
    return str(v)


def render_md(d: dict) -> str:
    L: list[str] = []
    a = L.append
    s, sp, ru, pr = d["scan"], d["spawn"], d["rules"], d["profiles"]
    rec = sp["donor_record"]
    tags = rec["tags"]
    hit = ru["donor_matches"][0] if ru["donor_matches"] else None

    a("# Traffic, AI and spawning of `v0300`")
    a("")
    a(f"G2-29. **Answer: `v0300_car_kensington_sportsmuscle_civilian_01` is a civilian traffic "
      f"vehicle, so replacing it puts AI-driven Batmobiles on the roads.** It has a record in the "
      f"ground-vehicle spawn table (`{SPAWN_FILE}`) whose tag list "
      f"`{', '.join(tags)}` satisfies {len(ru['donor_matches'])} of the {ru['selector_count']} "
      f"tag selectors in the traffic-rule block of `{RULES_FILE}`"
      + (f" - `{hit['selector']}`" if hit else "")
      + f"; those rules spawn a driver seat with an AI behaviour tree, and the entity ships its own "
      f"AI module. Only `civilian_01` is in that table, not the other `v0300` builds. **Lore break "
      f"(MOD-5, WLD-8): decision D-6 must take the standalone route (G2-27).**")
    a("")
    a(f"The full census is {len(s['hits'])} files that name the donor out of {s['files']} scanned "
      f"({s['bytes'] / 1e6:.0f} MB, tier {'A+B' if s['deep'] else 'A only'}); the spawn sites are "
      f"one spawn table, one Rebel Drop item, one chop-shop task key, two level `CVehicleRule` "
      f"objects and one frontend list entry. What the tags *mean* and whether the engine's traffic "
      f"picker reads them that way is `UNKNOWN` - that matcher is native code (§6).")
    a("")
    a("## 1. Every file that names the donor")
    a("")
    a(f"Scan: every index entry whose extension is one of `{', '.join(s['extensions'])}` - "
      f"**{s['files']} files / {s['bytes'] / 1e6:.1f} MB** - read from the archives and searched for "
      f"the ASCII name `{s['needle']}` and for the 32-bit Jenkins hash `{s['hash']}` of that name in "
      f"both byte orders. Tier B (`{', '.join(SCAN_B)}`: levels, level logic, entity modules) is "
      f"included{'' if s['deep'] else ' **NO - this run is --fast**'}.")
    a("")
    a("| kind | file | mount | bytes | name hits | hash hits | confidence | what it is |")
    a("|---|---|---|---|---|---|---|---|")
    for h in s["hits"]:
        a(f"| {h['kind']} | `{h['path']}` | {h['mount']} | {h['size']} | {h['strings']} | "
          f"{h['hashes']} | {h['confidence']} | {h['note']} |")
    a("")
    top = list(s["not_scanned"].items())[:5]
    a(f"**Not read:** {sum(v['files'] for v in s['not_scanned'].values())} files / "
      f"{sum(v['bytes'] for v in s['not_scanned'].values()) / 1e9:.1f} GB of media and navmesh types "
      f"({', '.join(f'`{e}` {v['files']}' for e, v in top)}) - none of them is a data table, and a "
      f"level that names the donor is covered by tier B. The full exclusion census is in the JSON.")
    a("")
    a(f"{len(s['hits'])} file rows ({s['failed'] and len(s['failed']) or 0} could not be read). Rows "
      f"with 0 name hits are a 32-bit hash that happens to occur in the file - they are listed for "
      f"completeness and are not used for any claim. Of the name hits, three are not spawn sites: "
      f"the entity's own `.epe`, the entity registry (which lists every entity) and "
      f"`patchmetadata.bin` (which lists the file as patched). Base and patch copies of the same "
      f"path each get their own row.")
    a("")
    a("## 2. The spawn table")
    a("")
    a(f"`{sp['main']['path']}` ({sp['main']['mount']}, "
      f"{sp['main']['size']} B) is the ground-vehicle spawn table: **{sp['main']['records']} "
      f"records**, each `entity path` + `tag list` + `name`. `settings/spawn_budget_pools.bin` names "
      f"it as *Ground Vehicles*, alongside `spawn_aircraft_defs.bin`, `spawn_boat_defs.bin` and the "
      f"rest, so this is the file the spawner draws ground vehicles from.")
    a("")
    a(f"**A pool key is a sparse field, and the donor's record has none.** Only "
      f"{sp['main']['keyed_records']} of the {sp['main']['records']} records carry a `a|b|c` key "
      f"string in the same record, and every key that does occur occurs once: "
      + ", ".join(f"`{k}`" for k in sp["main"]["pool_counts"]) +
      f". So the key cannot be read as a group label (my first pass did exactly that and invented "
      f"pools with 35 records in them), and **the donor's pool is `UNKNOWN`** - what selects it is "
      f"the tag list, which is what §3 tests. The record layout beyond its three strings is not "
      f"decoded here.")
    a("")
    a(f"The donor's record, read out of the table (offset {rec['offset']}):")
    a("")
    a("| field | value |")
    a("|---|---|")
    a(f"| pool key | {'`' + rec['group'] + '`' if rec['group'] else 'none in this record (UNKNOWN)'} |")
    a(f"| entity path | `{rec['path']}` |")
    a(f"| tags | {', '.join('`' + t + '`' for t in tags)} |")
    a(f"| name | `{rec['name']}` |")
    a("")
    a(f"Tag census over the {sp['main']['records']} records: "
      + ", ".join(f"`{k}` {v}" for k, v in list(sp["tag_counts"].items())[:14]) + " …")
    a("")
    a(f"Each build of the chassis sits in exactly one table, and they are different tables: "
      f"`civilian_01` here (the traffic table), the debug build in "
      f"`settings/spawn_vehicle_proto_defs.bin` and the pre-order build in the DLC's own "
      f"`dlc/v0300_preorder/settings/spawn_vehicle_defs.bin`. That matters for D-6: the *Batmobile* "
      f"would inherit the civilian car's traffic slot **only because it replaces `civilian_01`**, not "
      f"because the chassis is spawnable in general.")
    a("")
    a("| spawn table | mount | records | pool keys | `v0300` records |")
    a("|---|---|---|---|---|")
    for p, t in sorted(sp["tables"].items()):
        a(f"| `{p}` | {t['mount']} | {t['records']} | {t['groups']} | {fmt(t['v0300'])} |")
    a("")
    a("## 3. The traffic rules, and why this record is traffic")
    a("")
    a(f"`{ru['path']}` ({ru['size']} B) carries **{len(ru['rule_names'])} traffic-rule names**, "
      f"**{ru['selector_count']} tag selectors** (vehicle lists and driver-character lists), driver "
      f"seats ({', '.join(ru['seat_names'])}) and **{len(ru['bts'])} AI behaviour-tree paths**. A "
      f"rule there is a tag list plus a driver: e.g. the rebel tank rule pairs a vehicle selector "
      f"with `character,rebel` / `grunt` / `Driver` / "
      f"`ai/bts/enemies/01_shared/soldier_tank_driver.bts`. The numbered civilian rules carry no "
      f"`Rule` suffix in the game's data (`03_CivilianCarLiberatedProvince`), so the census matches "
      f"both spellings; {len(ru['other_rules'])} other `*Rule` objects in the same file are not "
      f"traffic ({', '.join('`' + x + '`' for x in ru['other_rules'])}) and are excluded.")
    a("")
    a(f"Testing the donor's tags against every selector (a selector matches when all of its plain "
      f"tags are present and none of its `-tag` exclusions are):")
    a("")
    a("| selector | next rule name in the file | requires | excludes | matches the donor? |")
    a("|---|---|---|---|---|")
    for m in ru["donor_matches"]:
        a(f"| `{m['selector']}` | `{m['next_rule']}` | {fmt(m['requires'])} | {fmt(m['excludes'])} "
          f"| **yes** |")
    for m in _near_misses(d):
        a(f"| `{m['selector']}` | `{m['next_rule']}` | {fmt(m['requires'])} | {fmt(m['excludes'])} "
          f"| no (missing {fmt(m['missing'])}) |")
    a("")
    a(f"**{len(ru['donor_matches'])} of {ru['selector_count']} selectors match**, and the match is a "
      f"civilian *car* rule, not a faction or special one. The pairing of selector to rule name is "
      f"positional (selector, then its rule name, then its driver list) and is labelled as such: "
      f"the record layout of the file is not decoded, only its strings.")
    a("")
    a("Rule names in the file, for context: " + ", ".join(f"`{x['name']}`" for x in ru["rule_names"]) + ".")
    a("")
    a("## 4. The other spawn sites")
    a("")
    a("| site | file | evidence |")
    a("|---|---|---|")
    a(f"| Rebel Drop item | `{pr['item']['path']}` ({pr['item']['mount']}, {pr['item']['size']} B) | "
      f"the donor name appears {pr['item']['name_count']}× plus "
      f"{len(pr['item']['keys'])} key(s): {', '.join('`' + k + '`' for k in pr['item']['keys']) or '-'} "
      f"- an item with a description key, so it is droppable by the player |")
    a(f"| chop-shop task | `{pr['task']['path']}` ({pr['task']['mount']}, {pr['task']['size']} B) | "
      f"{', '.join('`' + k + '`' for k in pr['task']['keys']) or '-'} "
      f"- a chop-shop task keyed on the vehicle |")
    lvl = [h for h in s["hits"] if h["kind"] == "level rule"]
    a(f"| level vehicle rules | {', '.join('`' + h['path'] + '`' for h in lvl) or '-'} | "
      f"`CVehicleRule` + `point.stunt` + the donor name in the level's logic object |")
    fe = [h for h in s["hits"] if h["kind"] == "frontend"]
    a(f"| frontend list | {', '.join('`' + h['path'] + '`' for h in fe) or '-'} | "
      f"the name sits in the frontend's padded string table |")
    a("")
    a("No shipped *region* level places the donor: the tier-B scan read every `.bl`, `.blo` and "
      "`.ee` and found it in two course/prototype logic objects and the frontend only. So the world "
      "does not park this car anywhere - **the spawner is what puts it in the world**, which is "
      "exactly the case the card asks about.")
    a("")
    tp = sp["main"]["tag_pairs"]
    a("## 5. What the tags say, counted")
    a("")
    a(f"Of the {tp['records']} ground-vehicle records, **{tp['ambient']} carry `ambient`** and "
      f"**{tp['ambient_and_liberated']} carry both `ambient` and `liberated`** - the donor is one of "
      f"them; {tp['liberated_without_ambient']} carry `liberated` without `ambient`, and "
      f"{tp['traffic_tagged']} carry a faction `*_traffic` tag instead "
      f"(`mil_now_traffic`, `mil_auth_road_traffic`, `rebel_now_traffic`). So `ambient` is the "
      f"civilian-traffic marker and `liberated` is the province condition, and the donor has both. "
      f"The matching selector asks for exactly `ambient,ground,car,liberated` and excludes "
      f"`highend` - which the donor is not tagged with.")
    a("")
    a("## 6. What AI drives it, and what stays UNKNOWN")
    a("")
    a(f"* **Proven.** The donor has a traffic-table record (§2); a civilian-car selector in the "
      f"traffic-rule block is satisfied by its tags (§3); the traffic rules in that block spawn "
      f"`Driver` seats bound to `ai/bts/...` behaviour trees, and the file also carries "
      f"{', '.join('`' + x + '`' for x in ru['impostor']) or '-'}; and the entity ships its own AI "
      f"module(s): {', '.join('`' + x + '`' for x in d['donor_modules']['ai']) or '**none in the index**'} "
      f"({len(d['donor_modules']['modules'])} module files in the entity's `modules/` tree).")
    a(f"* **UNKNOWN.** The tag matcher itself: no file in the archive states that a rule selecting "
      f"`{hit['selector'] if hit else ''}` takes records whose tags are a superset, and no script "
      f"(`graphs/*.gsc`, `ai/bts/*.btc`) mentions these tags - the picker is native. Whether the "
      f"impostor system reuses the same records, how often a province's traffic is re-rolled, and "
      f"what each record's six numeric fields mean (offsets, weights?) are also UNKNOWN: the file's "
      f"numeric block is not decoded, only its strings.")
    a(f"* **UNKNOWN.** Whether the two `CVehicleRule` levels would drag a Batmobile into their "
      f"course logic at runtime (they name the donor, but nothing says when the rule fires).")
    a("")
    a("## 7. What this means for the build")
    a("")
    a("| route | what happens to traffic |")
    a("|---|---|")
    a("| replace `civilian_01` (current plan) | the Batmobile inherits the civilian car's traffic "
      "record: NPC-driven Batmobiles in liberated provinces = **lore break** (MOD-5, WLD-8) |")
    a("| standalone entity, unhooked from the table (G2-27) | no traffic record, so no NPC "
      "Batmobiles - and the chop-shop/drop keys are keyed on the donor's name, so they would have to "
      "be added for the new path |")
    a("| replace `civilian_01` **and** edit `spawn_vehicle_defs.bin` to drop/mark the record | needs "
      "a `settings/` override in the dropzone; whether the engine honours a replaced settings file "
      "without a hash change is `UNKNOWN` (G2-27's question) |")
    a("")
    a("That third row is the decision D-6 actually owns; G2-29 only proves the record exists and "
      "that its tags select it into traffic.")
    a("")
    a("## 8. Checks")
    a("")
    a("| check | result |")
    a("|---|---|")
    a(f"| `python Tools/scripts/jc3traffic.py --check` | rebuilds both files and asserts the census, "
      f"the donor's record and the tag match |")
    a(f"| files scanned | {s['files']} ({s['bytes'] / 1e6:.1f} MB), tiers "
      f"{'A+B' if s['deep'] else 'A'} |")
    a(f"| files naming the donor | {len(s['hits'])} |")
    a(f"| spawn records | {sp['main']['records']} ({sp['main']['keyed_records']} carry a pool "
      f"key) |")
    a(f"| traffic rules / selectors | {len(ru['rule_names'])} / {ru['selector_count']} |")
    a(f"| selectors the donor satisfies | {len(ru['donor_matches'])} |")
    a("")
    a("Every number here is regenerated from the archives; none is typed by hand.")
    return "\n".join(L) + "\n"


def _other_v0300(d: dict) -> list[str]:
    main = d["spawn"]["main"]["path"]
    return [x for p, t in d["spawn"]["tables"].items() if p != main for x in t["v0300"]]


def _near_misses(d: dict) -> list[dict]:
    """The selectors that nearly match - one or two tags short - for the md table."""
    ru = d["rules"]
    tags = {t.lower() for t in d["spawn"]["donor_record"]["tags"]}
    out = []
    for s in ru["selectors"]:
        m = matches(s, tags)
        if m["ok"] or len(m["requires"]) < 2:
            continue  # driver/character lists and one-word tags are not vehicle selectors
        if len(m["missing"]) <= 1 and not m["denied_present"]:
            out.append(m)
    return out[:4]


# ---------------------------------------------------------------- invariants
def invariants(d: dict) -> list[str]:
    bad: list[str] = []
    s, sp, ru = d["scan"], d["spawn"], d["rules"]
    rec = sp["donor_record"]

    if not s["deep"]:
        bad.append("scan ran --fast: tier B (levels/entities) missing, the census is incomplete")
    if s["failed"]:
        bad.append(f"{len(s['failed'])} unreadable files: {s['failed'][:2]}")
    kinds = {h["kind"] for h in s["hits"]}
    for need in ("spawn table", "Rebel Drop", "task table", "level rule", "entity registry"):
        if need not in kinds:
            bad.append(f"no {need} hit")
    if len([h for h in s["hits"] if h["kind"] == "spawn table"]) != 1:
        bad.append(f"{len([h for h in s['hits'] if h['kind'] == 'spawn table'])} spawn tables name "
                   f"the donor (expected 1)")
    if len([h for h in s["hits"] if h["kind"] == "level rule"]) != 2:
        bad.append(f"{len([h for h in s['hits'] if h['kind'] == 'level rule'])} level rules "
                   f"(expected 2)")

    if sp["main"]["records"] != 86:
        bad.append(f"spawn records {sp['main']['records']} (expected 86)")
    if sp["main"]["keyed_records"] != 8 or len(sp["main"]["pool_counts"]) != 8:
        bad.append(f"keyed records {sp['main']['keyed_records']} / pools "
                   f"{len(sp['main']['pool_counts'])} (expected 8 / 8)")
    for key in sp["main"]["groups"]:
        if not GROUP_RE.fullmatch(key):
            bad.append(f"impossible pool key {key!r} (binary noise accepted as a group)")
    # measured: the donor's own record carries no pool key - the sparse-key finding this card reports
    if rec["group"] != "":
        bad.append(f"donor record now carries a pool key {rec['group']!r} - revisit the write-up")
    if sp["main"]["keyed_records"] > sp["main"]["records"]:
        bad.append("more keyed records than records")
    want = {"vehicle", "ground", "car", "civilian", "unarmed", "unarmored", "ambient", "liberated"}
    if not want <= {t.lower() for t in rec["tags"]}:
        bad.append(f"donor tags missing {sorted(want - {t.lower() for t in rec['tags']})}")
    if len(sp["main"]["v0300"]) != 1:
        bad.append(f"{len(sp['main']['v0300'])} v0300 records in the ground table (expected 1)")
    others = {p: t["v0300"] for p, t in sp["tables"].items() if p != sp["main"]["path"] and t["v0300"]}
    if len(others) != 2:
        bad.append(f"{len(others)} other tables with a v0300 record (expected 2: proto + preorder)")

    if len(ru["rule_names"]) != 31:
        bad.append(f"traffic rule names {len(ru['rule_names'])} (expected 31)")
    if not any(r["name"] == "03_CivilianCarLiberatedProvince" for r in ru["rule_names"]):
        bad.append("the numbered civilian car rule name is missing from the rule census")
    if ru["selector_count"] < 15:
        bad.append(f"selectors {ru['selector_count']} (expected >=15)")
    if len(ru["donor_matches"]) != 1:
        bad.append(f"{len(ru['donor_matches'])} selectors match the donor (expected 1)")
    elif ru["donor_matches"][0]["selector"] != "ambient,ground,car,liberated,-highend":
        bad.append(f"matching selector {ru['donor_matches'][0]['selector']}")
    elif ru["donor_matches"][0]["next_rule"] != "03_CivilianCarLiberatedProvince":
        bad.append(f"the matching selector's next rule is "
                   f"{ru['donor_matches'][0]['next_rule']} (expected the civilian car rule)")
    if not d["donor_modules"]["ai"]:
        bad.append("the donor has no AI module in the index")
    if "Driver" not in ru["seat_names"]:
        bad.append(f"no Driver seat in the rule block: {ru['seat_names']}")
    if len(ru["bts"]) < 5:
        bad.append(f"AI behaviour-tree refs {len(ru['bts'])} (expected >=5)")

    if not pr_item_key(d):
        bad.append("no Rebel Drop description key for the donor")
    if not pr_task_key(d):
        bad.append("no chop-shop task key for the donor")
    return bad


def pr_item_key(d: dict) -> bool:
    return any(k.endswith("_desc") for k in d["profiles"]["item"]["keys"])


def pr_task_key(d: dict) -> bool:
    return any(k.startswith("chopshop_") for k in d["profiles"]["task"]["keys"])


# ---------------------------------------------------------------- commands
def cmd_write(deep: bool) -> int:
    d = build(deep)
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    md = render_md(d)
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"{JSON_NAME}/{MD_NAME}: {d['scan']['files']} files scanned "
          f"({d['scan']['bytes'] / 1e6:.0f} MB, {'A+B' if deep else 'A'}), "
          f"{len(d['scan']['hits'])} name the donor, {d['spawn']['main']['records']} spawn records "
          f"({d['spawn']['main']['keyed_records']} with a pool key), "
          f"{len(d['rules']['rule_names'])} traffic rules, "
          f"{len(d['rules']['donor_matches'])} matching selector(s), {len(md.splitlines())} md lines")
    return 0


def cmd_check(deep: bool) -> int:
    d = build(deep)
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
        diff = list(difflib.unified_diff(have.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    rec = d["spawn"]["donor_record"]
    print(f"PASS: {d['scan']['files']} files scanned ({d['scan']['bytes'] / 1e6:.0f} MB, A+B), "
          f"{len(d['scan']['hits'])} name the donor "
          f"({'/'.join(sorted({h['kind'] for h in d['scan']['hits']}))}), "
          f"{d['spawn']['main']['records']} spawn records "
          f"({d['spawn']['main']['keyed_records']} with a pool key), donor tag list of "
          f"{len(rec['tags'])} tags, {len(d['rules']['rule_names'])} traffic rules / "
          f"{d['rules']['selector_count']} selectors, "
          f"{len(d['rules']['donor_matches'])} match "
          f"(`{d['rules']['donor_matches'][0]['selector']}`), "
          f"{len(d['rules']['bts'])} AI behaviour trees")
    return 0


def cmd_dump(what: str, deep: bool) -> int:
    d = build(deep)
    key = {"records": ("spawn", "main"), "rules": ("rules",), "hits": ("scan",),
           "profile": ("profiles",), "donor": ("donor",), "tags": ("spawn", "tag_counts")}
    if what not in key:
        print("one of: " + ", ".join(sorted(key)))
        return 2
    node = d
    for k in key[what]:
        node = node[k]
    print(json.dumps(node, indent=1, sort_keys=True, ensure_ascii=False)[:12000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    p.add_argument("--fast", action="store_true",
                   help="skip the tier-B scan (levels/entities); --check then fails closed")
    sub = p.add_subparsers(dest="cmd")
    dl = sub.add_parser("dump")
    dl.add_argument("what", nargs="?", default="records")
    a = p.parse_args()
    deep = not a.fast
    if a.write:
        return cmd_write(deep)
    if a.check:
        return cmd_check(deep)
    if a.cmd == "dump":
        return cmd_dump(a.what, deep)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
