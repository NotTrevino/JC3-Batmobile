#!/usr/bin/env python
"""jc3eject.py - G2-20: what an exit does, and whether anything launches the driver upward.

The card asks two questions and the data answers them in two different places:

1. **What each exit does.** An exit is a `CInteractionGraphExit` object in the vehicle's `.epe`
   graph. Its *members* say what it does - a `state` string (the animation state the player
   enters), a `modifier` (a class selector), `enabled`, `interaction` - and its *child* condition
   objects say when the game offers it. Conditions are child objects, so they can only be
   attributed to their exit in a nested tree: `Research/Epe/serpente_civilian.xml` is the only
   `.epe` kept that way. The G2-18 detail JSON flattens objects **sorted by id**, and ids repeat,
   so object order carries no nesting and the fleet's condition→exit mapping is not derivable
   there (stated as a limit, not guessed).
2. **Whether any vehicle launches the driver upward.** That would need a member carrying a
   velocity/impulse. There is none: the exit's whole member set is the 9 keys below, in all 232
   vehicle graphs, and the graph vocabulary has exactly one class with "Velocity" in its name - a
   *condition*. The entity modules have one upward-impulse mechanism, `turbo_jump`, and it moves
   the **vehicle**.

Geometry is not recomputed here: the Serpente/Batmobile positions, parents and surface verdicts
come from `Research/JC3Grab/INTERACTION.json` (G2-18) - one transform for every asset (R2).

Writes `Research/JC3Grab/EJECT.md` + `EJECT.json`.  `--check` re-derives and compares both.

Usage:
  python jc3eject.py --write
  python jc3eject.py --check
  python jc3eject.py dump exits|fleet|launch|bmak
"""
from __future__ import annotations

import argparse
import collections
import difflib
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
DETAIL = os.path.join(RAW, "detail")
ENTITIES = os.path.join(RAW, "entities")
DONOR_XML = os.path.join(ROOT, "Research", "Epe", "serpente_civilian.xml")
INTERACTION = os.path.join(OUT, "INTERACTION.json")
OFFSETS = os.path.join(BAT, "BMSDK_OFFSETS.json")
NATIVE_MD = os.path.join(BAT, "NATIVE.md")

MD_NAME, JSON_NAME = "EJECT.md", "EJECT.json"
DONOR_STEM = "v0300_car_kensington_sportsmuscle"
DONOR_ENTITY = ("v0300_car_kensington_sportsmuscle__"
                "v0300_car_kensington_sportsmuscle_civilian_01")
ROOTS = ("CCar", "CBoat", "CHelicopter", "CMotorBike", "CAirPlane", "CTrain")

EXIT_CLASS = "CInteractionGraphExit"
LAUNCH_RE = re.compile(r"eject|launch|catapult|impulse|parachute|wingsuit", re.I)
JUMP_RE = re.compile(r"turbo_jump|high_up_in_air|gravity_multiplier_in_air|jump", re.I)
# The member set every exit is allowed to have. Anything outside this would be a launch vector.
EXIT_KEYS = {"_object_id", "disable_event", "enable_event", "enabled", "interaction",
             "modifier", "name", "name_hash", "state"}


# ----------------------------------------------------------------------------- donor .epe

def xml_props(el: ET.Element) -> dict[str, str]:
    """An `<object>`'s own `value` children, keyed by name (hashed ids kept as `id:…`)."""
    out: dict[str, str] = {}
    for c in el:
        if c.tag == "value":
            key = c.get("name") or ("id:" + (c.get("id") or ""))
            out[key] = c.text or ""
    return out


def xml_children_conditions(el: ET.Element) -> list[dict]:
    """The `*Condition` objects nested directly inside one object."""
    out = []
    for c in el:
        if c.tag != "object":
            continue
        pr = xml_props(c)
        cls = pr.get("_class") or ""
        if "Condition" not in cls:
            continue
        keep = {k: v for k, v in pr.items() if k in ("check", "min", "max")}
        out.append({"class": cls, "values": keep})
    return out


def donor_exits() -> list[dict]:
    root = ET.parse(DONOR_XML).getroot()
    exits = []
    for obj in root.iter("object"):
        pr = xml_props(obj)
        if pr.get("_class") != EXIT_CLASS:
            continue
        gate = [c for c in xml_children_conditions(obj)
                if c["class"] == "CInteractionGraphParentVelocityCondition"]
        exits.append({
            "name": pr.get("name"),
            "state": pr.get("state"),
            "modifier": pr.get("modifier"),
            "enabled": pr.get("enabled"),
            "interaction": pr.get("interaction"),
            "conditions": xml_children_conditions(obj),
            "gate": ({"min": float(gate[0]["values"].get("min", "nan")),
                      "max": float(gate[0]["values"].get("max", "nan"))} if gate else None),
        })
    return exits


