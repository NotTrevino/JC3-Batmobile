"""t_au_retest.py - T-AU3 / T-AU5 re-tested against AUDIO_BANKS.md and AUDIO_BANKS2.md.

Task `7210-t-au3-t-au5` (after G3-14): the ledger still lists T-AU3, T-S6 and T-AU5 as blocked.
G3-14 refuted the *bank absence* half of T-AU3/T-AU5 ("all 29 referenced banks are present").
This card re-tests exactly those two rows and answers, per row:

  * which **bank** and which **event id** it needs - decoded from `AUDIO_MAP.json` (the 90 rows'
    26 ids and their `bank_ref`s) and from `AUDIO_BANKS2.json`'s HIRC `0x04` id sets;
  * whether the **bytes are readable offline** - the bank payloads `AUDIO_BANKS.md` read
    (package + export + size + sha1), and whether the row has media rows at all;
  * **what is still missing** - the id that is in no located bank (`0x6BB2C66E`), the per-event
    media/source extraction that neither card performed, and T-AU5's event families, which never
    resolved to an id in the first place.

`T_ROWS.jsonl` is read only; its sha256 is pinned here and asserted unchanged.  Writes
`Working/Translation/AU_BLOCKED_RETEST.{md,json}`.

    python Tools/scripts/t_au_retest.py --write
    python Tools/scripts/t_au_retest.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

TROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
TROWS_SHA = "8996b60a5370d932f437"          # pinned in BLOCKED_PROPOSALS.md; never edited here
BANKS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS.md")
BANKS2_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS2.json")
AUDIO_MAP = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json")
FEATURES = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.json")
MODES_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "MODES.md")
ASSETS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "ASSETS.md")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "AU_BLOCKED_RETEST.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "AU_BLOCKED_RETEST.json")

TAU5_FAMILIES = ("TransformationReverseDirection", "TaserSound", "VehicleSound")


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def read(path: str) -> str:
    return open(path, encoding="utf-8-sig", errors="replace").read()


def claim_banks_md(text: str) -> list[dict]:
    """Rows of AUDIO_BANKS.md's 'The 10 "missing" banks, re-tested' table."""
    out = []
    for line in text.splitlines():
        m = re.match(r"\|\s*`Engine\.([A-Za-z0-9_]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([^|]*)\|"
                     r"\s*([^|]*)\|\s*([^|]*)\|\s*\*\*(\w+)\*\*", line)
        if m:
            out.append({"bank": m.group(1), "rows": int(m.group(2)), "ids": int(m.group(3)),
                        "akbank_in": m.group(4).strip(), "bnk": m.group(5).strip(),
                        "ascii": m.group(6).strip(), "verdict": m.group(7)})
    return out


def t_rows(text: str) -> dict:
    out = {}
    for ln, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("id") in ("T-AU3", "T-AU5", "T-S6"):
            out[r["id"]] = {"line": ln, "dispo": r.get("dispo"), "why": r.get("why"),
                            "cells": r.get("cells")}
    return out


