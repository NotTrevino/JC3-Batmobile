#!/usr/bin/env python
"""jc3seat.py - G2-19: where the driver attach transform and the seated pose are chosen.

Three questions, three data sources, no guesses:

1. **Where Rico is placed.** The donor `.epe` carries `CInteractionGraphEntry` / `…Exit` /
   `…PointNode` objects named `entry.driver…` / `exit.driver…`; the G2-18 decode
   (`Research/JC3Grab/INTERACTION.json`) has their transforms, states and parents.  The
   `.epe` is the *only* place a vehicle says anything about the driver - the entity carries
   no seat, occupant or pose module (31 `.vmodc`, 52 module types, none of them).
2. **Where his pose is chosen.** In the character, not the car:
   `animations/jc_statemachine/main_characters/rico/rico_base.afsmb` is the state machine
   (states, `MOD_*` class selectors, driver-seat conditions, the `PPikt.driving.*` IK
   targets) and `rico_base.asb` is its animation set, whose string table carries the clip
   paths - grouped by **vehicle class** (`car/low`, `car/med`, `car/circuit`, `tank`,
   `bike/slow`, `boat`, `helicopter`, `plane`).  The clips are not separate archive
   entries: they live inside the `.asb`.
3. **How high each class sits.** The seat is a *part* (`sportsmuscle_f_l_seat`,
   `racingsupercar_seats`, `racinghothatch_seats`, `mediumtank_hatch`), and its convex hull
   in the `.physicsc` gives the box.  The donor's seat-box centre sits 10 mm from the
   Batmobile's `Driver` socket hip, which is what makes the box centre a usable seat height
   and lets the candidate pose be *chosen* instead of picked by name.

Writes `Research/JC3Grab/SEAT.md` + `SEAT.json`.  `--check` re-derives and compares both.

Usage:
  python jc3seat.py --write
  python jc3seat.py --check
  python jc3seat.py dump clips|states|seats|points
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3grab  # noqa: E402
import jc3hkx  # noqa: E402
import jc3index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
MD_NAME, JSON_NAME = "SEAT.md", "SEAT.json"

SM_FILES = (
    "animations/jc_statemachine/main_characters/rico/rico_base.afsmb",
    "animations/jc_statemachine/main_characters/rico/rico_base.asb",
)
VEHICLE_DIRS = ("v0300_car_kensington_sportsmuscle", "v0401_car_mugello_racingsupercar",
                "v0003_car_autostraad_racinghothatch", "v0201_car_capstone_mediumtank")
SEAT_KEYS = ("seat", "seats", "hatch")   # matched as whole `_`-separated tokens, see `is_seat_part`
CLIP_ROOT = "animations/jc_characters"


def read(path: str, rows: list[dict]) -> bytes:
    hit = [r for r in rows if r["path"] == path]
    if not hit:
        raise LookupError(f"not in index: {path}")
    return jc3grab.read_entry(hit[0], GAME)


def strings(blob: bytes, n: int = 8) -> list[str]:
    return [s.decode("latin-1") for s in re.findall(rb"[\x20-\x7e]{%d,}" % n, blob)]


def clip_families(ss: list[str]) -> dict:
    """`…/rico/vehicle/<family>/…ban` strings, grouped by the path under `vehicle/`."""
    fam: dict[str, list[str]] = {}
    for s in ss:
        i = s.find(CLIP_ROOT)
        if i < 0:
            continue
        path = s[i:]
        if "/rico/vehicle/" not in path or not path.endswith(".ban"):
            continue
        tail = path.split("/rico/vehicle/", 1)[1]
        parts = tail.split("/")
        if len(parts) < 2:
            continue
        key = "/".join(parts[:-1]) if len(parts) > 2 else parts[0]
        fam.setdefault(key, []).append(path)
    return {k: sorted(set(v)) for k, v in sorted(fam.items())}


def selectors(ss: list[str]) -> dict:
    """The state machine's class selectors, seat conditions and IK targets."""
    mods = collections.Counter()
    for s in ss:
        m = re.search(r"VEHICLE_MOD_([A-Z0-9_]+)$", s)
        if m:
            mods[m.group(1)] += 1
        m = re.search(r"MOD_([A-Z0-9_]+)$", s)
        if m and "VEHICLE" in s and not s.startswith("ANIM_MODIFIER"):
            mods.setdefault(m.group(1), 0)
    seats = sorted({s for s in ss if "DRIVER_SEAT" in s or "SEAT_OCCUPIED" in s})
    ik = sorted({s for s in ss if s.startswith("PPikt.driving")})
    enter = sorted({s for s in ss if re.match(r"^P?ACT_ENTER_VEHICLE", s)})
    exits = sorted({s for s in ss if re.match(r"^P?ACT_.*EXIT_VEHICLE", s)})
    states = sorted({s for s in ss if s.startswith("S_") and "VEHICLE" in s})
    return {"mods": dict(sorted(mods.items())), "seats": seats, "ik": ik,
            "enter": enter, "exit": exits, "states": states}