def donor_geometry() -> dict[str, dict]:
    """name -> the G2-18 placement row (no transform recomputation)."""
    doc = json.load(open(INTERACTION, encoding="utf-8"))
    return {p["name"]: p for p in doc["points"] if (p.get("name") or "").startswith("exit")}


# ----------------------------------------------------------------------------- fleet

def detail_files() -> list[str]:
    return sorted(f for f in os.listdir(DETAIL) if f.endswith(".ee.json"))


def entity_files() -> list[str]:
    return sorted(f for f in os.listdir(ENTITIES) if f.endswith(".ee.json"))


def root_class(objs: list[dict]) -> str | None:
    for o in objs:
        if o.get("class") in ROOTS:
            return o["class"]
    return None


def fleet(limit: int = 0) -> dict:
    names: dict[str, dict] = {}
    classes: collections.Counter = collections.Counter()
    total = graphs = 0
    exit_key_union: collections.Counter = collections.Counter()
    per_root: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for fn in detail_files():
        doc = json.load(open(os.path.join(DETAIL, fn), encoding="utf-8"))
        objs = doc["epe"]["objects"]
        root = root_class(objs)
        graphs += 1
        for o in objs:
            cls = o.get("class") or ""
            classes[cls] += 1
            if cls != EXIT_CLASS:
                continue
            total += 1
            v = o.get("values") or {}
            nm = o.get("name") or ""
            rec = names.setdefault(nm, {"count": 0, "states": collections.Counter(),
                                        "roots": collections.Counter(),
                                        "modifiers": collections.Counter(),
                                        "enabled": collections.Counter()})
            rec["count"] += 1
            rec["states"][v.get("state")] += 1
            rec["roots"][root or "?"] += 1
            rec["modifiers"][v.get("modifier")] += 1
            rec["enabled"][v.get("enabled")] += 1
            per_root[root or "?"][nm] += 1
            for k in v:
                exit_key_union[k] += 1
    out = {}
    for nm, rec in names.items():
        out[nm] = {"count": rec["count"],
                   "states": dict(rec["states"]),
                   "roots": dict(rec["roots"]),
                   "modifiers": {str(k): c for k, c in rec["modifiers"].items()},
                   "enabled": {str(k): c for k, c in rec["enabled"].items()}}
    if limit:
        out = dict(sorted(out.items(), key=lambda kv: -kv[1]["count"])[:limit])
    return {
        "graphs": graphs,
        "exits": total,
        "distinct_names": len(names),
        "names": out,
        "classes": dict(classes),
        "exit_keys": dict(exit_key_union),
        "unexpected_keys": sorted(k for k in exit_key_union if k not in EXIT_KEYS),
        "by_root": {r: dict(sorted(c.items(), key=lambda kv: -kv[1])) for r, c in per_root.items()},
    }


def module_sweep() -> dict:
    """Every vehicle module member whose *name* suggests a launch, plus the jump vocabulary."""
    launch: collections.Counter = collections.Counter()
    jump: collections.Counter = collections.Counter()
    owners: dict[str, set] = collections.defaultdict(set)
    for fn in entity_files():
        doc = json.load(open(os.path.join(ENTITIES, fn), encoding="utf-8"))
        for mod in doc.get("modules") or []:
            if not mod.get("type"):
                continue
            for r in mod.get("rows", []):
                p = r.get("path", "")
                if LAUNCH_RE.search(p):
                    launch[f"{mod['type']}.{p}"] += 1
                    owners[f"{mod['type']}.{p}"].add(fn)
                if JUMP_RE.search(p):
                    jump[f"{mod['type']}.{p}"] += 1
                    owners[f"{mod['type']}.{p}"].add(fn)
    return {"launch": dict(launch), "jump": dict(jump),
            "files": {k: len(v) for k, v in owners.items()}}