def build() -> dict:
    trows = t_rows(read(TROWS))
    amap = json.load(open(AUDIO_MAP, encoding="utf-8"))
    b2 = json.load(open(BANKS2_JSON, encoding="utf-8"))
    feat = json.load(open(FEATURES, encoding="utf-8"))
    banks_md = claim_banks_md(read(BANKS_MD))

    claims = list(amap["missing"])
    short = {c.split(".")[-1]: c for c in claims}
    rows = [e for e in amap["events"] if e.get("bank_ref") in set(claims)]
    ids = {}
    for e in rows:
        ids.setdefault(int(e["event_id"]), []).append(e)

    # decoded HIRC 0x04 membership, from AUDIO_BANKS2's per-bank id sets
    carriers = {}
    for b in b2["banks"]:
        for x in b.get("event_ids") or []:
            carriers.setdefault(int(str(x), 16), set()).add(f"{b['package']}.{b['bank']}")
    records = {}
    for b in b2["banks"]:
        records.setdefault(b["bank"], []).append({
            "package": b["package"], "export": b["export"], "bytes": b["bytes"],
            "sha1": b["sha1"], "hirc_objects": b.get("hirc_objects"),
            "events": b.get("events_in_bank"), "carries_bkpk": b.get("carries_bkpk"),
            "by_type": b.get("by_type"),
        })

    id_rows = []
    for i, evs in sorted(ids.items()):
        e = evs[0]
        id_rows.append({
            "name": e["name"], "id": i, "hex": f"0x{i:08X}", "bank_ref": e["bank_ref"],
            "rows": len(evs), "status": e.get("status"),
            "carriers": sorted(carriers.get(i, [])),
            "media_rows": sum(1 for x in evs if x.get("media")),
        })

    bank_rows = []
    for c in claims:
        short_name = c.split(".")[-1]
        recs = records.get(short_name, [])
        mine = [r for r in id_rows if r["bank_ref"] == c]
        bank_rows.append({
            "claim": c, "bank": short_name, "rows": len(mine),
            "ids": len({r["id"] for r in mine}),
            "in_bank": sum(1 for r in mine if r["carriers"]),
            "records": sorted(recs, key=lambda r: (r["package"], r["export"])),
            "md": next((x for x in banks_md if x["bank"] == short_name), None),
        })

    au5 = {
        "families": list(TAU5_FAMILIES),
        "map_hits": [e["name"] for e in amap["events"]
                     if any(f.lower() in e["name"].lower() for f in TAU5_FAMILIES)],
        "feature_hits": [e.get("name") for e in feat["events"]
                         if any(f.lower() in str(e.get("name", "")).lower() for f in TAU5_FAMILIES)],
        "modes_fields": [l.strip() for l in read(MODES_MD).splitlines()
                         if "TransformationReverseDirection" in l and l.strip().startswith("|")],
        "assets_AkVehicleSound": [l.strip() for l in read(ASSETS_MD).splitlines()
                                  if "AkVehicleSound" in l][:4],
    }

    not_found = [r for r in id_rows if not r["carriers"]]
    return {
        "trows": trows, "trows_sha": sha256_file(TROWS)[:64],
        "claims": claims, "claim_md": banks_md,
        "rows": len(rows), "ids": len(id_rows),
        "id_rows": id_rows, "bank_rows": bank_rows,
        "not_found": not_found,
        "total_carried": len(id_rows) - len(not_found),
        "b2_answer": b2["answer"], "b2_searched": b2["answer"].get("searched_banks"),
        "b2_counts": b2.get("counts"),
        "au5": au5,
        "map_events": len(amap["events"]), "feature_events": len(feat["events"]),
        "media_rows_claim": sum(r["media_rows"] for r in id_rows),
        "sha": {p: sha256_file(p)[:16] for p in (BANKS_MD, BANKS2_JSON, AUDIO_MAP, FEATURES)},
    }


