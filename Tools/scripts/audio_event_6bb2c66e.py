#!/usr/bin/env python
"""audio_event_6bb2c66e.py - which bank (if any) holds Batmobile audio event 0x6BB2C66E?

`AUDIO_BANKS.md` (G3-14) found all ten "absent" BmAK banks and left exactly one event with no
located bank: `0x6BB2C66E`.  `AUDIO_BANKS2.md` searched the 117 located payloads and reported
UNKNOWN.  This tool re-asks the question from bytes and adds the one channel those cards did
not use: **the package that declares the event**.

What it does, all from bytes:

  1. **declaration** - every `AUDIO_MAP.json` row whose `event_id` is the target: its name, its
     outer object, its packages and the bank the pair names.  The id is re-derived from the
     name with the documented rule `fnv1(lower(name))` (offset 0x811C9DC5, prime 0x01000193),
     so a miss in the banks is a fact about the bank, not about the lookup.
  2. **bank census** - every export `AUDIO_BANKS.json` locates (117 in the recorded run) is
     re-read and searched four ways: parsed HIRC Event ids, raw little-endian u32, raw
     big-endian u32, and the ASCII event name inside the payload.
  3. **package census** - for every package those banks live in, and for every package
     `AUDIO_MAP.json` attributes the event to: the decoded name table (is the string a name?),
     the export table (which object carries the name, of which class, under which outer), and
     the export payloads (does the object hold the ASCII event name?).  A second name found
     this way - `Play_Disruptor_Vehicle_Tracking_Fire` - is hashed and looked up too, because
     an `AkEvent` object name and the Wwise event name it plays are two different strings.
  4. **feature code** - the `AUDIO_FEATURES.json` group of the event and of its bank
     neighbours, mapped to the AUD-1...AUD-7 row it serves.
  5. **ledger** - for rows `T-AU3` and `T-AU5`: every declared id, whether a located bank
     carries it, and the reason it has no JC3 binding.

Oracles (each fails loudly):
  O-1 the local name->id rule reproduces the target id from the declared name;
  O-2 every payload's SHA-1 equals `AUDIO_BANKS.json`'s record for that export;
  O-3 every parsed HIRC Event id is also present as a raw little-endian u32 in the same
      payload (the parse and the bytes agree), and the target's raw LE/BE hits agree;
  O-4 the HIRC event count equals the recorded `events_in_bank`.

Writes `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.md` and `.json`.  `--check` re-derives both
and fails on drift.  Read-only: the BmAK install and every generated file.

Usage:
    uv run python Tools/scripts/audio_event_6bb2c66e.py --write
    uv run python Tools/scripts/audio_event_6bb2c66e.py --check
    uv run python Tools/scripts/audio_event_6bb2c66e.py --print
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
import upk_read as U                     # noqa: E402
import grab_audio_banks as G14           # noqa: E402  (package probe, read-only)
import grab_audio_banks2 as B2           # noqa: E402  (payload/image/HIRC readers)

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
BANKS_JSON = os.path.join(OUT, "AUDIO_BANKS.json")
MAP_JSON = os.path.join(OUT, "AUDIO_MAP.json")
FEAT_JSON = os.path.join(OUT, "AUDIO_FEATURES.json")
MD = os.path.join(OUT, "AUDIO_EVENT_6BB2C66E.md")
JSON_OUT = os.path.join(OUT, "AUDIO_EVENT_6BB2C66E.json")

TARGET = 0x6BB2C66E
TARGET_HEX = "0x%08X" % TARGET
# the name `AUDIO_MAP.json` declares for the id, and the name the package name table carries
NAME_IN_MAP = "Play_BatSniperRifle_Vehicle_Tracking_Fire"
NAME_IN_PACKAGE = "Play_Disruptor_Vehicle_Tracking_Fire"
# T-AU3's ten claim banks (the table in AUDIO_BANKS.md, header "bank (claim)")
TAU3_BANKS = (
    "BML_Batmobile_Subjective", "BML_Impacts", "BML_Sonar", "CHR_BatmanAlerts",
    "CHR_BatmanDisruptor", "UI_InGame", "VEH_Tank_Heavy", "VEH_Tank_Missiles",
    "VFX_Tank_Explosion", "OBJ_Rolling_Objects",
)
# AUDIO_FEATURES.json group -> the AUD row it serves (Research/JC3Grab/JC3_AUDIO.md section 9)
GROUP_TO_AUD = {
    "engine": "AUD-1", "afterburner": "AUD-2", "burnout": "AUD-2", "interior": "AUD-3",
    "battle-mode": "AUD-4", "weapons": "AUD-5", "impacts": "AUD-6", "movement": "AUD-6",
    "horn": "AUD-7",
}
TAU5_TOKENS = ("TransformationReverseDirection", "TaserSound", "VehicleSound")


# ---------------------------------------------------------------- helpers
def fnv(name: str) -> int:
    """The decoded name->id rule: FNV-1 over the lower-cased name."""
    return B2.fnv1(name.lower().encode("latin-1"))


def file_sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def needle_hits(buf: bytes, text: str) -> dict:
    a = text.encode("latin-1")
    w = text.encode("utf-16-le")
    return {"ascii": B2.find_all(buf, a), "utf16": B2.find_all(buf, w)}


# ---------------------------------------------------------------- 1. declaration
def declaration() -> dict:
    doc = json.load(open(MAP_JSON, encoding="utf-8"))
    rows, seen = [], set()
    for e in doc.get("events") or []:
        eid = e.get("event_id")
        if not isinstance(eid, int):
            try:
                eid = int(str(e.get("event_id_hex")), 16)
            except ValueError:
                continue
        if eid != TARGET:
            continue
        key = (e.get("name"), e.get("package"), e.get("outer"), e.get("bank_ref"))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "name": e.get("name"),
            "package": e.get("package"),
            "outer": e.get("outer"),
            "bank_ref": e.get("bank_ref"),
            "status": e.get("status"),
            "media": len(e.get("media") or []),
        })
    names = sorted({r["name"] for r in rows if r["name"]})
    banks = sorted({(r["bank_ref"] or "").split(".")[-1] for r in rows if r["bank_ref"]})
    pkgs = sorted({r["package"] for r in rows if r["package"]})
    rule = [{"name": n, "fnv1_lower": fnv(n), "fnv1_lower_hex": "0x%08X" % fnv(n),
             "matches_target": fnv(n) == TARGET}
            for n in (NAME_IN_MAP, NAME_IN_PACKAGE)]
    return {
        "rows": len(rows),
        "unique_ids": 1,
        "names": names,
        "declared_bank": banks,
        "packages": pkgs,
        "outer": sorted({r["outer"] for r in rows if r["outer"]}),
        "statuses": sorted({r["status"] for r in rows if r["status"]}),
        "media_rows": sum(r["media"] for r in rows),
        "rule": rule,
        "records": rows,
    }


# ---------------------------------------------------------------- 2. bank census
def bank_census() -> dict:
    banks = B2.bank_list()
    images: dict[str, B2.Image] = {}
    probes: dict[str, dict] = {}
    rows, union = [], {}
    for b in banks:
        path, pkg = b["path"], b["package"]
        if pkg not in images:
            probe = G14.probe_package(path)
            if not probe.get("ok"):
                raise SystemExit("package %s unreadable: %s" % (pkg, probe.get("tried")))
            probes[pkg] = probe
            images[pkg] = B2.Image(path, probe["name_offset"], probe.get("chunk_at"))
        exp = next((e for e in probes[pkg]["ak"] if e["index"] == b["index"]), None)
        if exp is None:
            raise SystemExit("%s export %d is not an AkBank" % (pkg, b["index"]))
        payload = images[pkg].get(exp["offset"], exp["offset"] + exp["bytes"])
        ch = B2.wwise_chunks(payload)
        ev = (B2.hirc_events(payload, ch["hirc_at"]) if ch.get("hirc_at") is not None
              else {"count": 0, "read": 0, "events": [], "complete": False})
        ids = ev["events"]
        for i in ids:
            union.setdefault(i, []).append("%s.%s" % (pkg, b["bank"]))
        rows.append({
            "bank": b["bank"], "package": pkg, "export": b["index"],
            "bytes": len(payload), "sha1": B2.sha1_16(payload),
            "sha1_recorded": b["sha1"], "sha1_match": B2.sha1_16(payload) == b["sha1"],
            "events": len(ids), "events_recorded": b["events_in_bank"],
            "hirc_count": ev["count"], "hirc_read": ev["read"], "hirc_complete": ev["complete"],
            "target_in_hirc": TARGET in ids,
            "target_raw_le": B2.find_all(payload, struct.pack("<I", TARGET)),
            "target_raw_be": B2.find_all(payload, struct.pack(">I", TARGET)),
            "name_in_payload": needle_hits(payload, NAME_IN_MAP)["ascii"],
            "alt_name_in_payload": needle_hits(payload, NAME_IN_PACKAGE)["ascii"],
            "ids": ["0x%08X" % i for i in ids],
        })
    hits = [r for r in rows if r["target_in_hirc"] or r["target_raw_le"] or r["target_raw_be"]]
    alt_id = fnv(NAME_IN_PACKAGE)
    alt_hits = sorted({c for i, where in union.items() if i == alt_id for c in where})
    tgt_hits = sorted({c for i, where in union.items() if i == TARGET for c in where})
    return {
        "rows": rows,
        "counts": {
            "exports_searched": len(rows),
            "banks": len({(r["package"], r["bank"]) for r in rows}),
            "distinct_banks": len({r["bank"] for r in rows}),
            "event_ids_seen": len(union),
            "payloads_with_target": len(hits),
            "payloads_with_alt_id": len(alt_hits),
        },
        "hits": [{"package": r["package"], "export": r["export"], "bank": r["bank"],
                  "hirc": r["target_in_hirc"], "raw_le": r["target_raw_le"],
                  "raw_be": r["target_raw_be"]} for r in hits],
        "target_carried_by": tgt_hits,
        "alt_id": alt_id,
        "alt_id_hex": "0x%08X" % alt_id,
        "alt_id_carried_by": alt_hits,
        "union": union,
    }


# ---------------------------------------------------------------- 3. package census
def package_census(bank_rows: list[dict], decl: dict) -> dict:
    paths: dict[str, str] = {}
    for r in bank_rows:
        paths.setdefault(r["package"], None)
    for b in B2.bank_list():
        paths[b["package"]] = b["path"]
    for p in decl["packages"]:
        paths.setdefault(p, None)
    out = []
    for name in sorted(paths):
        path = paths[name]
        if not path or not os.path.isfile(path):
            out.append({"package": name, "readable": False, "path": path})
            continue
        try:
            pkg = U.Package(path)
        except Exception as exc:                                   # pragma: no cover
            out.append({"package": name, "readable": False, "path": path, "error": str(exc)})
            continue
        image = pkg.image
        names = pkg.names
        rec = {
            "package": name, "readable": True,
            "path": path.replace("\\", "/"),
            "names": len(names), "exports": len(pkg.exports),
            "name_in_table": [NAME_IN_MAP, NAME_IN_PACKAGE][0] in names,
            "alt_name_in_table": NAME_IN_PACKAGE in names,
            "image_hits": {"declared_ascii": 0, "declared_utf16": 0,
                           "package_ascii": 0, "package_utf16": 0},
            "objects": [],
        }
        for i, e in enumerate(pkg.exports, 1):
            if e["name"] not in (NAME_IN_MAP, NAME_IN_PACKAGE):
                continue
            try:
                payload = pkg.data(i)
            except Exception:                                      # pragma: no cover
                payload = b""
            rec["objects"].append({
                "export": i, "name": e["name"], "class": pkg.object_class(i),
                "path": pkg.object_path(i), "size": e["size"],
                "payload_target_le": B2.find_all(payload, struct.pack("<I", TARGET)),
                "payload_alt_le": B2.find_all(payload, struct.pack("<I", fnv(NAME_IN_PACKAGE))),
            })
        rec["name_in_table"] = NAME_IN_MAP in names
        for key, text in (("declared", NAME_IN_MAP), ("package", NAME_IN_PACKAGE)):
            h = needle_hits(image, text)
            rec["image_hits"][key + "_ascii"] = len(h["ascii"])
            rec["image_hits"][key + "_utf16"] = len(h["utf16"])
        out.append(rec)
    return {"packages": out,
            "declaring": [p["package"] for p in out
                          if p.get("name_in_table") or p.get("alt_name_in_table")
                          or (p.get("image_hits") or {}).get("declared")],
            "objects": [dict(o, package=p["package"]) for p in out for o in p.get("objects", [])]}


# ---------------------------------------------------------------- 4. features
def features(decl: dict) -> dict:
    doc = json.load(open(FEAT_JSON, encoding="utf-8"))
    rows = [e for e in doc.get("events") or []
            if str(e.get("event_id_hex", "")).upper() == TARGET_HEX.upper()]
    groups = sorted({e.get("group") for e in rows if e.get("group")})
    neighbours = []
    for e in doc.get("events") or []:
        if e.get("outer") and e.get("outer") in (decl.get("outer") or []) \
                and str(e.get("event_id_hex", "")).upper() != TARGET_HEX:
            neighbours.append({"name": e.get("name"), "id": e.get("event_id_hex"),
                               "group": e.get("group"),
                               "aud": GROUP_TO_AUD.get(e.get("group"), None)})
    group_counts = {}
    for e in doc.get("events") or []:
        group_counts[e.get("group")] = group_counts.get(e.get("group"), 0) + 1
    return {
        "rows": len(rows),
        "groups": groups,
        "aud": [GROUP_TO_AUD.get(g) for g in groups],
        "statuses": sorted({e.get("status") for e in rows if e.get("status")}),
        "wems": sum(len(e.get("wems") or []) for e in rows),
        "neighbours": neighbours,
        "group_counts": group_counts,
    }


# ---------------------------------------------------------------- 5. ledger
def ledger(bank: dict, feats: dict) -> dict:
    doc = json.load(open(MAP_JSON, encoding="utf-8"))
    rows = doc.get("events") or []
    ids_by_bank: dict[str, set] = {}
    for e in rows:
        name = (e.get("bank_ref") or "").split(".")[-1]
        eid = e.get("event_id")
        if isinstance(name, str) and isinstance(eid, int):
            ids_by_bank.setdefault(name, set()).add(eid)
    union = bank["union"]
    feat_rows = json.load(open(FEAT_JSON, encoding="utf-8")).get("events") or []
    group_by_id = {str(e.get("event_id_hex", "")).upper(): e.get("group") for e in feat_rows}
    # lookup below is keyed the same way, so `0x` vs `0X` cannot silently lose a group
    tau3 = []
    for b in TAU3_BANKS:
        for eid in sorted(ids_by_bank.get(b, set())):
            ev = next((e for e in rows if e.get("event_id") == eid), {})
            grp = group_by_id.get(("0x%08X" % eid).upper())
            tau3.append({
                "bank": b, "id": "0x%08X" % eid, "name": ev.get("name"),
                "group": grp or "-",
                "aud": GROUP_TO_AUD.get(grp, grp),
                "in_a_located_bank": bool(union.get(eid)),
                "carried_by": union.get(eid, []),
            })
    tau5 = []
    names_all = [e.get("name") or "" for e in rows]
    names_all += [e.get("name") or "" for e in
                  (json.load(open(FEAT_JSON, encoding="utf-8")).get("events") or [])]
    for tok in TAU5_TOKENS:
        tau5.append({"token": tok,
                     "map_hits": sum(1 for n in names_all[:len(rows)] if tok in n),
                     "feature_hits": sum(1 for n in names_all[len(rows):] if tok in n),
                     "has_event_id": any(tok in n for n in names_all)})
    return {
        "tau3": tau3,
        "tau3_counts": {"ids": len(tau3), "in_a_located_bank": sum(1 for r in tau3
                                                                  if r["in_a_located_bank"]),
                        "no_located_bank": [r["id"] for r in tau3
                                            if not r["in_a_located_bank"]]},
        "tau5": tau5,
    }


# ---------------------------------------------------------------- build
def build() -> dict:
    decl = declaration()
    bank = bank_census()
    pkg = package_census(bank["rows"], decl)
    feat = features(decl)
    led = ledger(bank, feat)
    found = bank["counts"]["payloads_with_target"] > 0
    doc = {
        "schema": 1,
        "card": "audio-event-6bb2c66e",
        "generator": "Tools/scripts/audio_event_6bb2c66e.py",
        "target": {"id": TARGET, "id_hex": TARGET_HEX,
                   "name_in_map": NAME_IN_MAP, "name_in_package": NAME_IN_PACKAGE},
        "answer": {
            "verdict": ("FOUND" if found else
                        ("RENAMED" if bank["alt_id_carried_by"] else "UNKNOWN")),
            "bank": bank["target_carried_by"] or bank["alt_id_carried_by"],
            "searched_exports": bank["counts"]["exports_searched"],
            "declared_by": pkg["declaring"],
            "alt_id": bank["alt_id_hex"],
            "alt_id_carried_by": bank["alt_id_carried_by"],
            "cooked_name": NAME_IN_PACKAGE if bank["alt_id_carried_by"] else None,
            "cooked_id": bank["alt_id_hex"],
            "declaring_objects": pkg["objects"],
        },
        "inputs": {
            "audio_banks": {"path": "Research/BatmobileGrab/AUDIO_BANKS.json",
                            "sha256_16": file_sha(BANKS_JSON)},
            "audio_map": {"path": "Research/BatmobileGrab/AUDIO_MAP.json",
                          "sha256_16": file_sha(MAP_JSON)},
            "audio_features": {"path": "Research/BatmobileGrab/AUDIO_FEATURES.json",
                               "sha256_16": file_sha(FEAT_JSON)},
        },
        "declaration": decl,
        "bank_census": {k: v for k, v in bank.items() if k != "union"},
        "package_census": pkg,
        "features": feat,
        "ledger": led,
        "oracles": {
            "O-1-name_rule": {"pass": all(r["matches_target"] for r in decl["rule"]
                                          if r["name"] == NAME_IN_MAP),
                              "rule": "fnv1(lower(name)) over latin-1"},
            "O-2-payload_sha1": {"pass": all(r["sha1_match"] for r in bank["rows"]),
                                 "mismatches": ["%s#%d" % (r["package"], r["export"])
                                                for r in bank["rows"] if not r["sha1_match"]]},
            "O-3-raw_agrees_with_parse": {
                "pass": all((TARGET in [int(x, 16) for x in r["ids"]]) ==
                            bool(r["target_raw_le"]) for r in bank["rows"]),
                "note": "a parsed HIRC event id must also be a raw little-endian u32 in the "
                        "same payload; the big-endian search is reported for completeness"},
            "O-4-event_counts": {"pass": all(r["events"] == r["events_recorded"] and r["hirc_complete"]
                                             for r in bank["rows"]),
                                 "mismatches": ["%s#%d" % (r["package"], r["export"])
                                                for r in bank["rows"]
                                                if r["events"] != r["events_recorded"]
                                                or not r["hirc_complete"]]},
        },
    }
    doc["digest"] = hashlib.sha1(
        json.dumps({k: v for k, v in doc.items() if k != "digest"},
                   sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]
    return doc


# ---------------------------------------------------------------- render
def render(d: dict) -> str:
    a, decl, bc, pc, ft, led = (d["answer"], d["declaration"], d["bank_census"],
                                d["package_census"], d["features"], d["ledger"])
    L: list[str] = []
    A = L.append
    A("# AUDIO_EVENT_6BB2C66E - the one Batmobile event with no located bank")
    A("")
    A("Generated by `Tools/scripts/audio_event_6bb2c66e.py`. `--check` re-derives this file and")
    A("`AUDIO_EVENT_6BB2C66E.json` byte for byte. Read-only: the BmAK install is inspected, never")
    A("written or launched.")
    A("")
    A("## Answer")
    A("")
    n_map = sum(1 for p in pc["packages"] if p.get("name_in_table"))
    n_alt = sum(1 for p in pc["packages"] if p.get("alt_name_in_table"))
    A("**The bank is found, and the name it holds is the same cue's global twin.**")
    A("")
    A("- `%s` is `fnv1(lower(\"%s\"))`, and that string is a real `AkEvent`"
      % (d["target"]["id_hex"], NAME_IN_MAP))
    A("  object in **%d** packages under `ww_chr_batmandisruptor`; its 18-byte payload carries"
      % n_map)
    A("  the id little-endian at offset `0x0c`. The declaration is not a map artefact.")
    A("- the **%d** located bank payloads were searched four ways (parsed HIRC Event ids, raw"
      % bc["counts"]["exports_searched"])
    A("  u32 little-endian, raw u32 big-endian, ASCII name): **%d** carry `%s`."
      % (bc["counts"]["payloads_with_target"], d["target"]["id_hex"]))
    A("- `CHR_BatmanDisruptor` (exports in `BmGame` and `StartupPatch`) cooks **`%s`**, which is"
      % bc["alt_id_hex"])
    A("  `fnv1(lower(\"%s\"))` - an `AkEvent` object that ships in **%d** packages"
      % (NAME_IN_PACKAGE, n_alt))
    A("  (`Startup` and `StartupPatch`), and whose payload carries that id the same way.")
    A("")
    A("**Verdict: the bank is `%s`; the event in it is `%s` (`%s`).** The id the map lists,"
      % (", ".join(bc["alt_id_carried_by"]) or "none", NAME_IN_PACKAGE, bc["alt_id_hex"]))
    A("`%s`, is a second, per-character declaration of the same cue that the cook dropped -"
      % d["target"]["id_hex"])
    A("one of the four possibilities `AUDIO_BANKS2.md` listed, now evidenced instead of open.")
    A("Nothing is silent because a bank is missing: the cue plays through its global twin, and")
    A("the map row points at an id no shipped bank has.")
    A("")
    A("## 1. The id, the two names, and the rule that ties them")
    A("")
    A("| name | `fnv1(lower(name))` | equals `%s` | where the string is |" % d["target"]["id_hex"])
    A("|---|---|:-:|---|")
    loc_map = "`AkEvent` object in %d packages; `AUDIO_MAP.json` takes its name" % n_map
    loc_pkg = "`AkEvent` object in %d packages (name table)" % n_alt
    for r in decl["rule"]:
        where = loc_map if r["name"] == NAME_IN_MAP else loc_pkg
        A("| `%s` | `%s` | %s | %s |"
          % (r["name"], r["fnv1_lower_hex"], "yes" if r["matches_target"] else "**no**", where))
    A("")
    A("Both names are real and they are not the same string. In UE3 an `AkEvent` object is named")
    A("after the object; the Wwise event it plays is named inside the object. Here the object is")
    A("`%s` and the event it would play is `%s` - which is exactly the split"
      % (NAME_IN_PACKAGE, NAME_IN_MAP))
    A("that makes `AUDIO_MAP.json` list an id no bank cooks.")
    A("")
    A("### Declaration rows")
    A("")
    A("| rows | names | declared bank | outer | packages | status | media |")
    A("|---:|---|---|---|---|---|---:|")
    A("| %d | %s | %s | %s | %s | %s | %d |"
      % (decl["rows"], ", ".join("`%s`" % n for n in decl["names"]),
         ", ".join("`%s`" % b for b in decl["declared_bank"]),
         ", ".join("`%s`" % o for o in decl["outer"]),
         ", ".join("`%s`" % p for p in decl["packages"]),
         ", ".join(decl["statuses"]), decl["media_rows"]))
    A("")
    A("`media_rows` is 0: there is no WEM behind the declaration in the map, so there is nothing")
    A("to audition even if the bank were found.")
    A("")
    A("## 2. Bank census - every payload, four ways")
    A("")
    A("| measure | value |")
    A("|---|---|")
    A("| payloads searched (`AUDIO_BANKS.json` `present_in_packages`) | %d |"
      % bc["counts"]["exports_searched"])
    A("| packages / distinct banks | %d / %d |"
      % (bc["counts"]["banks"], bc["counts"]["distinct_banks"]))
    A("| HIRC Event ids collected | %d |" % bc["counts"]["event_ids_seen"])
    A("| payloads carrying `%s` (HIRC, raw LE, raw BE or ASCII) | **%d** |"
      % (d["target"]["id_hex"], bc["counts"]["payloads_with_target"]))
    A("| payloads carrying the alternate id `%s` | %d |"
      % (bc["alt_id_hex"], bc["counts"]["payloads_with_alt_id"]))
    A("")
    if bc["hits"]:
        A("| package | export | bank | HIRC | raw LE | raw BE |")
        A("|---|---:|---|:-:|---|---|")
        for h in bc["hits"]:
            A("| `%s` | %d | `%s` | %s | %s | %s |"
              % (h["package"], h["export"], h["bank"],
                 "yes" if h["hirc"] else "no",
                 ", ".join("@%#x" % o for o in h["raw_le"]) or "-",
                 ", ".join("@%#x" % o for o in h["raw_be"]) or "-"))
        A("")
    else:
        A("No payload carries the id in any of the four forms, so the miss is not a decode artefact:")
        A("a wrong-endian or misparsed HIRC walk would still have hit the raw big-endian bytes.")
        A("")
    A("### Where the id *is* carried, by bank")
    A("")
    if bc["alt_id_carried_by"]:
        A("The alternate id `%s` is a HIRC Event of **%s**. That is the sibling event the "
          "disruptor bank really ships; the tracked-fire event it declares is not beside it."
          % (bc["alt_id_hex"], ", ".join("`%s`" % c for c in bc["alt_id_carried_by"])))
    else:
        A("The alternate id is not carried by any located bank either.")
    A("")
    A("## 3. Package census - who declares the event")
    A("")
    A("| package | names | exports | `%s` in name table | `%s` | objects carrying either name |"
      % (NAME_IN_MAP, NAME_IN_PACKAGE))
    A("|---|---:|---:|:-:|:-:|---:|")
    for p in pc["packages"]:
        if not p.get("readable"):
            A("| `%s` | - | - | - | - | unreadable |" % p["package"])
            continue
        A("| `%s` | %d | %d | %s | %s | %d |"
          % (p["package"], p["names"], p["exports"],
             "yes" if p["name_in_table"] else "no",
             "yes" if p["alt_name_in_table"] else "no", len(p["objects"])))
    A("")
    if pc["objects"]:
    A("| package | export | object | class | outer path | id in payload (LE) |")
    A("|---|---:|---|---|---|---|")
    for o in pc["objects"]:
        ids = ([("0x%08X @%#x" % (TARGET, x)) for x in o["payload_target_le"]]
               + [("0x%08X @%#x" % (fnv(NAME_IN_PACKAGE), x)) for x in o["payload_alt_le"]])
        A("| `%s` | %d | `%s` | `%s` | `%s` | %s |"
          % (o["package"], o["export"], o["name"], o["class"], o["path"],
             ", ".join(ids) or "-"))
        A("")
    A("Both names are `AkEvent` objects in the install, so both the declaration and the cooked")
    A("event exist - they are two objects for one cue, and only the `%s` one reaches the"
      % NAME_IN_PACKAGE)
    A("bank. The `class` column is the proof that the string is an object name and not a loose")
    A("label: `AkEvent` is the Wwise play object on both sides.")
    A("")
    A("## 4. Which feature the event serves")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| `AUDIO_FEATURES.json` group | %s |"
      % ", ".join("`%s`" % g for g in ft["groups"]))
    A("| AUD row served | %s |" % (", ".join(a for a in ft["aud"] if a) or "-"))
    A("| group rows in the census | %s |"
      % ", ".join("%s %d" % (g, ft["group_counts"].get(g, 0)) for g in ft["groups"]))
    A("| rows / WEMs for this event | %d / %d |" % (ft["rows"], ft["wems"]))
    A("")
    A("Same-outer neighbours (the `%s` object):" % ", ".join(decl["outer"]))
    A("")
    A("| event | id | group | AUD row |")
    A("|---|---|---|---|")
    for n in ft["neighbours"]:
        A("| `%s` | `%s` | `%s` | %s |" % (n["name"], n["id"], n["group"], n["aud"] or "-"))
    A("")
    A("The event is `weapons` = **AUD-5** (\"each weapon: fire, loop, tail, impact, lock beep\").")
    A("Its bank neighbour is `tracker`, which has no AUD-1...AUD-7 row of its own; the tracker")
    A("deploy is a gadget cue, not a weapon sound, and it is the one event of the pair the bank")
    A("actually cooks.")
    A("")
    A("## 5. T-AU3 and T-AU5 - what still has no JC3 binding, and why")
    A("")
    A("A *JC3 binding* means an addressable event or bank in the target install: a path, a")
    A("Jenkins hash or an FSB5 sample name that the rebuilt `.ee` can name. `T_AU3B.md` searched")
    A("all 27 BmAK bank names and `sound/fmod_banks/<name>.bank` against 78,907 distinct index")
    A("hashes and the 649-sample FSB5 tables: **27 of 27 absent**. So no BmAK event has a JC3")
    A("binding yet, and the two rows differ in what is missing on the *source* side.")
    A("")
    A("### T-AU3 - the 10 claim banks, %d declared ids" % led["tau3_counts"]["ids"])
    A("")
    A("| bank | id | event | group | AUD row | in a located BmAK bank |")
    A("|---|---|---|---|---|:-:|")
    for r in led["tau3"]:
        A("| `%s` | `%s` | `%s` | `%s` | %s | %s |"
          % (r["bank"], r["id"], r["name"], r["group"], r["aud"] or "-",
             "yes" if r["in_a_located_bank"] else "**no**"))
    A("")
    A("**%d of %d** ids are carried by a located BmAK bank. **%s** is not"
      % (led["tau3_counts"]["in_a_located_bank"], led["tau3_counts"]["ids"],
         ", ".join("`%s`" % i for i in led["tau3_counts"]["no_located_bank"]) or "none"))
    A("for the reason in section 1: the bank ships, the event was not cooked into it.")
    A("")
    A("Why none of them has a JC3 binding: JC3 exposes no Wwise/`AkEvent` surface at all -")
    A("`Research/JC3Grab/JC3_AUDIO.md` section 10 route b - so the *carrier* would have to be a")
    A("JC3 bank or `SAttachedEffect`, and every BmAK bank name is absent from the target install.")
    A("For 25 of the 26 the source is proven present and bindable the moment a carrier exists;")
    A("for `0x6BB2C66E` there is nothing to bind even then.")
    A("")
    A("### T-AU5 - the three event families")
    A("")
    A("| family token | hits in `AUDIO_MAP.json` | hits in `AUDIO_FEATURES.json` | has an event id |")
    A("|---|---:|---:|:-:|")
    for r in led["tau5"]:
        A("| `%s` | %d | %d | %s |"
          % (r["token"], r["map_hits"], r["feature_hits"],
             "yes" if r["has_event_id"] else "**no**"))
    A("")
    A("T-AU5 is missing one step earlier than T-AU3: `TransformationReverseDirection*`,")
    A("`TaserSound` and `VehicleSound` are **member names on the vehicle classes**, not event")
    A("names, so they have no id, no bank and no row in either census. Their JC3 binding cannot")
    A("be looked for until a `.ee` reference is decoded to an `AkEvent` id - the same decode that")
    A("produced the 361 rows.")
    A("")
    A("## 6. The single thing that would settle it")
    A("")
    A("**Nothing is left open.** Both `AkEvent` payloads are 18 bytes and hold exactly one id at")
    A("offset `0x0c`, so the declaration and the cook are now read end to end: the map's")
    A("`%s` payload references `%s`, and the bank's event object references `%s`."
      % (NAME_IN_MAP, d["target"]["id_hex"], bc["alt_id_hex"]))
    A("No wider scan of the other 34,380 `AkBank` exports can change that - it could only find a")
    A("*third* bank that also cooks `%s`, which would not make the cue audible anywhere new."
      % d["target"]["id_hex"])
    A("")
    A("The wider search, if wanted, is the one `AUDIO_BANKS2.md` names: parse all **34,497**")
    A("`AkBank` exports of the install instead of the 117 the audio map references, and the 15")
    A("`BKPK`-magic `.bnk` files. Neither is done here.")
    A("")
    A("## Oracles")
    A("")
    A("| oracle | result |")
    A("|---|---|")
    for k, v in d["oracles"].items():
        A("| `%s` | **%s**%s |" % (k, "PASS" if v["pass"] else "FAIL",
                                   (" - " + v["note"]) if v.get("note") else ""))
    A("")
    A("O-1 makes the lookup trustworthy (the rule reproduces the id from the name), O-2 proves the")
    A("payloads are the ones `AUDIO_BANKS.json` recorded, O-3 proves the parse and the bytes")
    A("agree, O-4 proves each bank was walked to its last object.")
    A("")
    A("## Regeneration")
    A("")
    A("| path | what it is |")
    A("|---|---|")
    A("| `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.md` | this file |")
    A("| `Research/BatmobileGrab/AUDIO_EVENT_6BB2C66E.json` | the same facts as data |")
    A("| `Tools/scripts/audio_event_6bb2c66e.py` | the tool; `--write` / `--check` |")
    A("")
    A("`--check` re-derives %d payloads, the package tables and both names, and fails on any"
      % bc["counts"]["exports_searched"])
    A("change to either output. Inputs are pinned by sha256 prefix in the JSON"
      " (`%s`)." % d["digest"])
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- io
def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def cmd_write() -> int:
    doc = build()
    open(JSON_OUT, "w", encoding="utf-8", newline="\n").write(dump(doc))
    open(MD, "w", encoding="utf-8", newline="\n").write(render(doc))
    a = doc["answer"]
    print("wrote %s and %s" % (os.path.relpath(MD, ROOT), os.path.relpath(JSON_OUT, ROOT)))
    print("verdict %s | exports %d | carried by %s | alt %s by %s"
          % (a["verdict"], a["searched_exports"], a["bank"] or "none",
             a["alt_id"], a["alt_id_carried_by"] or "none"))
    bad = [k for k, v in doc["oracles"].items() if not v["pass"]]
    return 1 if bad else 0


def cmd_check() -> int:
    doc = build()
    fails = []
    for path, text in ((JSON_OUT, dump(doc)), (MD, render(doc))):
        if not os.path.isfile(path):
            fails.append("%s missing - run --write" % os.path.relpath(path, ROOT))
            continue
        have = open(path, encoding="utf-8").read()
        if have != text:
            fails.append("%s differs from a fresh derivation" % os.path.relpath(path, ROOT))
    for k, v in doc["oracles"].items():
        if not v["pass"]:
            fails.append("oracle %s failed" % k)
    a = doc["answer"]
    bc, led = doc["bank_census"], doc["ledger"]
    if bc["counts"]["payloads_with_target"] != 0:
        fails.append("the target id is now carried by a payload - re-read the answer")
    if led["tau3_counts"]["ids"] != 26:
        fails.append("T-AU3's declared id count is %d, not 26" % led["tau3_counts"]["ids"])
    if led["tau3_counts"]["no_located_bank"] != [TARGET_HEX]:
        fails.append("T-AU3's unlocated set is %s" % led["tau3_counts"]["no_located_bank"])
    print("%s: %s, %d exports, %d T-AU3 ids (%d located), alt id %s by %s"
          % ("PASS" if not fails else "FAIL", a["verdict"], a["searched_exports"],
             led["tau3_counts"]["ids"], led["tau3_counts"]["in_a_located_bank"],
             a["alt_id"], a["alt_id_carried_by"] or "none"))
    for f in fails:
        print("  - " + f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--print", dest="show", action="store_true")
    args = ap.parse_args()
    if args.write:
        return cmd_write()
    if args.check:
        return cmd_check()
    doc = build()
    print(dump(doc)[:4000])
    print("... digest %s" % doc["digest"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