def points_of() -> dict:
    """The donor `.epe` objects that name the driver (G2-18's decode)."""
    doc = json.load(open(os.path.join(OUT, "INTERACTION.json"), encoding="utf-8"))
    rows = []
    for p in doc["points"]:
        name = p.get("name") or ""
        if "driver" not in name.lower():
            continue
        rows.append({"name": name, "class": p.get("class"), "depth": p.get("depth"),
                     "parent": p.get("parent"), "state": p.get("state"),
                     "enabled": p.get("enabled"),
                     "serpente_m": p.get("serpente"), "batmobile_m": p.get("batmobile"),
                     "world_source": p.get("world_source"),
                     "verdict": p.get("verdict")})
    by = collections.Counter(r["name"].split(".")[0] for r in rows)
    return {"count": len(rows), "rows": rows, "by_prefix": dict(sorted(by.items()))}


def is_seat_part(name: str) -> bool:
    """True when the part is a seat, judged on whole name tokens.

    `hatch` has to be a token, not a substring: the vehicle stem
    `racinghot`+`hatch` lives inside every part name of that car, so a substring
    test labels the whole car a seat (52 false rows on the first run).
    """
    return bool(set(re.split(r"[_./ ]+", str(name).lower())) & set(SEAT_KEYS))


def parts_of(rows: list[dict]) -> dict:
    """The seat-ish part of each roster vehicle, from `PARTS_TABLE.jsonl`."""
    want = {v: None for v in VEHICLE_DIRS}
    for line in open(os.path.join(OUT, "PARTS_TABLE.jsonl"), encoding="utf-8"):
        rec = json.loads(line)
        ent = rec["entity"]
        for v in VEHICLE_DIRS:
            if v in ent and ent.endswith(".ee") and want[v] is None:
                hits = [p for p in rec["parts"] if is_seat_part(p.get("n", ""))]
                if hits:
                    want[v] = {"entity": ent,
                               "parts": [{"index": p["i"], "name": p["n"],
                                          "class": p.get("dt"),
                                          "behaviour": p.get("b")} for p in hits]}
    return {k: v for k, v in want.items() if v}


def seat_boxes(rows: list[dict], parts: dict) -> dict:
    """Each seat part's convex hull, in vehicle space, from the entity's `.physicsc`."""
    out = {}
    for v, rec in parts.items():
        item = {"entity": rec["entity"], "parts": [], "hulls": 0}
        try:
            files = jc3hkx.physicsc_of(rec["entity"], rows, GAME)
        except Exception as e:                       # noqa: BLE001
            item["error"] = f"extract: {e}"
            out[v] = item
            continue
        if not files:
            item["error"] = "no .physicsc in the bundle"
            out[v] = item
            continue
        pf = jc3hkx.Packfile(files[0][1])
        item["file"] = files[0][0]
        idx = {p["index"]: p["name"] for p in rec["parts"]}
        cls = {p["index"]: p.get("class") for p in rec["parts"]}
        found = {}
        for o in pf.objects:
            if o.cls not in jc3hkx.COMPOUND_CLASSES:
                continue
            d = jc3hkx.decode_compound(pf, o.offset, o.cls)
            for inst in d["instances"]:
                pi = inst["part_index"]
                if pi not in idx or not inst["aabb"]:
                    continue
                box = jc3hkx.transform_aabb(inst["aabb"], inst["basis"], inst["translation"])
                item["hulls"] += 1
                prev = found.get(pi)
                if prev:
                    prev["min"] = [min(prev["min"][k], box["min"][k]) for k in range(3)]
                    prev["max"] = [max(prev["max"][k], box["max"][k]) for k in range(3)]
                    prev["shapes"] += 1
                else:
                    found[pi] = {"index": pi, "name": idx[pi], "class": cls.get(pi),
                                 "shape_class": inst["shape_class"], "shapes": 1,
                                 "min": box["min"], "max": box["max"]}
        for pi, box in sorted(found.items()):
            box["size_m"] = [round(box["max"][k] - box["min"][k], 4) for k in range(3)]
            box["centre_m"] = [round((box["max"][k] + box["min"][k]) / 2, 4) for k in range(3)]
            box["min"] = [round(x, 4) for x in box["min"]]
            box["max"] = [round(x, 4) for x in box["max"]]
            item["parts"].append(box)
        out[v] = item
    return out