def donor_jump_values() -> dict:
    doc = json.load(open(os.path.join(ENTITIES, DONOR_ENTITY + ".ee.json"), encoding="utf-8"))
    out = {}
    for mod in doc.get("modules") or []:
        if not mod.get("type"):
            continue
        for r in mod.get("rows", []):
            p = r.get("path", "")
            if JUMP_RE.search(p) and "fins" not in p and "falloff" not in p:
                out[f"{mod['type']}.{p}"] = r.get("value")
    return out


def donor_exit_rows() -> list[dict]:
    geo = donor_geometry()
    rows = []
    for e in donor_exits():
        g = geo.get(e["name"], {})
        conds = [{"class": c["class"], "values": c["values"]} for c in e["conditions"]]
        rows.append({
            "name": e["name"],
            "state": e["state"],
            "modifier": e["modifier"],
            "enabled": e["enabled"],
            "interaction": e["interaction"],
            "parent": g.get("parent"),
            "serpente": g.get("serpente"),
            "batmobile": g.get("batmobile"),
            "verdict": g.get("verdict"),
            "surface_m": g.get("surface_m"),
            "gate": e["gate"],
            "conditions": conds,
            "condition_classes": [c["class"] for c in conds],
        })
    return sorted(rows, key=lambda r: r["name"] or "")


# ----------------------------------------------------------------------------- BmAK

def bmak_eject() -> dict:
    doc = json.load(open(OFFSETS, encoding="utf-8"))
    props = []
    for cname, c in doc["classes"].items():
        for p in c["properties"]:
            m = p["member"]
            if "Eject" in m or "GetOut" in m:
                props.append({"class": cname, "namespace": c.get("namespace"),
                              "offset": p["offset"], "kind": p["kind"],
                              "type": p["type"], "member": m})
    props.sort(key=lambda r: (r["class"], r["offset"]))
    native = ""
    if os.path.exists(NATIVE_MD):
        for line in open(NATIVE_MD, encoding="utf-8", errors="replace"):
            if "ModifyEjectUpLoc" in line or "SetBatmobileExit" in line:
                native += line.strip() + " "
    return {"properties": props,
            "classes": sorted({p["class"] for p in props}),
            "native": native.strip()}


# ----------------------------------------------------------------------------- build

def build() -> dict:
    doc = {
        "card": "G2-20",
        "donor": {"entity": DONOR_ENTITY, "xml": "Research/Epe/serpente_civilian.xml",
                  "geometry_from": "Research/JC3Grab/INTERACTION.json (G2-18)",
                  "exits": donor_exit_rows()},
        "fleet": fleet(),
        "launch": module_sweep(),
        "donor_jump": donor_jump_values(),
        "bmak": bmak_eject(),
    }
    doc["counts"] = {
        "donor_exits": len(doc["donor"]["exits"]),
        "donor_with_gate": sum(1 for e in doc["donor"]["exits"] if e["gate"]),
        "donor_without_condition": sum(1 for e in doc["donor"]["exits"] if not e["conditions"]),
        "fleet_graphs": doc["fleet"]["graphs"],
        "fleet_exits": doc["fleet"]["exits"],
        "fleet_names": doc["fleet"]["distinct_names"],
        "exit_launch_members": sum(c for k, c in doc["fleet"]["exit_keys"].items()
                                   if re.search(r"veloc|impulse|launch|force|speed", k)),
        "graph_classes_with_launch_name": sum(
            1 for c in doc["fleet"]["classes"]
            if re.search(r"Veloc|Impulse|Launch|Eject|Force", c)),
        "module_launch_members": len(doc["launch"]["launch"]),
        "bmak_eject_props": len(doc["bmak"]["properties"]),
    }
    blob = json.dumps(doc, sort_keys=True, separators=(",", ":"))
    doc["digest"] = hashlib.md5(blob.encode()).hexdigest()[:16]
    return doc


# ----------------------------------------------------------------------------- report

def fmt_gate(g: dict | None) -> str:
    if not g:
        return "-"
    return f"{g['min']:g}..{g['max']:g}"


def cond_text(conds: list[dict]) -> str:
    if not conds:
        return "none"
    parts = []
    for c in conds:
        cls = c["class"].replace("CInteractionGraph", "")
        v = c["values"]
        bits = [f"{k} {v[k]}" for k in ("min", "max", "check") if k in v]
        parts.append(cls + (" (" + ", ".join(bits) + ")" if bits else ""))
    return "<br>".join(parts)


def num(v) -> str:
    """A module value as the file means it: float32 noise trimmed, ints plain."""
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, float):
        return f"{v:g}"
    if isinstance(v, int):
        return str(v)
    return str(v)


