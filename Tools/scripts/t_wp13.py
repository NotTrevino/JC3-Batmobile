"""t_wp13.py - T-WP13: how many BmAK weapons JC3's driver-slot model can carry.

The row T-WP13 is blocked because D-7 wants all 11 BmAK weapons in both modes and the
fleet was read as "at most 2 driver slots, no active-slot index, no next/previous weapon
action".  This pass re-derives the three quantities the card asks for, from the files only:

  1. **slots per fleet vehicle** - `Research/JC3Grab/WEAPON_WIRING.jsonl` (G2-11's decode of
     all 232 entity graphs): the `counts.driver_slots` / `driver_weapons` fields and the
     `slots` map of every root, so the maximum is a measured number, not a recollection;
  2. **how a driver slot picks its weapon** - `Research/BatmobileGrab/DRIVINGMODE.md`
     (G3-02's decode of the `DrivingMode` state machine): the `SelectVehicleWeapon(<int>)`
     calls, whose integer argument is the slot index the quick-gadget states pass;
  3. **whether a next/previous action exists** - `Research/JC3Grab/INPUT.md` (G3-08's decode
     of the shipped `settings/keymap_*.bin`): every action whose name matches
     NEXT/PREV/SELECT weapon, its device and its scope.

It then writes the largest set the files support and an 11-weapon mapping, each assignment
labelled decoded / derived / UNKNOWN.  Nothing here edits `T_ROWS.jsonl` (read only).

Usage:
    uv run python Tools/scripts/t_wp13.py --write
    uv run python Tools/scripts/t_wp13.py --check
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WIRING = os.path.join(ROOT, "Research", "JC3Grab", "WEAPON_WIRING.jsonl")
INPUT = os.path.join(ROOT, "Research", "JC3Grab", "INPUT.md")
DRIVING = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVINGMODE.md")
ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
T7 = os.path.join(ROOT, "Working", "Translation", "T7_WEAPONS.md")
OUT = os.path.join(ROOT, "Working", "Translation")
MD = os.path.join(OUT, "T_WP13_PROPOSAL.md")
JS = os.path.join(OUT, "T_WP13_PROPOSAL.json")

DRIVER_PROPS = {"main_weapon", "secondary (id:00568A74)"}


# ------------------------------------------------------------------ the fleet
def fleet():
    rows = [json.loads(l) for l in open(WIRING, encoding="utf-8") if l.strip()]
    slots = Counter()
    two = []
    for r in rows:
        c = r["counts"]
        slots[c["driver_slots"]] += 1
        if c["driver_slots"] >= 2:
            root = r["roots"][0]
            two.append({"entity": r["entity"].split("jc_vehicles/")[-1],
                        "chassis": r["chassis"],
                        "slots": {k: (v.get("target"), v.get("prop"))
                                  for k, v in root["slots"].items()
                                  if k in DRIVER_PROPS},
                        "driver_weapons": c["driver_weapons"]})
    props = Counter()
    for r in rows:
        for root in r["roots"]:
            for k in root["slots"]:
                props[k] += 1
    return {"entities": len(rows), "slot_histogram": dict(sorted(slots.items())),
            "max_driver_slots": max(slots), "two_slot": two,
            "slot_names": dict(props.most_common()),
            "driver_entities": sum(v for k, v in slots.items() if k)}


# ------------------------------------------------------------------ input actions
def actions():
    out = []
    for line in open(INPUT, encoding="utf-8"):
        m = re.match(r"\| `([A-Z0-9_]+)` \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", line.strip())
        if not m:
            continue
        out.append({"action": m.group(1), "gamepad": m.group(2).strip(),
                    "keyboard": m.group(3).strip(), "scope": m.group(4).strip()})
    return out


# ------------------------------------------------------------------ driving mode
def drivemode():
    text = open(DRIVING, encoding="utf-8").read()
    sel = sorted({int(x) for x in re.findall(r"SelectVehicleWeapon\((\d+),", text)})
    rel = sorted({int(x) for x in re.findall(r"ReleaseVehicleWeapon\((\d+),", text)})
    states = re.findall(r"### `DrivingMode\.(QuickGadget\w+|ReleaseQuickGadget\w+)`", text)
    return {"select_args": sel, "release_args": rel, "states": states}


# ------------------------------------------------------------------ the demand
def demand():
    """The T-WP13 row and the 11 weapon rows it must place (read-only inputs)."""
    row = None
    ids = []
    for line in open(ROWS, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        ids.append(r["id"])
        if r["id"] == "T-WP13":
            row = {"dispo": r["dispo"], "why": r["why"]}
    weapons = [i for i in ids if re.fullmatch(r"T-WP\d+", i) and i not in
               ("T-WP12", "T-WP13", "T-WP14")]
    return {"row": row, "weapons": weapons, "rows": len(ids)}


# ------------------------------------------------------------------ proposal
# One entry per BmAK weapon: (id, name, slot, label, bound in a driver slot, why).
PROPOSAL = [
    ("WPN-1", "Heavy Cannon", "slot 1 `main_weapon` (`id:851CAABE`)",
     "decoded", True, "the medium tank binds `w602_mediumtank_canon` to this exact root "
     "property (G2-11), and the donor's own graph has the same member"),
    ("WPN-2", "Vulcan chain gun", "slot 2 `secondary (id:00568A74)`",
     "decoded", True, "the medium tank binds `w603_mediumtank_mgun` to the second driver "
     "property; it is the only land vehicle with two bound driver weapons (two helicopter "
     "and two plane chassis also bind two)"),
    ("WPN-3", "Missile launcher", "slot 3 (index only)", "derived", True,
     "`DrivingMode.SelectVehicleWeapon(3)` exists, so the state machine addresses a third "
     "index, but no fleet root has a third driver property to hold the missile (max 2) - "
     "the member behind index 3 is UNKNOWN"),
    ("WPN-4", "EMP missile", "slot 3, shared with WPN-3", "UNKNOWN", False,
     "same unresolved index; which of two weapons an index selects has no decoded member"),
    ("WPN-5", "EMP burst", "no weapon slot - entity `CForcePulse`", "decoded", False,
     "the pulse is an entity object (G2-16), not a driver slot; nothing decoded fires it"),
    ("WPN-6", "Power winch", "none", "decoded", False,
     "no winch class in the fleet (TETHER.md)"),
    ("WPN-7", "Drone hacker", "none", "decoded", False,
     "no allegiance-switch class in the fleet"),
    ("WPN-8", "Seismic sonar", "none", "decoded", False, "no sonar class in the fleet"),
    ("WPN-9", "Vehicle tracker", "none", "decoded", False, "no tracker class in the fleet"),
    ("WPN-10", "Riot suppressor", "none - a mode, not a weapon", "decoded", False,
     "no non-lethal flag in the member space; D-3 dropped it"),
    ("WPN-11", "Booster", "no slot - the nitro button", "decoded", False,
     "`arcade.nitro_boost` is a module block on 145/232 vehicles, not a weapon slot"),
]


def build():
    fl, ac, dm, de = fleet(), actions(), drivemode(), demand()

    sel = [a for a in ac if re.search(r"(?i)(next_weapon|prev_weapon|select.*weapon|weapon.*select)",
                                      a["action"])]
    fire = [a for a in ac if a["action"].startswith("FIRE_VEHICLE_WEAPON")]
    vehicle_sel = [a for a in sel if a["scope"] == "land-vehicle"]

    armed = fl["driver_entities"]
    capacity = len(dm["select_args"])          # quick-gadget indices 1..3
    bound = fl["max_driver_slots"]
    placed = sum(1 for p in PROPOSAL if p[4])
    decoded_binds = sum(1 for p in PROPOSAL if p[4] and p[3] == "decoded")
    lost = len(PROPOSAL) - placed

    d = {"fleet": fl, "actions": {"select": sel, "fire": fire,
                                  "next_prev": [a for a in sel if a["action"] in
                                                ("NEXT_WEAPON", "PREV_WEAPON")],
                                  "vehicle_select": vehicle_sel},
         "drivemode": dm, "demand": de, "proposal": PROPOSAL,
         "capacity": {"select_indices": capacity, "bound_slots": bound,
                      "placed": placed, "decoded_binds": decoded_binds, "lost": lost},
         "oracles": [], "md": ""}
    d["oracles"] = oracles(d)
    d["md"] = render(d)
    return d


def oracles(d):
    out = []

    def o(key, ok, ev):
        out.append({"key": key, "ok": bool(ok), "evidence": ev})

    fl, ac, dm, cap, de = (d["fleet"], d["actions"], d["drivemode"], d["capacity"],
                           d["demand"])
    o("O1-fleet-slot-max", fl["max_driver_slots"] == 2 and fl["entities"] >= 50,
      "%d armed entity graphs (of the 232 in the fleet): driver_slots histogram %s; "
      "%d carry a driver weapon; max %d"
      % (fl["entities"], fl["slot_histogram"], fl["driver_entities"],
         fl["max_driver_slots"]))
    o("O2-no-vehicle-select-action",
      not ac["vehicle_select"] and [a["action"] for a in ac["next_prev"]]
      == ["NEXT_WEAPON", "PREV_WEAPON"],
      "weapon-named actions: %s; land-vehicle scoped: %s"
      % ([(a["action"], a["scope"]) for a in ac["select"]], ac["vehicle_select"] or "none"))
    o("O3-select-indices", dm["select_args"] == [1, 2, 3],
      "`SelectVehicleWeapon(%s)` in %d quick-gadget state bodies; release side %s"
      % (",".join(map(str, dm["select_args"])), len(dm["states"]),
         dm["release_args"]))
    o("O4-capacity-is-two-bound", cap["bound_slots"] == 2 and cap["select_indices"] == 3,
      "state machine addresses %d indices, fleet binds at most %d root properties, so %d is "
      "the largest fully decoded set and the 3rd index has no member"
      % (cap["select_indices"], cap["bound_slots"], cap["bound_slots"]))
    o("O5-demand-exceeds-capacity", len(de["weapons"]) == 11 and cap["lost"] > 0,
      "%d weapon rows to place, %d addressable (%d decoded binds + 1 index), %d lost"
      % (len(de["weapons"]), cap["placed"], cap["decoded_binds"], cap["lost"]))
    o("O6-md-recomputed", True, "--check rebuilds this document from the files and compares it")
    return out


def render(d):
    L = []
    A = L.append
    fl, ac, dm, cap, de = d["fleet"], d["actions"], d["drivemode"], d["capacity"], d["demand"]
    A("# T-WP13 - the largest BmAK weapon set JC3's driver slots can carry")
    A("")
    A("Generated by `Tools/scripts/t_wp13.py --write`; `--check` re-reads every input and")
    A("fails on any change.  Static only: no game process was started or attached to.")
    A("")
    A("## 1. Answer")
    A("")
    A("**Two weapons can be bound at once; a third index is addressable but has no member.**")
    A("The fleet's own root properties hold at most **%d** driver weapons (%d of %d entity"
      % (fl["max_driver_slots"], fl["driver_entities"], fl["entities"]))
    A("graphs bind one), and the `DrivingMode` state machine calls")
    A("`SelectVehicleWeapon(1/2/3)` from its QuickGadgetB/X/Y states, i.e. it addresses **%d**"
      % cap["select_indices"])
    A("indices.  Only indices 1 and 2 have a decoded root property to point at, so")
    A("`main_weapon` + `secondary` is the largest set that can be written without inventing a")
    A("member.  No vehicle-scoped next/previous action exists: `NEXT_WEAPON` and")
    A("`PREV_WEAPON` ship on the keyboard (MWHEELUP/MWHEELDOWN) but are scoped on-foot and")
    A("nothing in the files says a vehicle consumes them.")
    A("")
    A("Against D-7's 11 weapons: **%d addressable** (%d decoded binds + 1 index with no"
      " member), **%d lost** (%s)."
      % (cap["placed"], cap["decoded_binds"], cap["lost"],
         ", ".join(p[0] for p in d["proposal"] if not p[4])))
    A("")
    A("## 2. Slots per fleet vehicle with a gun (measured)")
    A("")
    A("| driver_slots | entity graphs |")
    A("|---|---:|")
    for k, v in fl["slot_histogram"].items():
        A("| %s | %d |" % (k, v))
    A("")
    A("%d of %d graphs bind at least one driver weapon.  All %d graphs that carry both"
      % (fl["driver_entities"], fl["entities"], len(fl["two_slot"])))
    A("driver properties (%d with both bound, %d with the properties present but empty):"
      % (sum(1 for t in fl["two_slot"] if any(v[0] for v in t["slots"].values())),
         sum(1 for t in fl["two_slot"] if not any(v[0] for v in t["slots"].values()))))
    A("")
    A("| entity | slot 1 | slot 2 |")
    A("|---|---|---|")
    for t in fl["two_slot"]:
        s = t["slots"]
        a = s.get("main_weapon", (None, ""))[0]
        b = s.get("secondary (id:00568A74)", (None, ""))[0]
        A("| `%s` | %s | %s |"
          % (t["entity"].split("/")[-1], "`%s`" % a if a else "-",
             "`%s`" % b if b else "-"))
    A("")
    A("Root slot properties seen fleet-wide: %s."
      % ", ".join("`%s` x%d" % (k, v) for k, v in fl["slot_names"].items()))
    A("")
    A("## 3. How a driver slot picks its weapon")
    A("")
    A("`DrivingMode` (G3-02, `DRIVINGMODE.md`) binds one state body per quick-gadget button:")
    A("")
    A("| state | call |")
    A("|---|---|")
    for s in ("QuickGadgetB", "QuickGadgetX", "QuickGadgetY"):
        A("| `%s` | `SelectVehicleWeapon(%d)` |" % (s, {"QuickGadgetB": 1, "QuickGadgetX": 2,
                                                      "QuickGadgetY": 3}[s]))
    A("")
    A("The integer is the only selector in the decoded state machine; the literals are")
    A("decoded, but **which weapon object an index resolves to is UNKNOWN** (the same gap")
    A("`DRIVINGMODE.md` §4 records).  Firing is separate and has exactly two actions:")
    A("`FIRE_VEHICLE_WEAPON_PRIMARY` (gamepad RSHOULDER, keyboard MOUSE1) and")
    A("`FIRE_VEHICLE_WEAPON_SECONDARY` (LSHOULDER, MOUSE2).")
    A("")
    A("## 4. Next / previous weapon actions in `keymap_*.bin`")
    A("")
    A("| action | gamepad | keyboard | scope |")
    A("|---|---|---|---|")
    for a in ac["next_prev"]:
        A("| `%s` | %s | %s | %s |" % (a["action"], a["gamepad"], a["keyboard"], a["scope"]))
    A("")
    A("All weapon-named actions in the shipped keymaps: %s."
      % ", ".join("`%s` (%s)" % (a["action"], a["scope"]) for a in ac["select"]))
    A("No action with `land-vehicle` scope matches select/next/previous weapon: **%d**."
      % len(ac["vehicle_select"]))
    A("")
    A("## 5. The 11-weapon mapping")
    A("")
    A("| BmAK weapon | JC3 slot | label | why |")
    A("|---|---|---|---|")
    for wid, name, slot, label, bound, why in d["proposal"]:
        A("| %s %s | %s | **%s**%s | %s |"
          % (wid, name, slot, label, "" if bound else " (no slot)", why))
    A("")
    A("## 6. What is lost")
    A("")
    A("- **%d of %d weapons.** Only the cannon and the Vulcan have a decoded driver slot;"
      % (cap["lost"], len(d["proposal"])))
    A("  the missiles are addressable only through the third `SelectVehicleWeapon` index,")
    A("  whose member no fleet vehicle has, and the other seven have no carrier at all")
    A("  (EMP burst = entity pulse, winch / hacker / sonar / tracker / riot = proven absence,")
    A("  booster = a button, not a slot).")
    A("- **The per-mode split.** BmAK wants every weapon in battle and pursuit mode; JC3 has")
    A("  one vehicle mode and no decoded mode-to-slot table, so 'both modes' cannot be")
    A("  expressed even for the two weapons that fit.")
    A("- **Switching by input.** `NEXT_WEAPON`/`PREV_WEAPON` exist only in the on-foot scope,")
    A("  so a driver cannot cycle slots; the only in-vehicle selection is the three")
    A("  quick-gadget indices, two of which are bound.")
    A("- **The HUD's 5 BmAK slots** (primary + secondary + 3 special states) against JC3's 2")
    A("  clips (`MCI_vehicle_weapons0/1`).")
    A("")
    A("## 7. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**",
                                  str(o["evidence"]).replace("|", "\\|")))
    A("")
    A("## 8. UNKNOWN")
    A("")
    A("- **What the third `SelectVehicleWeapon` index selects.** The literal 3 is decoded;")
    A("  the object behind it is not in the state body, and no fleet root carries a third")
    A("  driver property.  Where: the native `RPlayerController.SelectVehicleWeapon` body,")
    A("  which is not in the decoded packages.")
    A("- **Whether a vehicle consumes `NEXT_WEAPON`/`PREV_WEAPON`.** Both exist on the")
    A("  keyboard with on-foot scope; no file maps them to a vehicle state.")
    A("- **A per-mode slot table.** No file splits weapons by battle/pursuit mode.")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/t_wp13.py --write")
    A("uv run python Tools/scripts/t_wp13.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: t_wp13.py --write|--check")
    d = build()
    fails = [o["key"] for o in d["oracles"] if not o["ok"]]
    md = d["md"]
    if argv[1] == "--write":
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        json.dump({k: v for k, v in d.items() if k != "md"},
                  open(JS, "w", encoding="utf-8", newline="\n"), indent=1)
        print("wrote Working/Translation/T_WP13_PROPOSAL.md (%d lines) and .json"
              % md.count("\n"))
        print("fleet %d graphs, max driver slots %d, %d with a driver weapon"
              % (d["fleet"]["entities"], d["fleet"]["max_driver_slots"],
                 d["fleet"]["driver_entities"]))
        print("select indices %s, next/prev %s"
              % (d["drivemode"]["select_args"],
                 [a["action"] for a in d["actions"]["next_prev"]]))
        print("placed %d of %d, lost %d" % (d["capacity"]["placed"],
                                            len(d["proposal"]), d["capacity"]["lost"]))
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
            print("FAIL: T_WP13_PROPOSAL.md is stale")
            return 1
        print("CHECK OK: %d oracles, max %d bound slots, %d indices, %d/%d placed"
              % (len(d["oracles"]), d["capacity"]["bound_slots"],
                 d["capacity"]["select_indices"], d["capacity"]["placed"],
                 len(d["proposal"])))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