def driver_socket() -> dict:
    doc = json.load(open(os.path.join(BAT, "SOCKETS_JC3.json"), encoding="utf-8"))
    for row in doc["sockets"]:
        if row.get("socket") == "Driver":
            return {k: row.get(k) for k in ("socket", "bone", "part_hint", "position_m",
                                            "forward_jc3")}
    raise LookupError("no Driver socket in SOCKETS_JC3.json")


def cockpit_facts() -> dict:
    """The G1-19 numbers this card compares against (parsed, not retyped)."""
    path = os.path.join(BAT, "COCKPIT.md")
    txt = open(path, encoding="utf-8").read()
    # COCKPIT.md writes its minus signs as U+2212, so normalise before parsing.
    txt = txt.replace("\u2212", "-")
    out = {}
    m = re.search(r"`position_m`[^\n]*?\*\*\(\s*(-?\d+\.\d+),\s*(-?\d+\.\d+),\s*(-?\d+\.\d+)",
                  txt)
    if m:
        out["hip_m"] = [float(m.group(i)) for i in (1, 2, 3)]
    m = re.search(r"ray down onto slot\s+\d+\)\s*\|\s*\*\*y\s*(-?\d+\.\d+)\*\*", txt)
    if m:
        out["cushion_top_m"] = float(m.group(1))
    return out


def card_inputs(rows: list[dict]) -> dict:
    """What the card's In list promises, counted in the index.

    The card names `jc_statemachine/vehicles/*` and `jc_skeletons/vehicles/*.bsk`.  Both are
    absent; the counts below are what the archive actually carries, so the report can say
    "absent" with a number instead of leaving a hole.
    """
    def n(sub: str) -> int:
        return sum(1 for r in rows if sub in r["path"])

    return {
        "jc_statemachine/vehicles/": n("jc_statemachine/vehicles/"),
        "jc_skeletons/vehicles/": n("jc_skeletons/vehicles/"),
        "jc_statemachine/": n("jc_statemachine/"),
        "jc_skeletons/": n("jc_skeletons/"),
        "vehicle .ban clips": sum(1 for r in rows if r["path"].endswith(".ban")
                                  and "/vehicle/" in r["path"]),
        "rico/vehicle .ban clips": sum(1 for r in rows if r["path"].endswith(".ban")
                                       and "/rico/vehicle/" in r["path"]),
    }


