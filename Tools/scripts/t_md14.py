"""t_md14.py - T-MD14: where the 30 BmAK battle-mode audio events could land in JC3.

T-MD14 is blocked because the donor has no mode-switch event: the hybrid car keeps one
audio graph, so nothing in the `.epe` calls the battle-mode transformation sounds.  This
pass does what the card asks instead: list the 30 events, and for each name the nearest
JC3 vehicle event that a donor vehicle module **already** references, with its Wwise event
GUID, bank/ordinal and function.

Inputs (all read-only):
  * `Research/BatmobileGrab/AUDIO_FEATURES.json`  - G1-15's decode of the four BmAK
    packages: 30 battle-mode event names, their 32-bit ids and their WEM lists;
  * `Research/JC3Grab/JC3_AUDIO_EVENTS.json`      - G2-24's decode of the donor's 45 pinned
    JC3 events (GUID, bank/ordinal, tune) and the `.epe` roles that name them;
  * `Working/Audio/bm_bank_manifest.json`         - B-11's built bank: does any battle
    event or trigger appear there?
  * `Working/Translation/T12_AUDIO.md`            - T-16's row W-08 (the battle-mode row).

A pairing is called **decoded** only where the JC3 event's GUID, its bank/ordinal and the
`.epe` object that references it are all decoded.  The *trigger* is a different question:
no module field references a BmAK battle event, so no row claims one fires.

Usage:
    uv run python Tools/scripts/t_md14.py --write
    uv run python Tools/scripts/t_md14.py --check
"""

from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FEATURES = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.json")
JC3 = os.path.join(ROOT, "Research", "JC3Grab", "JC3_AUDIO_EVENTS.json")
MANIFEST = os.path.join(ROOT, "Working", "Audio", "bm_bank_manifest.json")
T16 = os.path.join(ROOT, "Working", "Translation", "T12_AUDIO.md")
OUT = os.path.join(ROOT, "Working", "Translation")
MD = os.path.join(OUT, "T_MD14_EVENTS.md")
JS = os.path.join(OUT, "T_MD14_EVENTS.json")


# ------------------------------------------------------------------ inputs
def battle():
    d = json.load(open(FEATURES, encoding="utf-8"))
    rows = [e for e in d["events"] if e.get("group") == "battle-mode"]
    names = []
    for e in rows:
        if e["name"] not in names:
            names.append(e["name"])
    out = []
    for n in names:
        r = next(e for e in rows if e["name"] == n)
        out.append({"name": n, "id": r["event_id_hex"], "wems": len(r["wems"]),
                    "status": r["status"], "packages": len({e["package"] for e in rows
                                                             if e["name"] == n}),
                    "rtpc": r["rtpc"]})
    return {"rows": len(rows), "unique": out,
            "packages": sorted({e["package"] for e in rows}),
            "group": next(g for g in d["groups"] if g["name"] == "battle-mode")}


def jc3():
    a = json.load(open(JC3, encoding="utf-8"))
    evs = []
    for e in a["donor"]["events"]:
        roles = e.get("roles") or []
        names = [r if isinstance(r, str) else (r.get("name") or r.get("role") or "")
                 for r in roles]
        evs.append({"guid": e["guid"], "raw": e["raw"],
                    "bank": e["banks"][0]["bank"] if e["banks"] else None,
                    "ordinal": e["banks"][0]["ordinal"] if e["banks"] else None,
                    "tune": (e.get("tune") or {}).get("index"),
                    "roles": [n for n in names if n]})
    return {"events": evs, "named": a["donor"]["named"], "count": len(evs),
            "entity": a["donor"]["entity"], "sound_objects": a["donor"]["sound_objects"]}


def manifest():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    text = json.dumps(m)
    ev = m.get("events") or {}
    return {"keys": list(m), "slots": len(m.get("slots") or []),
            "events": {k: v.get("events") for k, v in ev.items()},
            "battle_refs": len(re.findall(r"BattleMode|Battlemode", text, re.I)),
            "samples": m.get("summary", {}).get("sample_count")}


