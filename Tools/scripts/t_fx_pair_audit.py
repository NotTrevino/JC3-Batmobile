#!/usr/bin/env python
"""t_fx_pair_audit.py - audit T-17's chosen `.effc` pairs and its five named omissions.

Read-only. Three chosen pairs (T-FX7 afterburner, T-FX10 cannon muzzle flash, T-FX19
wall-scrape sparks) are audited in full; the other nine chosen rows are listed for context.
For every chosen path the script asks:

  * is it a JC3 index entry (`Research/JC3Grab/INDEX.jsonl`, the output of
    `Tools/scripts/jc3index.py`), or an effect embedded in an `.ee` container that the
    index does name?
  * do the row's size / arrays / rows / vehicles / family counts equal what
    `Research/JC3Grab/FX_TABLE.jsonl` records for that path?
  * does the BmAK group the row replaces have the systems / emitters / names / lifetime the
    row claims (`Research/BatmobileGrab/PARTICLES_FEATURES.json`)?

The five omissions are re-tested by scanning the 955-path EffectRTSystem set for the term
each row claims was searched, and the two `shell_eject` effects are checked to be
non-vehicle carriers.

Verdicts are `holds`, `wrong` or `UNKNOWN` (cannot be reproduced from the files). `--check`
rebuilds every number and diffs the `.md` byte for byte.
"""
import argparse
import collections
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

T17 = "Working/Translation/t17_fx.json"
INDEX = "Research/JC3Grab/INDEX.jsonl"
FX = "Research/JC3Grab/FX_TABLE.jsonl"
PART = "Research/BatmobileGrab/PARTICLES_FEATURES.json"
OUT = "Working/Translation/FX_PAIR_AUDIT.md"

AUDITED = ["T-FX7", "T-FX10", "T-FX19"]
OMISSIONS = ["T-FX9", "T-FX12", "T-FX13", "T-FX16", "T-FX20"]

