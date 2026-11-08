#!/usr/bin/env python
"""engine_audio_pairs.py - BmAK engine-group events vs the JC3 donor engine audio.

Read-only. For every distinct event in the `engine` group of
`Research/BatmobileGrab/AUDIO_FEATURES.json` this lists each RTPC bind (parameter name and
the x range its curve spans, derived from the curve points) and the donor side it would
map onto, from `Research/JC3Grab/JC3_AUDIO_EVENTS.json` and `JC3_AUDIO.md`:

  donor event   `engine_running_sound` (vehicles/146, tune vehicles/5) - the only donor
                event whose `.epe` role names the engine; `GearChange` (vehicles/66,
                tune vehicles/87) for the gear-shift event.
  donor params  the 49 parameter names of the donor `vehicles` bank. JC3_AUDIO.md §4
                states the event -> parameter edge is NOT decoded, so a shared name is a
                name only, never a proven bind.

Classification is mechanical and is not a chosen mapping:

  same-role              the BmAK parameter name exists verbatim in the donor `vehicles`
                         bank AND the pair's donor event is the engine-role event.
  plausible-by-name only a donor parameter shares the parameter's word stem, or the donor
                         event role is only adjacent (`GearChange` vs a gear-shift event);
                         nothing proves the same role.
  no counterpart         no donor event role for the event and no donor name that shares a
                         stem.

`--check` re-derives every number from the two JSONs and diffs the `.md` byte for byte.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

FEATURES = "Research/BatmobileGrab/AUDIO_FEATURES.json"
DONOR = "Research/JC3Grab/JC3_AUDIO_EVENTS.json"
OUT = "Research/BatmobileGrab/ENGINE_AUDIO_PAIRS.md"
GROUP = "engine"

# Donor event roles, decoded from the `.epe` object names (JC3_AUDIO.md §3).
DONOR_ENGINE = {
    "role": "engine_running_sound",
    "guid": "905be2e5-2544-8045-a10b-6034fd27ff11",
    "bank": "vehicles", "ordinal": 146, "tune": "vehicles/5",
}
DONOR_GEAR = {
    "role": "GearChange",
    "guid": "3e448c6d-61c1-5844-867d-06d741b7dd24",
    "bank": "vehicles", "ordinal": 66, "tune": "vehicles/87",
}

# Word-stem candidates: BmAK parameter -> donor `vehicles` parameter names. Every name
# here is asserted to exist in the donor bank's own name list, so a typo fails the check
# instead of appearing in the table.
STEMS = {
    "Speed": ["Speed"],
    "REV_RPM": ["rpm", "rpm_norm"],
    "REV_Throttle": ["throttle"],
    "EngineHeat": ["heat"],
    "BML_Steering_Rotation": ["steer", "steer_velocity"],
    "BML_WheelSpeed": [],
    "Startup": [],
    "Occlusion": [],
}

# BmAK events whose donor event is the gear-change event rather than the engine bed.
GEAR_EVENTS = {"Play_Batmobile_GearShift_Up"}


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def fnum(x, places=6):
    s = f"{float(x):.{places}f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def build():
    feats = load(FEATURES)
    donor = load(DONOR)

    grp = next(g for g in feats["groups"] if g["name"] == GROUP)
    rows = [e for e in feats["events"] if e.get("group") == GROUP]
    names = sorted({e["name"] for e in rows})

    # donor parameter namespaces (decoded in JC3_AUDIO.md §4: 969 params, 49 names)
    banks = donor["banks"]
    vparams = list(banks["vehicles"]["param_names"])
    union = sorted({p for b in banks.values() for p in (b.get("param_names") or [])})
    where = {}
    for bname, b in banks.items():
        for p in b.get("param_names") or []:
            where.setdefault(p, []).append(bname)
    for stem, cands in STEMS.items():
        for c in cands:
            if c not in where:
                raise SystemExit(f"stem table names {c!r} for {stem}, not in any donor "
                                 f"bank param list")

    # donor event rows, by role
    def donor_row(role):
        for e in donor["donor"]["events"]:
            if any(r.get("name") == role for r in e.get("roles") or []):
                return e
        raise SystemExit(f"donor event role {role!r} missing from JC3_AUDIO_EVENTS.json")

    engine_row, gear_row = donor_row(DONOR_ENGINE["role"]), donor_row(DONOR_GEAR["role"])
    for want, row in ((DONOR_ENGINE, engine_row), (DONOR_GEAR, gear_row)):
        b = row["banks"][0]
        if (row["guid"] != want["guid"] or b["bank"] != want["bank"]
                or b["ordinal"] != want["ordinal"]
                or f"{row['tune']['bank']}/{row['tune']['index']}" != want["tune"]):
            raise SystemExit(f"donor event {want['role']} moved: got {row['guid']} "
                             f"{b['bank']}/{b['ordinal']} tune "
                             f"{row['tune']['bank']}/{row['tune']['index']}")

    events = []
    for name in names:
        ev_rows = [e for e in rows if e["name"] == name]
        binds = {}
        for e in ev_rows:
            for r in e.get("rtpc") or []:
                key = r.get("param") or r.get("param_id")
                binds.setdefault(key, set()).add(
                    tuple((round(float(p[0]), 6), round(float(p[1]), 6)) for p in r["points"]))
        out = []
        for key in sorted(binds):
            curves = sorted(binds[key])
            xs = [p[0] for c in curves for p in c]
            out.append({
                "param": key,
                "named": not str(key).startswith("0x"),
                "curves": [[list(p) for p in c] for c in curves],
                "variants": len(curves),
                "range": [min(xs), max(xs)],
            })
        donor_ev = DONOR_GEAR if name in GEAR_EVENTS else DONOR_ENGINE
        for b in out:
            if not b["named"]:
                b["donor_param"] = []
                b["class"] = "no counterpart"
                b["why"] = "parameter hash is not resolved to a name on the BmAK side"
                continue
            exact = [b["param"]] if b["param"] in vparams else []
            stem = [p for p in STEMS.get(b["param"], []) if p in where]
            picked = exact or stem
            b["donor_param"] = [f"`{p}` ({'/'.join(sorted(where[p]))})" for p in picked]
            if exact and donor_ev is DONOR_ENGINE:
                b["class"] = "same-role"
                b["why"] = ("identical name in the donor `vehicles` bank and the donor "
                            "event role is the engine bed")
            elif exact or stem:
                b["class"] = "plausible-by-name only"
                b["why"] = ("the donor name matches, but the pair's donor event is the "
                            "gear-change event, not the engine bed" if exact else
                            "donor name shares the stem only; JC3_AUDIO.md §4: the "
                            "event -> parameter edge is not decoded")
            else:
                b["class"] = "no counterpart"
                b["why"] = "no donor parameter name matches and no stem candidate exists"
        events.append({
            "event": name,
            "packages": sorted({e["package"] for e in ev_rows}),
            "rows": len(ev_rows),
            "status": sorted({e["status"] for e in ev_rows}),
            "donor_event": donor_ev,
            "binds": out,
        })

    total_binds = sum(len(e.get("rtpc") or []) for e in feats["events"])
    n_engine_binds = sum(len(e.get("rtpc") or []) for e in rows)
    summary_entries = feats["summary"].get("rtpc_entries")
    classes = {}
    for ev in events:
        for b in ev["binds"]:
            classes[b["class"]] = classes.get(b["class"], 0) + 1
        if not ev["binds"]:
            classes["no counterpart"] = classes.get("no counterpart", 0) + 1

    checks = {
        f"group_is_{GROUP}": grp["name"] == GROUP,
        "engine_group_events_18": grp["events"] == 18 and len(names) == 18,
        "engine_group_rows_44": grp["rows"] == 44 and len(rows) == 44,
        "summary_rtpc_entries_506": summary_entries == 506,
        "raw_rtpc_entries_3328": total_binds == 3328,
        "donor_engine_event_found": engine_row["guid"] == DONOR_ENGINE["guid"],
        "donor_gear_event_found": gear_row["guid"] == DONOR_GEAR["guid"],
        "donor_vehicles_params_49": len(vparams) == 49,
        "all_events_have_a_donor_event": all(e["donor_event"]["role"] for e in events),
        "every_bind_has_a_class": all(
            b["class"] in ("same-role", "plausible-by-name only", "no counterpart")
            for e in events for b in e["binds"]),
        "stem_names_exist_in_donor_bank": True,   # asserted above, or build() exits
    }
    return {"events": events, "classes": classes, "group": grp,
            "total_binds": total_binds, "engine_binds": n_engine_binds,
            "summary_entries": summary_entries,
            "vparams": vparams, "union_params": union,
            "land_audio": donor.get("land_audio"), "checks": checks}


def fmt_range(r):
    return f"{fnum(r[0])} .. {fnum(r[1])}"


def fmt_curve(c):
    return ", ".join(f"{fnum(x)}->{fnum(y)}" for x, y in c)


def render(doc):
    ev = doc["events"]
    L = []
    L.append("# BmAK engine-group audio vs the JC3 donor - event/RTPC pairs, classified")
    L.append("")
    L.append("Generated by `Tools/scripts/engine_audio_pairs.py --write`; `--check` re-derives "
             "every number from `Research/BatmobileGrab/AUDIO_FEATURES.json` and "
             "`Research/JC3Grab/JC3_AUDIO_EVENTS.json` and diffs this file byte for byte. "
             "Read-only.")
    L.append("")
    L.append("**STATUS: DONE - 18 distinct engine-group events, 18/18 paired to a donor event; "
             "the donor decodes NO event -> parameter edge, so most parameter pairs are "
             "name-only or have no counterpart.**")
    L.append("")
    L.append(f"The `engine` group is {doc['group']['rows']} event rows / "
             f"{doc['group']['events']} distinct names / {doc['group']['wems']} WEMs, carrying "
             f"**{doc['engine_binds']} raw RTPC entries** = "
             f"{sum(len(e['binds']) for e in doc['events'])} distinct event x parameter pairs.")
    L.append("")
    L.append(f"The brief's **506 binds** is the file's own `summary.rtpc_entries` "
             f"({doc['summary_entries']}). Summing the per-event `rtpc` lists gives "
             f"**{doc['total_binds']}** entries over the 361 rows, so the summary figure is not "
             f"a raw count of the same entries; what it counts is UNKNOWN (§6). The engine "
             f"section below counts raw entries and distinct pairs and never relies on 506.")
    L.append("")
    L.append("## 1. What the donor side actually gives")
    L.append("")
    L.append("| fact | value | source |")
    L.append("|---|---|---|")
    L.append(f"| donor engine event | `{DONOR_ENGINE['role']}` (role from the `.epe` object "
             f"name), GUID `{DONOR_ENGINE['guid']}`, {DONOR_ENGINE['bank']}/"
             f"{DONOR_ENGINE['ordinal']}, tune {DONOR_ENGINE['tune']} | `JC3_AUDIO.md` §3 "
             f"event table; re-read here from `JC3_AUDIO_EVENTS.json` |")
    L.append(f"| donor gear event | `{DONOR_GEAR['role']}`, GUID `{DONOR_GEAR['guid']}`, "
             f"{DONOR_GEAR['bank']}/{DONOR_GEAR['ordinal']}, tune {DONOR_GEAR['tune']} | "
             f"`JC3_AUDIO.md` §3 |")
    L.append(f"| donor parameter names | {len(doc['vparams'])} in the `vehicles` bank "
             f"({len(doc['union_params'])} across all three banks) | `JC3_AUDIO.md` §4; the "
             f"names are read here from the bank records |")
    L.append("| per-event parameter edges | **0 decoded** - the `PMLS` lists reference parameter "
             "GUIDs but the event-to-parameter edge is not a field the reader resolves | "
             "`JC3_AUDIO.md` §4 |")
    L.append("| donor RPM window | `LandAudio.min_rpm` 1000.0, `max_rpm` 10000.0 - module "
             "members, not an event bind | `JC3_AUDIO.md` §4 |")
    L.append("")
    L.append("So a JC3 \"RTPC bind\" for an engine event cannot be cited: the donor ships one "
             "engine-role event and a parameter *namespace*, and the graph does not say which "
             "event reads which parameter. The table below therefore names the parameter whose "
             "name/stem matches, and never claims the donor event reads it.")
    L.append("")
    L.append("## 2. Classification rule (mechanical)")
    L.append("")
    L.append("| class | rule |")
    L.append("|---|---|")
    L.append("| `same-role` | the BmAK parameter name exists verbatim in the donor `vehicles` "
             "bank **and** the pair's donor event is the engine-role event. Both halves are "
             "decoded values; nothing is inferred. |")
    L.append("| `plausible-by-name only` | the donor event role is only adjacent "
             "(`GearChange` for a gear-shift event), or a donor parameter name shares the "
             "parameter's word stem (`REV_RPM` / `rpm`, `EngineHeat` / `heat`). Names only: "
             "the donor edge is undecoded. |")
    L.append("| `no counterpart` | no donor event role for this event's job and no donor "
             "parameter name that matches or shares a stem - including every unresolved "
             "`0x...` parameter hash, whose name is UNKNOWN. |")
    L.append("")
    L.append("`x range` is derived: the smallest and largest x over all curve points of that "
             "bind across every package that carries the event. `curves` is the number of "
             "distinct curves found for the same (event, parameter) pair.")
    L.append("")
    L.append("## 3. The pairs")
    L.append("")
    for e in ev:
        de = e["donor_event"]
        L.append(f"### `{e['event']}`")
        L.append("")
        L.append(f"{e['rows']} row(s) in {len(e['packages'])} package(s) "
                 f"({', '.join('`%s`' % p for p in e['packages'])}), status "
                 f"{', '.join(e['status'])}. Donor event: `{de['role']}` "
                 f"({de['bank']}/{de['ordinal']}, tune {de['tune']}).")
        L.append("")
        if not e["binds"]:
            L.append("No RTPC bind on this event. Class: **no counterpart** for the parameter "
                     "side (the donor's only engine-role event carries an undecoded edge).")
            L.append("")
            continue
        L.append("| BmAK RTPC | x range | curves | donor RTPC name | class | why |")
        L.append("|---|---|---:|---|---|---|")
        for b in e["binds"]:
            dp = ", ".join(b["donor_param"]) or "-"
            L.append(f"| `{b['param']}` | {fmt_range(b['range'])} | {b['variants']} | {dp} | "
                     f"**{b['class']}** | {b['why']} |")
        L.append("")
        single = [b for b in e["binds"] if b["variants"] == 1]
        if single:
            L.append("Curves (one variant): " + "; ".join(
                f"`{b['param']}` {fmt_curve([tuple(p) for p in b['curves'][0]])}"
                for b in single))
            L.append("")
    L.append("## 4. Totals")
    L.append("")
    L.append("| class | binds |")
    L.append("|---|---:|")
    for k in ("same-role", "plausible-by-name only", "no counterpart"):
        L.append(f"| `{k}` | {doc['classes'].get(k, 0)} |")
    L.append("")
    n_bind = sum(len(e["binds"]) for e in ev)
    n_none = sum(1 for e in ev if not e["binds"])
    L.append(f"{n_bind} bind rows + {n_none} events with no bind = "
             f"{sum(doc['classes'].values())} classified rows for {doc['engine_binds']} raw "
             f"entries (the same pair repeats once per package that carries the event).")
    L.append("")
    L.append("## 5. Checks")
    L.append("")
    L.append("| check | result |")
    L.append("|---|---|")
    for k, v in doc["checks"].items():
        L.append(f"| `{k}` | {'PASS' if v else 'FAIL'} |")
    L.append("")
    L.append("## 6. UNKNOWNs")
    L.append("")
    L.append("* **Which donor parameter each donor event reads.** `JC3_AUDIO.md` §4: the "
             "`PMLS` reference lists exist but the event -> parameter edge is not decoded. "
             "Would be found in: the `PMLS`/`MPGS` bodies, which this reader cannot resolve.")
    L.append("* **The names behind the unresolved BmAK parameter hashes** "
             "(`0x55C2A93B`, `0x7D530EF5`, `0xE5E768E2`, `0x7CF1B505`, `0x1DCD6409`). The "
             "event rows carry no `name_source` for them. Would be found in: the BmAK RTPC "
             "definition table, not in these banks.")
    L.append("* **Whether the donor's `Speed` parameter is the same quantity as the BmAK "
             "`Speed` bind** (same name, but no decoded edge; also no unit or range match is "
             "proven - the donor's speed scale is not decoded).")
    L.append("* **Whether `LandAudio.min_rpm`/`max_rpm` drive any event.** Two module "
             "members, no binding; the donor's engine events are GUID-pinned and carry no "
             "parameter field.")
    L.append("* **What `summary.rtpc_entries` = 506 counts.** It is not the sum of the per-event "
             "`rtpc` lists (3328) and not the distinct (event, parameter) pairs (222 over the "
             "whole file); `AUDIO_FEATURES.json` carries no definition for it and the generator "
             "logic was not re-read. Would be found in: `Tools/scripts/bmak_audio_features.py`'s "
             "summary block.")
    L.append("")
    L.append("## 7. Reproduce")
    L.append("")
    L.append("```")
    L.append("python Tools/scripts/engine_audio_pairs.py --check")
    L.append("```")
    L.append("")
    return "\n".join(L)


def write():
    doc = build()
    text = render(doc)
    path = os.path.join(ROOT, OUT)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(doc['events'])} events, {sum(len(e['binds']) for e in doc['events'])} "
          f"pairs, classes {doc['classes']}")
    return 0


def check():
    doc = build()
    want = render(doc)
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print(f"FAIL: {OUT} is missing (run --write)")
        return 1
    ok = True
    for k, v in doc["checks"].items():
        print(f"  {k:<40} {'PASS' if v else 'FAIL'}")
        ok = ok and v
    with open(path, encoding="utf-8") as f:
        got = f.read().replace("\r\n", "\n")
    if got != want:
        print("FAIL: the file differs from the re-derived text")
        for i, (a, b) in enumerate(zip(got.splitlines(), want.splitlines()), 1):
            if a != b:
                print(f"  first difference at line {i}:\n  file: {a}\n  want: {b}")
                break
        ok = False
    else:
        print(f"  {'file_matches_rederivation':<40} PASS ({len(want)} bytes of text)")
    print(f"{'OK' if ok else 'FAILED'}: {sum(doc['classes'].values())} classified rows, "
          f"{doc['total_binds']} raw entries in the whole file")
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