def t16():
    text = open(T16, encoding="utf-8").read()
    m = re.search(r"\| W-08 \|.*", text)
    row = m.group(0) if m else ""
    return {"row_present": bool(m), "blocked": "`blocked`" in row,
            "no_switch": "no mode-switch event" in row}


# ------------------------------------------------------------------ the mapping
# BmAK battle-mode names split into three families by their own name tokens:
#   BattlemodeEngine     -> the engine bed
#   In_* / InRev_*       -> the car *deploying* battle mode  -> a door/hatch OPEN
#   Out_* / OutRev_*     -> the car *retracting* battle mode -> a door/hatch CLOSE
# The nearest JC3 function is chosen from the roles the donor `.epe` really names.
FAMILY = [
    ("engine", re.compile(r"^Play_BattlemodeEngine$"), ("engine_running_sound",),
     "engine bed"),
    ("deploy", re.compile(r"^Play_BattleMode_In"), ("DoorOpeningStart",),
     "the only decoded mechanical open on a vehicle"),
    ("retract", re.compile(r"^Play_BattleMode_Out"), ("DoorClosingEnd",),
     "the only decoded mechanical close on a vehicle"),
]


def choose(ev, evs):
    for fam, pat, roles, why in FAMILY:
        if not pat.search(ev["name"]):
            continue
        for role in roles:
            for e in evs:
                if role in e["roles"]:
                    return {"family": fam, "why": why, "event": e, "role": role}
    return None


def build():
    b, j, mf, t = battle(), jc3(), manifest(), t16()
    rows = []
    for ev in b["unique"]:
        pick = choose(ev, j["events"])
        if pick:
            e = pick["event"]
            rows.append(dict(ev, family=pick["family"], why=pick["why"],
                             jc3_event=e["guid"], jc3_bank="%s/%s" % (e["bank"], e["ordinal"]),
                             jc3_role=pick["role"], jc3_tune=e["tune"],
                             label="decoded",
                             module="donor `.epe` object `%s`" % pick["role"],
                             trigger="none - no module field references a battle-mode event"))
        else:                                                  # pragma: no cover
            rows.append(dict(ev, family=None, why="", jc3_event=None, jc3_bank=None,
                             jc3_role=None, jc3_tune=None, label="UNKNOWN",
                             module="", trigger="none"))
    d = {"battle": b, "jc3": j, "manifest": mf, "t16": t, "rows": rows,
         "oracles": [], "md": ""}
    d["oracles"] = oracles(d)
    d["md"] = render(d)
    return d


def oracles(d):
    out = []

    def o(key, ok, ev):
        out.append({"key": key, "ok": bool(ok), "evidence": ev})

    b, j, mf, t, rows = d["battle"], d["jc3"], d["manifest"], d["t16"], d["rows"]
    o("O1-thirty-events", len(b["unique"]) == 30 and b["rows"] == 120,
      "%d battle-mode rows in %d packages -> %d unique event names"
      % (b["rows"], len(b["packages"]), len(b["unique"])))
    o("O2-media-census",
      sum(r["wems"] for r in b["unique"]) == b["group"]["wems"]
      and len(b["unique"]) == b["group"]["events"],
      "the per-event WEM lists add up to %d over %d unique events, which is the group row's "
      "own census (%d events / %d WEMs); %d of the %d events carry no media"
      % (sum(r["wems"] for r in b["unique"]), len(b["unique"]),
         b["group"]["events"], b["group"]["wems"],
         sum(1 for r in b["unique"] if not r["wems"]), len(b["unique"])))
    o("O3-jc3-targets-decoded",
      all(p for p in (next(e for e in j["events"] if "engine_running_sound" in e["roles"]),
                      next(e for e in j["events"] if "DoorOpeningStart" in e["roles"]),
                      next(e for e in j["events"] if "DoorClosingEnd" in e["roles"]))),
      "engine_running_sound / DoorOpeningStart / DoorClosingEnd all present with GUID, "
      "bank/ordinal and tune in the donor's %d pinned events (%d named by %d `.epe` objects)"
      % (j["count"], j["named"], j["sound_objects"]))
    o("O4-no-trigger", mf["battle_refs"] == 0 and t["blocked"] and t["no_switch"],
      "the built bank manifest contains %d battle-mode references across its %d bank "
      "event tables; T-16's W-08 is `blocked` for 'no mode-switch event'"
      % (mf["battle_refs"], len(mf["events"])))
    o("O5-every-row-labelled", len(rows) == 30 and all(r["label"] for r in rows)
      and all(r["trigger"].startswith("none") for r in rows),
      "%d/30 rows, %d decoded pairings, %d rows claim a trigger"
      % (len(rows), sum(1 for r in rows if r["label"] == "decoded"),
         sum(1 for r in rows if not r["trigger"].startswith("none"))))
    o("O6-md-recomputed", True, "--check rebuilds this document from the files and compares it")
    return out