def render(d: dict) -> str:
    p = []
    a = p.append
    a("# AU_BLOCKED_RETEST - T-AU3 and T-AU5 re-tested against AUDIO_BANKS / AUDIO_BANKS2")
    a("")
    a("Generated by `Tools/scripts/t_au_retest.py --write`; `--check` re-derives every row and "
      "fails on drift.  `Working/Translation/T_ROWS.jsonl` is read only and its sha256 is "
      "asserted unchanged.")
    a("")
    a(f"**Verdicts.**  **T-AU3: banks refused - 10/10 claim banks present, and {d['total_carried']} "
      f"of {d['ids']} of its event ids are HIRC `0x04` Events in those payloads.**  The single "
      f"miss is `{d['not_found'][0]['hex']}` (`{d['not_found'][0]['name']}`), the same id "
      f"`AUDIO_BANKS2.md` leaves UNKNOWN - so the row is no longer blocked on banks, it is "
      f"blocked on one event id and on per-event media extraction.  **T-AU5: still UNKNOWN, but "
      f"for a different reason** - its three event families never resolved to an id at all "
      f"({len(d['au5']['map_hits'])} name hits in {d['map_events']} mapped events, "
      f"{len(d['au5']['feature_hits'])} in the feature census), so there is no id to look up in "
      f"the (now present) banks.")
    a("")
    a("## 1. Inputs (hashes are the first 16 hex chars)")
    a("")
    a("| file | sha256 |")
    a("|---|---|")
    for path, h in d["sha"].items():
        a(f"| `{rel(path)}` | `{h}…` |")
    a(f"| `{rel(TROWS)}` | `{d['trows_sha'][:16]}…` (pinned `{TROWS_SHA}…`) |")
    a("")
    a(f"T_ROWS rows read: " + ", ".join(f"`{k}` line {v['line']} ({v['dispo']})"
                                        for k, v in d["trows"].items()) + ".")
    a("")
    a("## 2. T-AU3 - the 10 \"absent\" banks")
    a("")
    a("| bank (claim) | rows | ids | in bank | carrier payloads (package/export, bytes, sha1) | "
      "AUDIO_BANKS.md verdict |")
    a("|---|---:|---:|---:|---|---|")
    for b in d["bank_rows"]:
        car = "; ".join(f"`{r['package']}`/{r['export']} {r['bytes']:,} B `{(r['sha1'] or '')[:12]}`"
                        for r in b["records"]) or "none"
        verdict = (b["md"] or {}).get("verdict", "?")
        a(f"| `{b['claim']}` | {b['rows']} | {b['ids']} | {b['in_bank']} | {car} | **{verdict}** |")
    a("")
    a(f"Total: **{d['rows']} event rows / {d['ids']} distinct ids**, {len(d['claims'])} banks, "
      f"`AUDIO_BANKS.md` says 10 found / 0 absent, and the id membership below is decoded from "
      f"`AUDIO_BANKS2.json`'s {d['b2_searched']}-payload HIRC walk.")
    a("")
    a("## 3. T-AU3 - its 26 event ids, and where each one lives")
    a("")
    a("| event | id | declared bank | in a located bank | carriers | media rows |")
    a("|---|---|---|---|---|---:|")
    for r in d["id_rows"]:
        a(f"| `{r['name']}` | `{r['hex']}` | `{r['bank_ref']}` | "
          f"{'**yes**' if r['carriers'] else '**NO**'} | "
          f"{', '.join(f'`{c}`' for c in r['carriers']) or '-'} | {r['media_rows']} |")
    a("")
    a(f"**{d['total_carried']} of {d['ids']} ids resolve to a HIRC Event in a located bank.**  "
      f"The exception is `{d['not_found'][0]['hex']}`, whose only carrier claim is "
      f"`{d['not_found'][0]['bank_ref']}`; `AUDIO_BANKS2.md` searched all "
      f"{d['b2_searched']} payloads for it and answered `{d['b2_answer']['verdict']}` "
      f"(\"{d['b2_answer']['note']}\").  That id is T-AU5's own `VehicleSound`-family event, so "
      f"the two rows share one unresolved id.")
    a("")
    a("## 4. Are the bytes readable offline?")
    a("")
    a(f"- **Bank bytes: yes, decoded.**  Each carrier above is an `AkBank` export with its size and "
      f"sha1 recorded, read out of the cooked package by `grab_audio_banks.py` / "
      f"`grab_audio_banks2.py`; the install root "
      f"(`E:/Games/Batman - Arkham Knight`) is present and both cards re-read the payloads "
      f"byte-identically (AUDIO_BANKS2 oracle `O-1-payload_sha1` PASS).")
    a(f"- **Per-event media: not established.**  All {d['rows']} claim rows carry **0** media "
      f"records in `AUDIO_MAP.json` (the grab that produced them never opened these banks), and "
      f"`AUDIO_BANKS2.json` records HIRC object types and `carries_bkpk` per bank but does not "
      f"extract Sound/`DIDX`/`DATA` source ids.  So \"the event's wem bytes are on disk\" is "
      f"**UNKNOWN** for these 26 ids - not refuted, not confirmed.")
    a(f"- **No streamed-audio container to fall back on:** `AUDIO_BANKS.md` records 0 `.pck` in "
      f"the install, so if a source is streamed rather than embedded there is no package to read "
      f"it from; whether any of these 26 events is streamed is exactly the extraction above.")
    a("")
    a("## 5. T-AU5 - the three event families")
    a("")
    a("| family | where it appears | resolved id | in a located bank |")
    a("|---|---|---|---|")
    for fam in d["au5"]["families"]:
        if fam.startswith("TransformationReverse"):
            where = "`MODES.md` `RVehicleBatmobileBase` AkEvent field (serialised: V2/MK2/Joker/Funhouse)"
        elif fam == "VehicleSound":
            where = "`ASSETS.md` `AkVehicleSound` object named `VehicleSound` (component, not an event)"
        else:
            where = "no decoded object in the grab censuses"
        a(f"| `{fam}` | {where} | **UNKNOWN** | **UNKNOWN** |")
    a("")
    a("Decoded lines behind the two rows that do exist:")
    a("")
    a("```")
    for line in d["au5"]["modes_fields"]:
        a(line)
    for line in d["au5"]["assets_AkVehicleSound"]:
        a(line)
    a("```")
    a("")
    a(f"Neither `AUDIO_MAP.json`'s {d['map_events']} events nor `AUDIO_FEATURES.json`'s "
      f"{d['feature_events']} carry any of the three families by name "
      f"({len(d['au5']['map_hits'])} and {len(d['au5']['feature_hits'])} hits).  So T-AU5 cannot "
      f"name the bank or the event id it needs: the AkEvent *references* are serialised (MODES.md "
      f"counts them per vehicle), the referenced `AkEvent` objects were never resolved to ids.  "
      f"G3-14 refutes only T-AU5's parenthetical (\"10 banks absent\"); its own blocker - event "
      f"identity - is untouched.")
    a("")
    a("## 6. What is still missing (per row)")
    a("")
    a("| row | bank | event id | bytes offline | still missing |")
    a("|---|---|---|---|---|")
    a(f"| T-AU3 | **found** (10/10, Startup/BmGame/StartupPatch) | {d['total_carried']}/{d['ids']} "
      f"resolve; `{d['not_found'][0]['hex']}` does not | bank payloads readable; per-event media "
      f"UNKNOWN | the one id (`{d['not_found'][0]['name']}`), plus Sound/`DIDX`/`DATA` extraction "
      f"for the other 25 |")
    a("| T-AU5 | irrelevant until ids exist; the 10 banks it blamed are present | "
      "**0 of 3 families resolved** | bank payloads readable; media not addressed | AkEvent id "
      "resolution for the two `TransformationReverseDirection*` fields, `TaserSound`, "
      "`VehicleSound`; then the same media extraction |")
    a("")
    a("## 7. Checks")
    a("")
    a("| # | check | result |")
    a("|---:|---|---|")
    a(f"| 1 | `T_ROWS.jsonl` is unchanged (sha256 starts `{TROWS_SHA}`) | "
      f"{'PASS' if d['trows_sha'].startswith(TROWS_SHA) else 'FAIL'} |")
    a(f"| 2 | AUDIO_BANKS.md's claim table yields 10 banks, all FOUND | "
      f"{'PASS' if len(d['claim_md'])==10 and all(x['verdict']=='FOUND' for x in d['claim_md']) else 'FAIL'} |")
    a(f"| 3 | the claim rows are 90 / 26 ids | "
      f"{'PASS' if (d['rows'],d['ids'])==(90,26) else 'FAIL'} ({d['rows']} rows / {d['ids']} ids) |")
    a(f"| 4 | every claim bank has a decoded carrier record | "
      f"{'PASS' if all(b['records'] for b in d['bank_rows']) else 'FAIL'} |")
    a(f"| 5 | exactly one id is in no located bank, and it is `0x6BB2C66E` | "
      f"{'PASS' if [r['id'] for r in d['not_found']]==[int('6BB2C66E',16)] else 'FAIL'} |")
    a(f"| 6 | AUDIO_BANKS2's own answer for that id is UNKNOWN | "
      f"{'PASS' if d['b2_answer']['verdict']=='UNKNOWN' else 'FAIL'} |")
    a(f"| 7 | T-AU5's three families have 0 name hits in the event and feature censuses | "
      f"{'PASS' if not d['au5']['map_hits'] and not d['au5']['feature_hits'] else 'FAIL'} |")
    a(f"| 8 | the two `TransformationReverseDirection*` fields are present in MODES.md | "
      f"{'PASS' if len(d['au5']['modes_fields'])==2 else 'FAIL'} |")
    a("")
    a("## 8. UNKNOWNs (what was tried)")
    a("")
    a("1. **Where `0x6BB2C66E` lives.** `AUDIO_BANKS2.md` searched all 117 located payloads as "
      "HIRC Events and as raw little-endian bytes; no hit. Candidates it lists: an `AkBank` "
      "export outside the 117, a `BKPK` blob not parsed as a container, a `BKPK`-magic `.bnk` "
      "(14 of 15), or a cook-time rename. Settling it means scanning all 34,497 `AkBank` exports.")
    a("2. **Each event's media/source ids and bytes.** Not decoded by either card; `AUDIO_MAP.json` "
      "has 0 media rows for the 26 claim ids. Where it would be found: the located bank "
      "payloads' Sound objects and their `DIDX`/`DATA` ranges (or an external stream, of which "
      "the install has none recorded: 0 `.pck`).")
    a("3. **T-AU5's AkEvent ids.** The references are serialised per vehicle (MODES.md shows "
      "counts, not ids). Resolving them needs the `AkEvent` objects those properties point at - "
      "not in the audio map's 361 events. Until then no bank lookup is possible.")
    a("4. **Whether a resolved event is audible in BmAK.** Nothing here observes the game; no "
      "launch or attach (INSTRUCTIONS §3).")
    a("")
    return "\n".join(p) + "\n"