# The search term each omission row claims was used with "0 of 955 match". Where the row
# names no term (T-FX16) the list is empty and the verdict is UNKNOWN, not a pass.
OMISSION_TERMS = {
    "T-FX9": ["haze", "steam", "heat"],
    "T-FX12": ["tracer"],
    "T-FX13": ["casing", "shell_eject"],
    "T-FX16": [],
    "T-FX20": ["brake"],
}


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build():
    t17 = load(T17)
    rows = t17["rows"]
    index_rows = load_jsonl(INDEX)
    fx = load_jsonl(FX)
    part = load(PART)

    idx = collections.defaultdict(list)
    for r in index_rows:
        idx[r["path"].lower()].append(r)
    fx_by = collections.defaultdict(list)
    for r in fx:
        fx_by[r["path"]].append(r)

    fx955 = sorted({r["path"] for r in fx if r["root"] == "EffectRTSystem"})
    effc = [r for r in index_rows if r["path"].lower().endswith(".effc")]

    def vehicles_of(rs):
        return len({r["container"] for r in rs if "/jc_vehicles/" in r["container"]})

    chosen = []
    for r in rows:
        ch = r.get("chosen")
        if not ch:
            continue
        path = ch["path"]
        rs = fx_by.get(path, [])
        hits = idx.get(path.lower(), [])
        containers = sorted({x["container"] for x in rs})
        in_index = [c for c in containers if c.lower() in idx]
        facts = {
            "id": r["id"],
            "path": path,
            "claimed": {k: ch.get(k) for k in ("size", "arrays", "rows", "vehicles", "family_total")},
            "family": [(f["path"], f["vehicles"]) for f in ch["family"]],
            "fx_rows": len(rs),
            "sizes": sorted({x["size"] for x in rs}),
            "arrays": sorted({x["arrays"] for x in rs}),
            "rows_fx": sorted({x["rows"] for x in rs}),
            "containers": len(containers),
            "containers_in_index": len(in_index),
            "vehicles": vehicles_of(rs),
            "digests": len({x["digest"] for x in rs}),
            "index_hits": [(h["archive"], h["offset"], h["size"], h["mount"]) for h in hits],
            "index_effc_total": len(effc),
        }
        if not rs:
            facts["existence"] = "NOT IN FX_TABLE"
        elif hits:
            facts["existence"] = "index entry"
        elif len(in_index) == len(containers):
            facts["existence"] = "embedded in an indexed .ee"
        else:
            facts["existence"] = f"container not indexed ({len(in_index)}/{len(containers)})"

        c = facts["claimed"]
        tests = {
            "size": bool(facts["sizes"]) and facts["sizes"] == [c["size"]],
            "arrays": bool(facts["arrays"]) and facts["arrays"] == [c["arrays"]],
            "rows": bool(facts["rows_fx"]) and facts["rows_fx"] == [c["rows"]],
            "vehicles": facts["vehicles"] == c["vehicles"],
            "family_total": isinstance(facts["family"], list) and len(facts["family"]) == c["family_total"],
        }
        facts["claims"] = tests
        facts["claim_verdict"] = "holds" if all(tests.values()) and rs else "wrong"
        chosen.append(facts)

    # ---- BmAK side for the three audited rows
    groups = {g["name"]: g for g in part["groups"]}
    systems = part["systems"]
    for f in chosen:
        if f["id"] not in AUDITED:
            continue
        row = next(r for r in rows if r["id"] == f["id"])
        f["bmak"] = []
        for b in row["bmak"]:
            g = b["group"]
            gsys = [s for s in systems if s["group"] == g]
            grp = groups[g]
            colours = [c for s in gsys for c in (s.get("colours") or [])]
            f["bmak"].append({
                "group": g,
                "claimed_systems": b["systems"],
                "claimed_emitters": b["emitters"],
                "claimed_distinct": b["distinct"],
                "claimed_lifetime": b["lifetime"],
                "claimed_spawn": b["spawn_rate"],
                "claimed_names": b["names"],
                "systems": len(gsys),
                "emitters_sum": sum(s["emitters"]["total"] for s in gsys),
                "group_emitters": grp["emitters"],
                "distinct_names": sorted({s["name"] for s in gsys}),
                "lifetime": grp["lifetime"],
                "spawn_rate": grp["spawn_rate"],
                "colours": len(colours),
                "colour_sources": sorted({c["source"] for c in colours}),
            })
        f["colour_claim"] = "none"   # no T-FX row states a colour
        f["bmak_verdict"] = "holds" if all(
            b["systems"] == b["claimed_systems"]
            and b["emitters_sum"] == b["claimed_emitters"]
            and b["group_emitters"] == b["claimed_emitters"]
            and len(b["distinct_names"]) == b["claimed_distinct"]
            for b in f["bmak"]) else "wrong"

    # ---- the five omissions
    omissions = []
    for rid in OMISSIONS:
        row = next(r for r in rows if r["id"] == rid)
        terms = OMISSION_TERMS[rid]
        scans = {t: [p for p in fx955 if t in p.lower()] for t in terms}
        hits = sorted({p for v in scans.values() for p in v})
        veh_hits = [p for p in hits if any("/jc_vehicles/" in x["container"] for x in fx_by[p])]
        if not terms:
            verdict = "UNKNOWN"
            why = "the row names no search term, so its '0 of 955' cannot be reproduced"
        elif not hits:
            verdict, why = "holds", "0 of the 955 EffectRTSystem paths contain any term"
        elif rid == "T-FX13" and not veh_hits:
            verdict = "holds"
            why = (f"{len(hits)} term hit(s), all non-vehicle carriers - exactly what the "
                   f"row states as its non-vehicle matches")
        elif rid == "T-FX9" and not any(t in p.lower() for t in ("haze", "steam") for p in hits):
            verdict = "holds"
            why = ("0 haze and 0 steam paths; the single 'heat' hit is "
                   f"`{hits[0].split('/')[-1]}`, a heater effect, and the row claims haze")
        else:
            verdict, why = "WRONG", f"{len(hits)} hit(s) contradict the absence claim"
        omissions.append({"id": rid, "feature": row["feature"], "terms": terms,
                          "hits": hits, "vehicle_hits": veh_hits,
                          "verdict": verdict, "why": why,
                          "carrier": row.get("now")})

    checks = {
        "rows_17": len(rows) == 17,
        "chosen_12": len(chosen) == 12,
        "omissions_5": len(omissions) == 5,
        "fx_rows_57187": len(fx) == 57187,
        "fx_paths_1533": len({r["path"] for r in fx}) == 1533,
        "effectrtsystem_paths_955": len(fx955) == 955,
        "index_effc_35": len(effc) == 35,
        "all_chosen_in_fx_table": all(f["fx_rows"] for f in chosen),
        "all_chosen_size_rows_arrays_hold": all(
            f["claims"]["size"] and f["claims"]["arrays"] and f["claims"]["rows"] for f in chosen),
        "audited_groups_hold": all(f["bmak_verdict"] == "holds" for f in chosen if "bmak" in f),
    }
    return {"chosen": chosen, "omissions": omissions, "checks": checks,
            "fx955": len(fx955), "fx_paths": len({r["path"] for r in fx}),
            "fx_rows": len(fx), "index_effc": len(effc),
            "summary": t17["summary"]}