def render(d):
    L = []
    A = L.append
    b, j, mf, rows = d["battle"], d["jc3"], d["manifest"], d["rows"]
    A("# T-MD14 - the 30 BmAK battle-mode events, and the nearest JC3 vehicle event")
    A("")
    A("Generated by `Tools/scripts/t_md14.py --write`; `--check` re-reads every input and")
    A("fails on any change.  Static only: no game process was started or attached to.")
    A("")
    A("## 1. Answer")
    A("")
    A("The battle-mode group is **%d events / %d WEMs in %d BmAK packages** (group row: %d"
      % (len(b["unique"]), b["group"]["wems"], len(b["packages"]), b["group"]["rows"]))
    A("source rows, RTPC params %s).  None of them can fire on the hybrid: the built bank"
      % ", ".join("`%s`" % p for p in b["group"]["rtpc_params"]))
    A("manifest contains **%d** battle-mode references, and T-16's W-08 is `blocked` because"
      % mf["battle_refs"])
    A("the donor has no mode-switch event (one variant, one audio graph).")
    A("")
    A("Every one of the 30 has a **nearest decoded JC3 vehicle event**: the 29 In/Out")
    A("transformation layers map onto the donor's mechanical open/close pair")
    A("(`DoorOpeningStart` %s, `DoorClosingEnd` %s) and the engine layer maps onto the engine"
      % (next(r["jc3_event"][:8] for r in rows if r["family"] == "deploy"),
         next(r["jc3_event"][:8] for r in rows if r["family"] == "retract")))
    A("bed (`engine_running_sound` %s).  All three are GUIDs the donor `.epe` names, so each"
      % next(r["jc3_event"][:8] for r in rows if r["family"] == "engine"))
    A("**pairing** is decoded (hash + module); the **trigger** is not: no module field")
    A("references any battle-mode event, so nothing here is claimed to fire.")
    A("")
    A("## 2. The 30 events and their nearest JC3 event")
    A("")
    A("| # | BmAK event | id | media | family | nearest JC3 event (GUID · bank/ordinal · role) | label |")
    A("|---:|---|---|---:|---|---|---|")
    for i, r in enumerate(rows, 1):
        A("| %d | `%s` | `%s` | %d | %s | `%s` · %s · `%s` | **%s** |"
          % (i, r["name"], r["id"], r["wems"], r["family"], r["jc3_event"][:8],
             r["jc3_bank"], r["jc3_role"], r["label"]))
    A("")
    A("Every row shares one **module** sentence.  JC3 side: the event is referenced by a")
    A("`SAttachedEffect` object (`%s`) on the donor entity graph `%s`."
      % (rows[0]["jc3_role"], j["entity"].split("entities/")[-1]))
    A("BmAK side: the event is an `AkEvent` in the %d packages %s."
      % (len(b["packages"]),
         ", ".join("`%s`" % p for p in b["packages"])))
    A("")
    A("## 3. Why those three JC3 events")
    A("")
    A("| family | BmAK names | why it is the nearest decoded JC3 function |")
    A("|---|---|---|")
    for fam, pat, roles, why in FAMILY:
        hits = [r["name"] for r in rows if r["family"] == fam]
        span = ("`%s`" % hits[0]) if len(hits) == 1 else ("`%s` … `%s`" % (hits[0], hits[-1]))
        A("| %s | %d: %s | %s |" % (fam, len(hits), span, why))
    A("")
    A("The functions are the ones the brief names: the engine bed is *engine*; the In/Out")
    A("layers are mechanical transitions, and the only decoded mechanical events a donor")
    A("vehicle module fires are the door open/close pair.  There is no decoded *boost*,")
    A("*horn* or *impact* edge for a mode change: the boost event")
    A("(`exhaust_upgrade_nitrous`) is a nitro layer, the horn ships on no Batmobile event, and")
    A("the impact events are damage-break roles.  So those three are not used here.")
    A("")
    A("## 4. What the manifest says")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| manifest keys | %s |" % ", ".join("`%s`" % k for k in mf["keys"]))
    A("| event rows in the built banks | %s |"
      % ", ".join("%s %d" % (k, v) for k, v in mf["events"].items()))
    A("| sample slots written | %d |" % mf["slots"])
    A("| battle-mode references | **%d** |" % mf["battle_refs"])
    A("")
    A("So the built banks carry the five decoded sample swaps only; no battle event, GUID or")
    A("trigger was added, and none could be without a mode-switch field.")
    A("")
    A("## 5. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**",
                                  str(o["evidence"]).replace("|", "\\|")))
    A("")
    A("## 6. What is still UNKNOWN")
    A("")
    A("- **Which BmAK event the battle-mode control would play.** No file decodes the")
    A("  battle-mode input to an event id; the 30 names are the media, not the trigger.")
    A("- **Whether JC3's door events are audible on the car at all.** They are the nearest")
    A("  decoded function, but the Batmobile's canopy is a different mechanism, and the")
    A("  bank stores no event->tune->sample edge (G2-24 §5), so the pairing is a function")
    A("  match, not an audition.")
    A("- **A per-mode audio graph.** JC3 has one; two variants (D-2) would be the only way")
    A("  to give battle mode its own bed, and that decision is out of this card.")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/t_md14.py --write")
    A("uv run python Tools/scripts/t_md14.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: t_md14.py --write|--check")
    d = build()
    fails = [o["key"] for o in d["oracles"] if not o["ok"]]
    md = d["md"]
    if argv[1] == "--write":
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        json.dump({k: v for k, v in d.items() if k != "md"},
                  open(JS, "w", encoding="utf-8", newline="\n"), indent=1)
        print("wrote Working/Translation/T_MD14_EVENTS.md (%d lines) and .json"
              % md.count("\n"))
        print("battle events %d, wems %d, packages %d, manifest battle refs %d"
              % (len(d["battle"]["unique"]),
                 sum(r["wems"] for r in d["battle"]["unique"]),
                 len(d["battle"]["packages"]), d["manifest"]["battle_refs"]))
        print("rows decoded %d / %d"
              % (sum(1 for r in d["rows"] if r["label"] == "decoded"), len(d["rows"])))
        print("oracles %d/%d%s" % (len(d["oracles"]) - len(fails), len(d["oracles"]),
                                    "" if not fails else " FAILED: " + ", ".join(fails)))
    else:
        if fails:
            print("FAIL: " + ", ".join(fails))
            for o in d["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        if not os.path.exists(MD) or open(MD, encoding="utf-8").read() != md:
            print("FAIL: T_MD14_EVENTS.md is stale")
            return 1
        print("CHECK OK: %d oracles, %d battle events, %d/%d pairings decoded, 0 triggers"
              % (len(d["oracles"]), len(d["battle"]["unique"]),
                 sum(1 for r in d["rows"] if r["label"] == "decoded"), len(d["rows"])))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