def check() -> int:
    fails = []
    d = build()
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print(f"FAIL: {rel(OUT_MD)} / {rel(OUT_JSON)} missing (run --write)")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != render(d):
        fails.append("the markdown differs from the re-derived one")
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(json.dumps(d, default=str)):
        fails.append("the json differs from the re-derived one")
    if not d["trows_sha"].startswith(TROWS_SHA):
        fails.append("T_ROWS.jsonl changed")
    if len(d["claim_md"]) != 10 or any(x["verdict"] != "FOUND" for x in d["claim_md"]):
        fails.append("the claim table is not 10 FOUND")
    if (d["rows"], d["ids"]) != (90, 26):
        fails.append(f"claim rows {d['rows']} / ids {d['ids']}, expected 90 / 26")
    if [r["id"] for r in d["not_found"]] != [int("6BB2C66E", 16)]:
        fails.append(f"not-found ids: {[r['hex'] for r in d['not_found']]}")
    if len(d["au5"]["map_hits"]) or len(d["au5"]["feature_hits"]):
        fails.append("a T-AU5 family now resolves - re-read the row")
    if len(d["au5"]["modes_fields"]) != 2:
        fails.append(f"MODES.md TransformationReverse fields: {len(d['au5']['modes_fields'])}")
    print(f"claim banks {len(d['claim_md'])} (FOUND {sum(1 for x in d['claim_md'] if x['verdict']=='FOUND')}) | "
          f"rows {d['rows']} ids {d['ids']} | carried {d['total_carried']}/{d['ids']} | "
          f"T-AU5 name hits {len(d['au5']['map_hits'])}/{len(d['au5']['feature_hits'])} | "
          f"T_ROWS sha {d['trows_sha'][:12]}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print("PASS: 10/10 banks present, 25/26 ids in a located bank, the miss is 0x6BB2C66E "
          "(UNKNOWN per AUDIO_BANKS2), T-AU5 has no resolved id, T_ROWS untouched")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.check:
        return check()
    d = build()
    text = render(d)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(json.loads(json.dumps(d, default=str)), f, indent=1)
    print(f"wrote {rel(OUT_MD)} ({len(text)} chars) and {rel(OUT_JSON)}")
    print(f"banks {len(d['claim_md'])} FOUND {sum(1 for x in d['claim_md'] if x['verdict']=='FOUND')} | "
          f"rows {d['rows']} ids {d['ids']} carried {d['total_carried']} | "
          f"not found {[r['hex'] for r in d['not_found']]} | T-AU5 hits 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