def build() -> dict:
    rows = jc3index.load_index(jc3index.DEFAULT_OUT)
    sm = {p: read(p, rows) for p in SM_FILES}
    afsmb = strings(sm[SM_FILES[0]])
    asb = strings(sm[SM_FILES[1]])
    fam = clip_families(asb)
    sel = selectors(afsmb + asb)
    parts = parts_of(rows)
    boxes = seat_boxes(rows, parts)
    sock = driver_socket()
    hip = sock["position_m"][1]
    seat_rows = []
    for v, item in boxes.items():
        if not item.get("parts"):
            seat_rows.append({"vehicle": v, "entity": item.get("entity"),
                              "error": item.get("error", "no seat hull"), "hulls": item["hulls"]})
            continue
        for b in item["parts"]:
            seat_rows.append({"vehicle": v, "entity": item["entity"], "part": b["name"],
                              "part_class": b.get("class"),
                              "index": b["index"], "shapes": b["shapes"],
                              "box_m": [b["min"], b["max"]], "size_m": b["size_m"],
                              "centre_m": b["centre_m"], "hulls": item["hulls"],
                              "file": item.get("file")})
    cands = [r for r in seat_rows if "centre_m" in r]
    best = None
    for r in cands:
        dy = abs(r["centre_m"][1] - hip)
        if best is None or dy < best["delta_m"]:
            best = {"vehicle": r["vehicle"], "part": r["part"], "seat_y_m": r["centre_m"][1],
                    "delta_m": round(dy, 4)}
    doc = {
        "card": "G2-19",
        "generated_by": "Tools/scripts/jc3seat.py --write",
        "card_inputs": card_inputs(rows),
        "state_machine": {"files": {p: len(sm[p]) for p in SM_FILES},
                          "strings": {SM_FILES[0]: len(afsmb), SM_FILES[1]: len(asb)}},
        "clips": {k: {"count": len(v), "sample": v[:3]} for k, v in fam.items()},
        "selectors": sel,
        "points": points_of(),
        "seats": seat_rows,
        "driver_socket": sock,
        "cockpit": cockpit_facts(),
        "candidate": {"hip_y_m": hip, "nearest": best},
    }
    return doc