JUMP_ROLE = (("punch_delay_time", "s, delay before the punch"),
             ("punch_speed_kph", "km/h, the speed the jump punches to"),
             ("top_speed_kph", "km/h, the speed cap while airborne"),
             ("top_speed_jump_multiplier", "x, cap multiplier during the jump"),
             ("f_multiplier", "x, forward multiplier"),
             ("r_multiplier", "x, reverse multiplier"),
             ("gravity_multiplier_in_air_up", "x, gravity while rising"),
             ("gravity_multiplier_in_air_down", "x, gravity while falling"),
             ("high_up_in_air_height", "game units, the vehicle's air height"),
             ("cooldown_upgraded", "s, upgraded cooldown"),
             ("cooldown", "s, cooldown between jumps"))


def jump_role(key: str) -> str:
    for tail, text in JUMP_ROLE:
        if key.endswith(tail):
            return text
    return "no unit stated in the file"


def pos(p) -> str:
    if not p:
        return "-"
    return f"({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})"


def report(doc: dict) -> str:
    L: list[str] = []

    def a(s: str = "") -> None:
        L.append(s)

    d = doc["donor"]
    f = doc["fleet"]
    c = doc["counts"]
    exits = d["exits"]
    gated = [e for e in exits if e["gate"]]
    para = next((e for e in exits if e["name"] == "exit.driver.moving.parachute"), None)
    roll = next((e for e in exits if e["name"] == "exit.driver.roll.out"), None)
    still = next((e for e in exits if e["name"] == "exit.driver.default"), None)
    fall = next((e for e in exits if e["name"] == "exit.driver.to.fall"), None)

    a("# Exit, bail-out and eject (G2-20)")
    a("")
    a(f"Generated by `Tools/scripts/jc3eject.py` (digest `{doc['digest']}`). The donor is")
    a(f"`{DONOR_ENTITY}`; the fleet figures are all")
    a(f"{c['fleet_graphs']} vehicle `.epe` graphs in `{DETAIL}`.")
    a("")
    a("**The short answer.** JC3 has no eject. An exit in this game is a *state name* plus a set of")
    a("gates, and the only numbers any exit carries are the gates. Nothing in the graph or in the")
    a("vehicle's modules can push the driver upward; the one upward impulse the data does carry,")
    a("`turbo_jump`, moves the **car**. Exiting above the speed gate selects")
    a(f"`exit.driver.moving.parachute` → `{para['state'] if para else 'UNKNOWN'}` — that is the")
    a("carrier MOD-3 gets, and the launch half is UNKNOWN with a Q-1 probe below.")
    a("")
    a("## 1. What an exit is, in this game's data")
    a("")
    a(f"`CInteractionGraphExit` objects: **{c['fleet_exits']}** in {c['fleet_graphs']} graphs,")
    a(f"{c['fleet_names']} distinct names, {c['donor_exits']} in the donor. Every one of them has its")
    a(f"members from a set of **{len(f['exit_keys'])} keys**:")
    a("")
    a(", ".join(f"`{k}`" for k in sorted(f['exit_keys'])) + ".")
    a("")
    a("| member | what it is |")
    a("|---|---|")
    a("| `name` / `name_hash` | the graph's identifier (`exit.driver.moving.parachute`) |")
    a("| `state` | the state string the player enters (`S_EXIT_VEHICLE_PARA`) — the actual contract |")
    a("| `modifier` | a class selector (`MOD_HELI_ASSAULT`, `MOD_JET_BEHIND`, `MOD_RIGHT`, …) |")
    a(f"| `enabled` | `1` on all {c['fleet_exits']}; `0` never appears |")
    a(f"| `interaction` | object pointer, `00000000` (null) on all {c['fleet_exits']} |")
    a("| `disable_event` / `enable_event` | event lists, empty on every donor exit |")
    a("")
    a("**There is no launch field.** Members whose *name* suggests one (`velocity`, `impulse`,")
    a(f"`launch`, `force`, `speed`): **{c['exit_launch_members']}**. Keys outside the set above,")
    a(f"anywhere in the fleet: **{len(f['unexpected_keys'])}**"
      + (f" ({', '.join(f['unexpected_keys'])})" if f["unexpected_keys"] else "") + ".")
    a("")
    launch_classes = [k for k in f["classes"]
                      if re.search(r"Veloc|Impulse|Launch|Eject|Force", k)]
    a(f"The graph vocabulary is **{len(f['classes'])}** classes. Those with Velocity/Impulse/"
      f"Launch/Eject/Force in the name: **{len(launch_classes)}** —")
    a(", ".join(f"`{k}`" for k in sorted(launch_classes)) + ".")
    a("`CInteractionGraphParentVelocityCondition` has")
    a(f"{f['classes'].get('CInteractionGraphParentVelocityCondition', 0)} instances and is a")
    a("**condition**: it gates an exit, it does not carry the player anywhere. The other is the")
    a("vehicle's own explosion pulse (`CForcePulse`, G2-17), which pushes away from the **car** and")
    a("has nothing to do with a seated driver. Neither is an exit action.")
    a("")
    a("**State-machine refs.** An exit's state string appears twice in the donor's `.epe`: as the")
    a("exit's own `state`, and inside its `ExitObstructedCondition` (the same string, under the")
    a("hashed key `id:A3CC001A`). There is no vehicle state machine to carry it - the index has 0")
    a("`jc_statemachine/vehicles/` files, and the 142 state machines it does carry are character-side")
    a("(G2-19, `SEAT.md`). So the exit hands the game a name and the name's behaviour lives in")
    a("native code plus Rico's animation set - not in a file the mod can edit.")
    a("")
    a("## 2. The donor's 26 exits")
    a("")
    a("Positions are G2-18's (Serpente-local metres → Batmobile-local metres, bbox mapping, **not**")
    a("the R2 build transform). `verdict` is G2-18's inside/floating check of that point.")
    a("")
    a("| exit | state | gate (parent speed) | conditions | parent | Serpente (m) | Batmobile (m) | verdict |")
    a("|---|---|---|---|---|---|---|---|")
    for e in exits:
        a(f"| `{e['name']}` | `{e['state']}` | {fmt_gate(e['gate'])} | {cond_text(e['conditions'])} | "
          f"`{e['parent'] or '-'}` | {pos(e['serpente'])} | {pos(e['batmobile'])} | {e['verdict'] or '-'} |")
    a("")
    a(f"{c['donor_with_gate']} of {c['donor_exits']} exits are speed-gated; "
      f"{c['donor_without_condition']} carry no condition at all:")
    a("")
    for e in exits:
        if not e["conditions"]:
            a(f"* `{e['name']}` → `{e['state']}`")
    a("")
    a("Those five are entered from code (a push, a pull, a roll-over), not offered by a gate.")
    a("")
    a("## 3. The speed gates, read strictly")
    a("")
    a("Every `CInteractionGraphParentVelocityCondition` is a `min`/`max` pair on the **parent's**")
    a("speed. The unit is not stated anywhere in the file — treat the numbers as game speed units")
    a("and the conversion as UNKNOWN. The donor's driver side splits at 5:")
    a("")
    a("| exit | gate | reads as |")
    a("|---|---|---|")
    if still:
        a(f"| `exit.driver.default` | {fmt_gate(still['gate'])} | offered below 5 — the plain "
          f"`{still['state']}` exit |")
    if fall:
        a(f"| `exit.driver.to.fall` | {fmt_gate(fall['gate'])} | below 5, with its own obstructed "
          "check — leaving into a fall |")
    if roll:
        a(f"| `exit.driver.roll.out` | {fmt_gate(roll['gate'])} | offered from 5 up — "
          f"`{roll['state']}` |")
    if para:
        a(f"| `exit.driver.moving.parachute` | {fmt_gate(para['gate'])} | offered from 5 up — "
          f"`{para['state']}` |")
    a("")
    a("So the **only** difference the data makes between exiting a parked car and exiting one at")
    a("speed is which state string plays: at speed the game offers the roll-out and the parachute")
    a("state, and `exit.driver.default` (0..5) is no longer available. The passenger side does the")
    a("same lower down: `pulled.out` 0..3, `roll.out` 3..999.")
    a("")
    a("Both high-speed exits have the same gate and no other condition on the donor's")
    a("`point.driver`, so **which one wins is not in the data** — UNKNOWN, probe Q1-EJ-B.")
    a("")
    a("## 4. What the fleet adds: which vehicle gets which exit")
    a("")
    everywhere = sorted(nm for nm, rec in f["names"].items() if len(rec["roots"]) >= 5)
    a("Counts are exits across the 232 graphs, by root class. The spread is the class coverage:")
    a("the driver's universal exits are on every class with a driver:")
    a("")
    for n in everywhere:
        a(f"* `{n}` ({f['names'][n]['count']} vehicles)")
    a("")
    a("and every `exit.ai.*` row reads 0 for motorbikes: an AI driver exits only cars, boats,")
    a("helicopters and jets.")
    a("")
    a("| exit | total | CCar | CBoat | CHelicopter | CMotorBike | CAirPlane | states seen |")
    a("|---|---|---|---|---|---|---|---|")
    for nm, rec in sorted(f["names"].items(), key=lambda kv: -kv[1]["count"])[:22]:
        r = rec["roots"]
        states = ", ".join(f"`{s}`" for s in rec["states"] if s) or "-"
        a(f"| `{nm}` | {rec['count']} | {r.get('CCar', 0)} | {r.get('CBoat', 0)} | "
          f"{r.get('CHelicopter', 0)} | {r.get('CMotorBike', 0)} | {r.get('CAirPlane', 0)} | {states} |")
    a("")
    plane_only = [nm for nm, rec in f["names"].items()
                  if set(rec["roots"]) == {"CAirPlane"}]
    heli_only = [nm for nm, rec in f["names"].items()
                 if set(rec["roots"]) == {"CHelicopter"}]
    a(f"Exits only jets carry ({len(plane_only)}): "
      + (", ".join(f"`{n}`" for n in sorted(plane_only)) or "none") + ".")
    a(f"Exits only helicopters carry ({len(heli_only)}): "
      + (", ".join(f"`{n}`" for n in sorted(heli_only)) or "none") + ".")
    a("")
    if para:
        pc = f["names"].get("exit.driver.moving.parachute", {}).get("count", 0)
        a(f"**`exit.driver.moving.parachute` is not car-specific**: it is on **{pc}** of the")
        a(f"{c['fleet_graphs']} vehicles, including every class that has a driver - boats,")
        a("helicopters, jets and bikes included. It is the generic \"leave at speed\" exit.")
    a("")
    mods = collections.Counter()
    for nm, rec in f["names"].items():
        for m, n in rec["modifiers"].items():
            if m != "None":
                mods[m] += n
    a(f"Non-null `modifier` values on exits fleet-wide ({len(mods)} distinct):")
    a("")
    a("| modifier | exits |")
    a("|---|---|")
    for m, n in sorted(mods.items()):
        a(f"| `{m}` | {n} |")
    a("")
    a("They are the same `MOD_*` class selectors G2-19 found in the character state machine, so")
    a("an exit's variant is chosen by a vehicle class the game derives - not by the exit's name.")
    a("")
    a("## 5. Does any vehicle launch the driver upward?")
    a("")
    a("Three sweeps, all negative on the driver:")
    a("")
    a(f"1. **Exits**: {c['exit_launch_members']} of {c['fleet_exits']} carry a"
      " velocity/impulse/force member (§1).")
    a(f"2. **Graph classes**: {c['graph_classes_with_launch_name']} of {len(f['classes'])} contain")
    a("   Veloc/Impulse/Launch/Eject/Force in their name - the velocity *condition* and the car's")
    a("   `CForcePulse`. No class applies motion to the driver.")
    a(f"3. **Vehicle modules**: the 232 entity graphs have **{c['module_launch_members']}**")
    a("   distinct member name matching eject/launch/catapult/impulse/parachute/wingsuit"
      + (": " + ", ".join(f"`{k}` ×{v}" for k, v in sorted(doc["launch"]["launch"].items()))
         if doc["launch"]["launch"] else "") + ".")
    a("")
    a("What the modules *do* carry is a jump — of the vehicle, not of the driver:")
    a("")
    a("| member | donor value | role |")
    a("|---|---|---|")
    for k, v in sorted(doc["donor_jump"].items()):
        a(f"| `{k}` | {num(v)} | {jump_role(k)} |")
    a("")
    jf = doc["launch"]["files"]
    a(f"`arcade.turbo_jump` is on "
      f"**{jf.get('CustomLandGlobal.arcade.turbo_jump.punch_speed_kph', 0)}** land vehicles,"
      f" `VehicleMisc.turbo_jump_cooldown` on **{jf.get('VehicleMisc.turbo_jump_cooldown', 0)}**.")
    a("Its members are speed punches and multipliers - **no vertical speed member exists**, so even")
    a("the car's rise is derived by code (UNKNOWN magnitude). It is also the wrong subject for")
    a("MOD-3: BmAK ejects *Batman*, not the car.")
    a("")
    a("**Conclusion:** no vehicle in the grab launches its driver upward. The state strings say")
    a("\"leave the car\" (roll out, pushed/pulled out, upside down, to fall, to swim, parachute);")
    a("none of them says \"up\". Whether the parachute state's *animation* happens to start with a")
    a("pop is animation data, not entity data, and the `.asb` clip bodies are not decoded here —")
    a("UNKNOWN, probe Q1-EJ-A.")
    a("")
    a("## 6. The BmAK side")
    a("")
    a("BmAK does have an eject, and it is authored as a **special move plus a distance**:")
    a("")
    a("| property | class | offset | kind |")
    a("|---|---|---|---|")
    for p in doc["bmak"]["properties"]:
        a(f"| `{p['member']}` | `{p['class']}` | `{p['offset']:#06x}` | {p['kind']} |")
    a("")
    a(f"Plus the natives `{doc['bmak']['native'] or 'UNKNOWN'}` (`NATIVE.md`), the `Eject` package")
    a("and the `Eject_To_Spot` special-move config (`ASSETS.md`). Read as behaviour:")
    a("")
    a("* The move set is split by *direction*: `EjectUpMove` / `EjectForwardMove`, each with a")
    a("  `…WhenBatmobileVerticalMove` variant, plus `EjectToSpotMove`. The property names are the")
    a("  only evidence for what the moves do — the special-move assets themselves are not decoded")
    a("  here, so \"up\" is the property name, not a measured trajectory.")
    a("* `EjectUpDist` (float) is the only **numeric** eject property on the vehicle. Its value is")
    a("  per-archetype and the grab has no archetype dump for it: the number is UNKNOWN, and so is")
    a("  what it measures (a distance is the reading the name supports, nothing more).")
    a("* `MaxEjectType` (byte, typed `EBatmobileEjectType`) and `OverrideNextEject` (typed")
    a("  `RSeqAct_OverrideBatmobileEject`) show the eject has *types* and can be overridden by a")
    a("  script action. The enum's members and the override's wiring are not in the grab (UNKNOWN).")
    a("* `GetOut*` moves are the ordinary exits, separate from the eject: BmAK keeps \"get out\" and")
    a("  \"eject\" as different animations - the same distinction JC3 makes with different exit")
    a("  *states*.")
    a("")
    a("## 7. The mapping for MOD-3 (launch → glide)")
    a("")
    a("| BmAK behaviour | JC3 carrier that exists | take that can fail | verdict |")
    a("|---|---|---|---|")
    a("| leave the car while moving | `exit.driver.moving.parachute` → `S_EXIT_VEHICLE_PARA` "
      f"(gated {fmt_gate(para['gate']) if para else '?'}) | exiting above the gate must play the "
      "para state, not the plain one | **stated** |")
    a("| leave the car at rest | `exit.driver.default` → `S_EXIT_VEHICLE` (gate "
      f"{fmt_gate(still['gate']) if still else '?'}) | at rest the plain exit must play | **stated** |")
    a("| side roll-out (fast, no chute) | `exit.driver.roll.out` → `S_ROLL_OUT_EXIT_VEHICLE` "
      f"(gate {fmt_gate(roll['gate']) if roll else '?'}) | both fast exits pass their gate; which "
      "one wins is code | **stated carrier, selection UNKNOWN** |")
    a("| **launch upward** (`EjectUpMove`, `EjectUpDist`) | **none** — 0 launch members in 4,832 "
      "exits, 0 in 232 module graphs | a data-authored upward impulse would have to exist; it does "
      "not | **UNKNOWN → Q1-EJ-A** |")
    a("| glide after the launch | the parachute state the exit selects | the para state must leave "
      "the player airborne with the chute available | **carrier named, behaviour UNKNOWN → Q1-EJ-C** |")
    a("")
    a("So MOD-3's honest position: **the exit half maps onto `exit.driver.moving.parachute`**, one")
    a("name and one state string, and the build can carry it unchanged (it is the donor's own exit,")
    a("already parented to `point.driver`). **The launch half has no JC3 carrier.** A build cannot")
    a("author an upward impulse from entity data; the choices are (a) accept exit + glide without")
    a("the launch, (b) a Q-1 probe to see whether the para animation already pops the player up, or")
    a("(c) use the vehicle's `turbo_jump` to jump the *car* at the same moment — visibly different,")
    a("and not what the lore asks for.")
    a("")
    a("## 8. UNKNOWNs, and the probes that would close them")
    a("")
    a("1. **The upward impulse.** No member carries it. Q1-EJ-A: exit the donor at a steady speed")
    a("   above the gate (e.g. 8 units, comfortably over 5) on flat ground with no input after the")
    a("   exit. Expected, hypothesis H1 (no launch): Rico's vertical velocity is ≤ 0 within 0.2 s")
    a("   and his apex is 0.0 m above the exit point (±0.2 m). Hypothesis H2 (launch): vertical")
    a("   velocity > 0 and apex > 1.0 m above the exit point. One launch, one variable (R13). The")
    a("   thresholds are probe design; the exit and its gate are the data.")
    a("2. **Which fast exit wins.** Both `roll.out` and `moving.parachute` pass their gate. Q1-EJ-B:")
    a("   exit at just over the gate; expect `S_ROLL_OUT_EXIT_VEHICLE` (side roll, no chute) or")
    a("   `S_EXIT_VEHICLE_PARA` (chute state). Observable without any new file: the two states look")
    a("   different.")
    a("3. **Whether the chute is automatic.** The exit only names a state; whether `S_EXIT_VEHICLE_PARA`")
    a("   deploys the parachute by itself or needs the usual chute input is UNKNOWN - Q1-EJ-C: exit")
    a("   at speed and input nothing; a chute that opens is H3, one that does not is H4.")
    a("4. **The gate's unit.** `min 5` / `max 999` are game speed units. Nothing in the file states")
    a("   the unit or the conversion to m/s, so no metres-per-second threshold is quoted here.")
    a("5. **The fleet's condition→exit mapping.** It is decoded for the donor only: the detail JSON")
    a("   sorts objects by id and ids repeat, so nesting cannot be recovered from it, and the other")
    a("   231 `.epe` files are not kept as XML. The fleet table therefore reports names, states and")
    a("   modifiers, and no per-vehicle gates.")
    a("6. **`EjectUpDist` and the eject moves.** `EjectUpDist` is a float property on")
    a("   `RVehicleBatmobileBase` with no value in the grab; the `Eject*Move` properties are")
    a("   `RSpecialMoveConfig` references whose assets are not decoded, so no eject trajectory,")
    a("   speed or height is quoted in this report.")
    a("")
    a("## 9. Reproduce")
    a("")
    a("```")
    a("python Tools/scripts/jc3eject.py --write    # this file + EJECT.json")
    a("python Tools/scripts/jc3eject.py --check    # re-derive and compare")
    a("```")
    a("")
    a("Inputs: `Research/Epe/serpente_civilian.xml` (donor `.epe`, nested),")
    a(f"`{DETAIL}/*.ee.json` ×{c['fleet_graphs']},")
    a(f"`{ENTITIES}/*.ee.json` ×{c['fleet_graphs']} (module rows),")
    a("`Research/JC3Grab/INTERACTION.json` (G2-18 positions),")
    a("`Research/BatmobileGrab/BMSDK_OFFSETS.json` + `NATIVE.md` + `ASSETS.md` (BmAK). All read-only;")
    a("no game launch, no archive write.")
    a("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- cli

def dump(what: str) -> int:
    doc = build()
    if what == "exits":
        print(json.dumps(doc["donor"]["exits"], indent=1)[:6000])
    elif what == "fleet":
        print(json.dumps({"counts": doc["counts"],
                          "by_root": doc["fleet"]["by_root"]}, indent=1)[:6000])
    elif what == "launch":
        print(json.dumps({"launch": doc["launch"]["launch"],
                          "jump": doc["launch"]["jump"],
                          "donor_jump": doc["donor_jump"]}, indent=1)[:6000])
    elif what == "bmak":
        print(json.dumps(doc["bmak"], indent=1)[:6000])
    else:
        print("dump exits|fleet|launch|bmak")
        return 2
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write EJECT.md + EJECT.json")
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
    c = doc["counts"]
    summary = (f"{c['fleet_exits']} exits in {c['fleet_graphs']} graphs ({c['fleet_names']} names) | "
               f"donor {c['donor_exits']} exits, {c['donor_with_gate']} speed-gated, "
               f"{c['donor_without_condition']} unconditional | launch members: exits "
               f"{c['exit_launch_members']}, graph classes {c['graph_classes_with_launch_name']}, "
               f"vehicle modules {c['module_launch_members']} | BmAK eject props "
               f"{c['bmak_eject_props']}")
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