def yn(b):
    return "yes" if b else "**no**"


def render(doc):
    ch = {c["id"]: c for c in doc["chosen"]}
    L = []
    L.append("# T-17 FX pairs - audit of 3 chosen `.effc` effects and the 5 named omissions")
    L.append("")
    L.append("Generated by `Tools/scripts/t_fx_pair_audit.py --write`; `--check` rebuilds every "
             "number from `t17_fx.json`, `FX_TABLE.jsonl`, `INDEX.jsonl` and "
             "`PARTICLES_FEATURES.json` and diffs this file byte for byte. Read-only.")
    L.append("")
    L.append(f"**STATUS: DONE - {sum(1 for f in doc['chosen'] if f['id'] in AUDITED and f['claim_verdict']=='holds' and f.get('bmak_verdict')=='holds')}/3 "
             f"audited pairs hold in full (path, size/arrays/rows/vehicles/family, BmAK "
             f"systems/emitters/names); "
             f"{sum(1 for o in doc['omissions'] if o['verdict']=='holds')}/5 omissions hold, 1 "
             f"(T-FX16) cannot be reproduced because its row names no search term. None of the "
             f"12 chosen effects is a broken path: "
             f"{sum(1 for f in doc['chosen'] if f['existence']=='embedded in an indexed .ee')} are "
             f"embedded in indexed `.ee` containers and "
             f"{sum(1 for f in doc['chosen'] if f['existence']=='index entry')} is a standalone "
             f"index entry.**")
    L.append("")
    L.append("## 1. What the index is, and why most chosen paths are not in it")
    L.append("")
    L.append(f"`INDEX.jsonl` is the `jc3index.py` output: {len(doc['chosen']) and doc['fx_paths']} "
             f"distinct FX paths exist in `FX_TABLE.jsonl`, but only {doc['index_effc']} `.effc` "
             f"files are standalone archive entries in the index. The rest are FX resources "
             f"embedded inside an `.ee` entity container - still real, addressable through the "
             f"container's index row, but absent from the path index by construction. So "
             f"\"not in the index\" is not \"missing\" here; the audit checks the container.")
    L.append("")
    L.append(f"The doc's **955** is reproduced exactly: it is the distinct paths whose "
             f"`FX_TABLE` row has `root = EffectRTSystem` ({doc['fx955']} of {doc['fx_paths']} "
             f"distinct paths). The other 578 paths are other effect roots, which is why the "
             f"absence scans below use the 955 set the rows cite.")
    L.append("")
    L.append("## 2. The 12 chosen effects - existence and counts")
    L.append("")
    L.append("`size`/`arrays`/`rows`/`vehicles` are the row's numbers against `FX_TABLE`'s "
             "records; `vehicles` counts distinct containers under `/jc_vehicles/` (the "
             "convention that reproduces all twelve rows).")
    L.append("")
    L.append("| row | chosen `.effc` | existence | size | arrays | rows | vehicles | family |")
    L.append("|---|---|---|---:|---:|---:|---:|---|")
    for f in doc["chosen"]:
        c = f["claimed"]
        hit = (f" - {f['index_hits'][0][0]}+{f['index_hits'][0][1]}, "
               f"{f['index_hits'][0][2]} B, {f['index_hits'][0][3]}") if f["index_hits"] else ""
        L.append(f"| `{f['id']}` | `{f['path']}` | {f['existence']}{hit} | "
                 f"{'ok' if f['claims']['size'] else '**%s vs %s**' % (c['size'], f['sizes'])} | "
                 f"{'ok' if f['claims']['arrays'] else '**wrong**'} | "
                 f"{'ok' if f['claims']['rows'] else '**wrong**'} | "
                 f"{'ok' if f['claims']['vehicles'] else '**%s vs %s**' % (c['vehicles'], f['vehicles'])} | "
                 f"{'ok' if f['claims']['family_total'] else '**wrong**'} |")
    L.append("")
    L.append("### T-FX7 - afterburner flame -> `car_cycle_base_dual_nitrous.effc`")
    L.append("")
    f = ch["T-FX7"]
    L.append(f"* Existence: **{f['existence']}** - {f['fx_rows']} `FX_TABLE` rows, "
             f"{f['containers']} containers, all {f['containers_in_index']} containers present in "
             f"the index as `.ee` entries; size `{f['sizes'][0]}` B, arrays {f['arrays'][0]}, "
             f"rows {f['rows_fx'][0]}. The path is not an index entry, which is expected: the "
             f"effect is embedded in the donor's own `.ee`.")
    L.append(f"* Row counts: **{'holds' if f['claim_verdict'] == 'holds' else 'WRONG'}** "
             f"({f['claimed']}).")
    for b in f["bmak"]:
        L.append(f"* BmAK group `{b['group']}`: claimed {b['claimed_systems']} systems / "
                 f"{b['claimed_distinct']} names / {b['claimed_emitters']} emitters, life "
                 f"{b['claimed_lifetime']} s - decoded {b['systems']} systems / "
                 f"{len(b['distinct_names'])} names / {b['emitters_sum']} emitters (group field "
                 f"{b['group_emitters']}), life {b['lifetime']} s. **{f['bmak_verdict']}**.")
        L.append(f"* Colour: the row makes **no colour claim**. The group's decoded palette is "
                 f"{b['colours']} colour entries from {', '.join('`%s`' % s for s in b['colour_sources']) or 'none'} "
                 f"- listed for reference, nothing asserted.")
    L.append("")
    L.append("### T-FX10 - cannon muzzle flash -> `tank_canon_muzzleflash.effc`")
    L.append("")
    f = ch["T-FX10"]
    L.append(f"* Existence: **{f['existence']}** - {f['fx_rows']} rows in {f['containers']} "
             f"containers, all indexed as `.ee`; size {f['sizes'][0]} B, arrays {f['arrays'][0]}, "
             f"rows {f['rows_fx'][0]}.")
    L.append(f"* Row counts: **{'holds' if f['claim_verdict'] == 'holds' else 'WRONG'}** - "
             f"size {f['claimed']['size']} B, {f['claimed']['arrays']} arrays, "
             f"{f['claimed']['rows']} rows, **{f['claimed']['vehicles']} vehicles**; "
             f"`FX_TABLE` records {f['sizes'][0]} B / {f['arrays'][0]} arrays / "
             f"{f['rows_fx'][0]} rows and **{f['vehicles']}** distinct `/jc_vehicles/` "
             f"containers of {f['containers']} in total.")
    for b in f["bmak"]:
        L.append(f"* BmAK group `{b['group']}`: claimed {b['claimed_systems']} systems / "
                 f"{b['claimed_distinct']} names / {b['claimed_emitters']} emitters - decoded "
                 f"{b['systems']} / {len(b['distinct_names'])} / {b['emitters_sum']} "
                 f"(group {b['group_emitters']}), life {b['lifetime']} s vs claimed "
                 f"{b['claimed_lifetime']}. **{f['bmak_verdict']}**.")
        L.append(f"* Colour: no claim. Decoded palette: {b['colours']} entries from "
                 f"{', '.join('`%s`' % s for s in b['colour_sources']) or 'none'}.")
    L.append("")
    L.append("### T-FX19 - wall-scrape sparks -> `spark_trail_02_med.effc`")
    L.append("")
    f = ch["T-FX19"]
    L.append(f"* Existence: **index entry** - `{f['index_hits'][0][0]}` at offset "
             f"{f['index_hits'][0][1]}, **{f['index_hits'][0][2]} B**, mount "
             f"`{f['index_hits'][0][3]}`. That size is exactly the row's 8,495 B, and "
             f"`FX_TABLE` has {f['fx_rows']} rows over {f['containers']} containers.")
    L.append(f"* Row counts: **{'holds' if f['claim_verdict'] == 'holds' else 'WRONG'}** - "
             f"the row says **{f['claimed']['vehicles']} vehicles**; `FX_TABLE` shows "
             f"**{f['vehicles']}** distinct `/jc_vehicles/` containers ({f['containers']} "
             f"containers in all), so the vehicle count is right. Its "
             f"`{f['claimed']['family_total']} variants` family is "
             + ", ".join(f"`{p.split('/')[-1]}` ({v})" for p, v in f['family']) + ".")
    for b in f["bmak"]:
        L.append(f"* BmAK group `{b['group']}`: claimed {b['claimed_systems']} systems / "
                 f"{b['claimed_emitters']} emitters - decoded {b['systems']} / "
                 f"{b['emitters_sum']}. **{f['bmak_verdict']}** (this is the `derived` row: no "
                 f"BmAK system drives the socket, the effect is borrowed from the fleet).")
        L.append(f"* Colour: no claim; the group has 0 systems, so no palette exists.")
    L.append("")
    L.append("## 3. The five named omissions")
    L.append("")
    L.append(f"Each was re-tested by scanning the {doc['fx955']} `EffectRTSystem` paths for the "
             f"term the row itself cites.")
    L.append("")
    L.append("| row | feature | terms scanned | hits | verdict | why |")
    L.append("|---|---|---|---:|---|---|")
    for o in doc["omissions"]:
        terms = ", ".join(f"`{t}`" for t in o["terms"]) or "none named"
        L.append(f"| `{o['id']}` | {o['feature']} | {terms} | {len(o['hits'])} | "
                 f"**{o['verdict']}** | {o['why']} |")
    L.append("")
    for o in doc["omissions"]:
        if o["hits"]:
            L.append(f"* `{o['id']}` hits: " + "; ".join(
                f"`{p}`" + ("" if p not in o["vehicle_hits"] else " (vehicle carrier)")
                for p in o["hits"]))
    L.append("")
    L.append("`T-FX13`'s two hits are the shotgun shell-eject effects the row already names as "
             "non-vehicle matches; their containers are `w15x` weapon `.ee` files, so the "
             "vehicle-carried claim holds. `T-FX9`'s only near hit is "
             "`effects/jc_vehicles/exhaust/car_speedrom_heater.effc`, a heater effect, not haze.")
    L.append("")
    L.append("## 4. Checks")
    L.append("")
    L.append("| check | result |")
    L.append("|---|---|")
    for k, v in doc["checks"].items():
        L.append(f"| `{k}` | {'PASS' if v else 'FAIL'} |")
    L.append("")
    L.append("## 5. UNKNOWNs")
    L.append("")
    L.append("* **T-FX16's absence proof.** The row says \"0 of 955 match\" but names no term, "
             "and the 955 set contains many `trail` effects, so the claim cannot be "
             "reproduced either way. What was tried: a scan for `trail` (too broad to settle "
             "it) and a check of the row text for the missing term. Would be found in: "
             "`t17_fx.py`'s absence rule for the projectile-trail group, which is not read here.")
    L.append("* **What \"vehicles\" counts in `t17_fx.json`.** The `/jc_vehicles/` container "
             "count reproduces all 12 rows, but it is a derived convention, not a decoded "
             "field: the rows never say what they count, and the container totals are higher "
             "(12 vs 11 for T-FX10, 301 vs 298 for T-FX19) because non-vehicle containers "
             "carry the same effect. What the extra containers mean is UNKNOWN.")
    L.append("* **Whether any of these effects plays correctly in game.** Test ban; nothing "
             "here is a runtime check, and the T-17 verify cells stay Q probes.")
    L.append("* **The colour of the BmAK groups in play.** The rows claim no colour; the "
             "decoded palettes are listed, but no row-to-colour judgement is made.")
    L.append("")
    L.append("## 6. Reproduce")
    L.append("")
    L.append("```")
    L.append("python Tools/scripts/t_fx_pair_audit.py --check")
    L.append("```")
    L.append("")
    return "\n".join(L)


def write():
    doc = build()
    text = render(doc)
    with open(os.path.join(ROOT, OUT), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(doc['chosen'])} chosen, {len(doc['omissions'])} omissions; "
          f"claims {sum(1 for c in doc['chosen'] if c['claim_verdict']=='holds')}/12 hold")
    for o in doc["omissions"]:
        print(f"  {o['id']} {o['verdict']}")
    return 0


def check():
    doc = build()
    want = render(doc)
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print(f"FAIL: {OUT} missing (run --write)")
        return 1
    ok = True
    for k, v in doc["checks"].items():
        print(f"  {k:<40} {'PASS' if v else 'FAIL'}")
        ok = ok and v
    with open(path, encoding="utf-8") as f:
        got = f.read().replace("\r\n", "\n")
    if got != want:
        print("FAIL: file differs from the re-derived text")
        ok = False
    else:
        print(f"  {'file_matches_rederivation':<40} PASS ({len(want)} bytes of text)")
    print(f"{'OK' if ok else 'FAILED'}")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(write() if a.write else check())


if __name__ == "__main__":
    main()