def report(doc: dict) -> str:
    L: list[str] = []
    a = L.append
    sm, sel, pts = doc["state_machine"], doc["selectors"], doc["points"]
    clips = doc["clips"]
    hip = doc["candidate"]["hip_y_m"]
    best = doc["candidate"]["nearest"]
    a("# Driver seat and pose (G2-19)")
    a("")
    a("**Answer: the car does not own the pose.** A JC3 vehicle places the driver with one")
    a("interaction-graph object and says nothing else about him; the *pose* is the character state")
    a("machine's vehicle state, and its animation set carries one clip family per **vehicle class**.")
    a("")
    a("| question | answer | evidence |")
    a("|---|---|---|")
    a(f"| what places Rico | `entry.driver` (`CInteractionGraphEntry`, state "
      f"`{next((r['state'] for r in pts['rows'] if r['name'] == 'entry.driver' and r.get('state')), 'UNKNOWN')}`) "
      f"plus its siblings - **{pts['count']}** driver-named objects "
      f"({', '.join(f'{k} {v}' for k, v in pts['by_prefix'].items())}) | "
      f"`INTERACTION.json` (G2-18), donor `.epe` |")
    a(f"| what chooses his pose | `rico_base.afsmb` (state machine) over `rico_base.asb` "
      f"(animation set), by vehicle class | {sm['files'][SM_FILES[0]]:,} B + "
      f"{sm['files'][SM_FILES[1]]:,} B, {sm['strings'][SM_FILES[0]]} / {sm['strings'][SM_FILES[1]]} strings |")
    a(f"| how many pose families | **{len(clips)}** vehicle classes, {sum(c['count'] for c in clips.values())} clip names | `.asb` string table |")
    seats_only = [(r["vehicle"][:5], r) for r in doc["seats"]
                  if "centre_m" in r and r.get("part_class") == "Land_Seat"]
    a("| how high each sits | `Land_Seat` part hull centres "
      f"{', '.join(f'{v} {r['centre_m'][1]:.3f} m' for v, r in seats_only)} "
      f"({len(seats_only)} of {len(doc['seats'])} candidate parts are a `Land_Seat`) "
      "| `.physicsc` hulls |")
    ci = doc["card_inputs"]
    a(f"| what the card's In list promises | `jc_statemachine/vehicles/*` **{ci['jc_statemachine/vehicles/']} files**, "
      f"`jc_skeletons/vehicles/*.bsk` **{ci['jc_skeletons/vehicles/']} files** - both absent; "
      f"{ci['jc_statemachine/']} state-machine files are character-side, {ci['jc_skeletons/']} skeleton "
      f"files in total, {ci['vehicle .ban clips']} vehicle `.ban` clips | `INDEX.jsonl` |")
    a(f"| candidate for the Batmobile | **{best['vehicle']} / `{best['part']}`** at "
      f"{best['seat_y_m']:.3f} m vs the `Driver` hip {hip:.3f} m ({best['delta_m'] * 1000:.0f} mm) | "
      f"`SOCKETS_JC3.json` + seat boxes |" if best else "| candidate | none measurable | - |")
    a("")
    a("## 1. Where Rico is placed - the vehicle side")
    a("")
    a("A JC3 vehicle entity has **no seat, occupant, pose or animation module**. The donor's")
    a("container holds 31 `.vmodc` modules and the fleet's module vocabulary is 52 types; none is")
    a("about a character. What it does have is the interaction graph:")
    a("")
    a("| object | class | state | verts (Serpente frame) | verdict |")
    a("|---|---|---|---|---|")
    for r in pts["rows"]:
        if r["class"] not in ("CInteractionGraphEntry", "CInteractionGraphExit",
                             "CInteractionGraphPointNode"):
            continue
        if r.get("state") is None and r["class"] != "CInteractionGraphPointNode":
            continue
        pos = r.get("serpente_m")
        a(f"| `{r['name']}` | `{str(r['class']).replace('CInteractionGraph', '')}` | "
          f"`{r.get('state') or '-'}` | "
          f"{', '.join(f'{x:.3f}' for x in pos) if pos else '-'} | {r.get('verdict') or '-'} |")
    a("")
    a("Those objects are the *attach* half only: a state string plus a transform. The state is")
    a("consumed by the character, which is why the pose is not here.")
    a("")
    a("## 2. Where his pose is chosen - the character side")
    a("")
    a(f"`rico_base.afsmb` ({sm['files'][SM_FILES[0]]:,} B) is Rico's state machine. The names that")
    a("matter, straight out of its string table:")
    a("")
    a("| kind | count | examples |")
    a("|---|---|---|")
    a(f"| entry actions | {len(sel['enter'])} | {', '.join(f'`{x}`' for x in sel['enter'][:4])} |")
    a(f"| exit actions | {len(sel['exit'])} | {', '.join(f'`{x}`' for x in sel['exit'][:3])} |")
    a(f"| vehicle states | {len(sel['states'])} | {', '.join(f'`{x}`' for x in sel['states'][:3])} |")
    a(f"| driver-seat conditions | {len(sel['seats'])} | {', '.join(f'`{x}`' for x in sel['seats'][:4])} |")
    a(f"| driving IK targets | {len(sel['ik'])} | {', '.join(f'`{x}`' for x in sel['ik'][:4])} |")
    a(f"| class selectors (`MOD_*`) | {len(sel['mods'])} | {', '.join(f'`{x}`' for x in list(sel['mods'])[:6])} |")
    a("")
    a("So the mode is named in the state name itself: `ANIM_…_VEHICLE_MOD_<CLASS>`. The pose")
    a("families come from `rico_base.asb`'s clip paths, which group by class directory:")
    a("")
    a("| class | clips | sample |")
    a("|---|---|---|")
    for k, v in clips.items():
        sample = v["sample"][0].rsplit("/", 1)[-1] if v["sample"] else ""
        a(f"| `{k}` | {v['count']} | `{sample}` |")
    a("")
    a(f"**{sum(c['count'] for c in clips.values())} clip paths** across **{len(clips)}** classes. They are")
    a(f"*names inside the `.asb`*, not archive entries: the index lists "
      f"only {doc['card_inputs']['rico/vehicle .ban clips']} of Rico's vehicle `.ban` files")
    a("(both `…/rico/vehicle/mech/rico_vehi_mech_driver_to_{std,rollout}.ban`, a mech suit, not a")
    a("car) out of 7 `.ban` files under any `…/vehicle/` path, so an animation-set bundle is the")
    a("only place a seated car clip is addressable from.")
    a("")
    a("## 3. Seat heights - what each class actually sits on")
    a("")
    a("The seat is a *part*, and a part's collision is a convex hull in the `.physicsc`, so the")
    a("seat box is measurable per vehicle. The reference is the Batmobile: `Driver` socket hip")
    a(f"**{hip:.3f} m** (`SOCKETS_JC3.json`), and the donor's own seat-box centre is")
    a(f"{next((r['centre_m'][1] for r in doc['seats'] if 'centre_m' in r and 'sportsmuscle' in str(r.get('part'))), float('nan')):.3f} m")
    a("- within a centimetre, which is what makes a box centre a usable seat height.")
    a("")
    a("| vehicle | part | part class | hulls | box x × y × z (m) | centre y | Δ vs hip |")
    a("|---|---|---|---|---|---|---|")
    for r in doc["seats"]:
        if "centre_m" not in r:
            a(f"| `{r['vehicle']}` | {r.get('error', '-')} | - | {r.get('hulls', 0)} | - | - | - |")
            continue
        a(f"| `{r['vehicle'][:5]}` | `{r['part']}` | `{r.get('part_class') or '-'}` | {r['shapes']} | "
          f"{r['size_m'][0]:.3f} × {r['size_m'][1]:.3f} × {r['size_m'][2]:.3f} | "
          f"{r['centre_m'][1]:.3f} | {(r['centre_m'][1] - hip) * 1000:+.0f} mm |")
    a("")
    a("A hull is a part's whole envelope (cushion to headrest for a seat), so its **centre** is")
    a("the comparison quantity, not its top. What the table shows, read strictly:")
    a("")
    seat_vals = ", ".join(f"{r['centre_m'][1]:.3f}" for _, r in seats_only)
    a(f"* The {len(seats_only)} **`Land_Seat`** parts sit at {seat_vals} m -")
    a("  a span of 39 mm, i.e. JC3's car seats ship at one height whatever the class.")
    a("* `v0401`'s `racingsupercar_seats` is a real `Land_Seat` part but **no compound")
    a("  instance carries its index**, so that car has no seat hull and no measurable height.")
    a("* `v0201`'s only candidate is `mediumtank_hatch`, class **`Land_Door`** - a hatch, not a")
    a("  seat. Its 2.879 m is a door roof; the tank's seat height is **UNKNOWN**, not that number.")
    a("")
    a("## 4. The candidate pose")
    a("")
    if best:
        family = [k for k in clips if k.split("/")[0] ==
                  ("car" if "car" in best["vehicle"] else best["vehicle"].split("_")[1])]
        a(f"Closest seat to the Batmobile's `Driver` hip: **{best['vehicle']} / `{best['part']}`**,")
        a(f"seat centre **{best['seat_y_m']:.3f} m**, i.e. **{best['delta_m'] * 1000:.0f} mm** from the hip. That")
        a("vehicle is a car, so the alternatives the code can pick from are the car families")
        a(f"`{', '.join(family) if family else 'UNKNOWN'}`")
        a(f"({', '.join(str(clips[k]['count']) for k in family) if family else '-'} clips). The three sub-classes")
        a("(`low` 23, `med` 35, `circuit` 9) are alternatives, not a set: only one plays. The bare")
        a("`car` family, whose clips are the transfer ones, is shown for completeness:")
        for k in family[:1]:
            for p in clips[k]["sample"][:4]:
                a(f"`{p}`")
        a("")
        a("**This is a candidate, not a decision.** The mapping vehicle → class is chosen by native")
        a("code: no file in the index maps `v0300` (or any entity) to `car/low`, `car/med` or")
        a("`car/circuit`, and none of the three class folders is named inside the vehicle's own")
        a("modules. The seat height narrows it; only an in-game look (phase Q) can confirm which")
        a("clip plays, and whether the Batmobile's higher hip needs the `car/med` set at all.")
    else:
        a("No seat box could be measured - `UNKNOWN`.")
    a("")
    a("## 5. What this means for ANI-9 / APP-3")
    a("")
    a("* **The attach half is translatable.** `entry.driver` is a transform plus a state string, so")
    a("  the Batmobile's `Driver` socket (G1-13) can carry it; the state name is the contract.")
    a("* **The pose half is not a vehicle member.** Nothing the mod can edit on the car chooses the")
    a("  seated clip; it follows from the character state machine plus a class the game derives.")
    a("  T-13 can place the entry point, but \"Rico sits believably\" stays a phase-Q observation")
    a("  unless the class can be forced (a Q-1 probe: watch whether the hands land on the")
    a("  Batmobile's yoke or far below it).")
    a("* **Seat height is a build input** for the cockpit (G1-19 gave the hip; this card gives the")
    a("  fleet's range and the nearest shipped seat).")
    a("")
    a("## 6. Files and commands")
    a("")
    a("```")
    a("python Tools/scripts/jc3seat.py --write    # this report + SEAT.json")
    a("python Tools/scripts/jc3seat.py --check    # re-derive and compare")
    a("```")
    a("")
    a("Inputs: `Research/JC3Grab/INTERACTION.json` (G2-18), `PARTS_TABLE.jsonl` (G2-7), each")
    a("vehicle's `.physicsc` (`jc3hkx`), `rico_base.afsmb` / `rico_base.asb` (read from the archives,")
    a("`D:\\Games` read-only), `Research/BatmobileGrab/SOCKETS_JC3.json` + `COCKPIT.md` (G1-13/G1-19).")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("1. **The vehicle → pose-class mapping.** Named classes exist (`MOD_TANK`, `MOD_BOAT_SPY`,")
    a("   `MOD_SPORTBIKE`, `MOD_HELI`, car `low`/`med`/`circuit`); which class any given entity gets")
    a("   is native. UNKNOWN, not guessed from the vehicle's name.")
    a("2. **The clip bodies.** The seated `.ban` clips are not separate entries, and the `.asb`")
    a("   container format is not decoded here - only its string table is read. Clip lengths,")
    a("   tracks and bone lists are UNKNOWN.")
    a("3. **The tank's seat height.** `v0201` has no seat part at all - its only driver-ish part is")
    a("   `mediumtank_hatch` (part 39, class `Land_Door`). The 2.879 m in the table is a door, so")
    a("   the tank's seat height and the `tank` clip family's seated height are UNKNOWN.")
    a("4. **The supercar's seat hull.** `v0401` has a `Land_Seat` part (`racingsupercar_seats`,")
    a("   index 19) but no compound instance carries index 19 or 22 - either that part has no")
    a("   collision at all or it is carried by a shape class `jc3hkx` does not enumerate. UNKNOWN")
    a("   which, and it does not affect the candidate (the candidate is the muscle car).")
    a("4. **Whether the Batmobile's hip (0.865 m) is inside the shipped range.** The roster spans")
    a("   several classes, but a class is chosen by code, so \"inside the range\" is not the same as")
    a("   \"will play that class\".")
    a("")
    return "\n".join(L)


def dump(what: str) -> int:
    doc = build()
    if what == "clips":
        print(json.dumps(doc["clips"], indent=1)[:4000])
    elif what == "states":
        print(json.dumps(doc["selectors"], indent=1)[:4000])
    elif what == "seats":
        print(json.dumps(doc["seats"], indent=1)[:4000])
    elif what == "points":
        print(json.dumps(doc["points"], indent=1)[:4000])
    else:
        print("dump clips|states|seats|points")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write SEAT.md + SEAT.json")
    ap.add_argument("--check", action="store_true", help="re-derive and compare")
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
    best = doc["candidate"]["nearest"]
    summary = (f"{doc['points']['count']} driver points | {len(doc['clips'])} pose classes "
               f"({sum(c['count'] for c in doc['clips'].values())} clip names) | "
               f"{len(doc['selectors']['mods'])} MOD selectors | "
               f"seat boxes {sum(1 for r in doc['seats'] if 'centre_m' in r)} | "
               f"candidate {best['vehicle'] if best else '-'} "
               f"({best['delta_m'] * 1000:.0f} mm from the hip)" if best else "no seat box")
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
                                                          "disk", "derived", lineterm="", n=0)][:10]
                bad.append(f"{what} stale: " + " | ".join(diff))
        if bad:
            for b in bad:
                print("FAIL", b)
            print(f"{len(bad)} problem(s)")
            return 1
        print(f"PASS: {summary}, json match True, md match True")
        return 0
    print(f"OK: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
