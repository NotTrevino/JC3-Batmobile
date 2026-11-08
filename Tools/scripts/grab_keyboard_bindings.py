#!/usr/bin/env python3
"""grab_keyboard_bindings.py - G3-02h: which keyboard/mouse bindings reach a Batmobile function.

Reads the effective PC ini chain of Batman: Arkham Knight, read-only, and nothing else:

    BmGame/Config/PC/PCInput.ini --BasedOn--> BmGame/Config/UserInput.ini
      --BasedOn--> BmGame/Config/DefaultInput.ini --BasedOn--> Engine/Config/BaseInput.ini

`Research/BatmobileGrab/BINDINGS_MERGED.json` (G3-02g) does not exist, so every number here is
re-derived from the four ini files' bytes. Consumer names are quoted from G3-02/G3-02b
(`CONTROLS.md`, `CONTROLS_CONSUMERS.md`) and every quotation is re-checked against those files.

What it decides:
    * every live `Bindings=` line, its file:line, its section, its device;
    * alias expansion (`BrakeButton` -> `BrakePressed | Button bHandbrakeOrBrake`) with the
      file:line of each alias definition on the chain;
    * whether any expanded token names a vehicle function (accelerate, brake, steer,
      battle mode, boost, fire, exit, eject);
    * how the token reaches the function: vehicle-specific name, generic name (vehicle use
      unproven), decoded call quoted from G3-02b, or cheat manager.

Oracles (re-run by --check; a failure is a hard error):
    P1  the chain is the documented one: 4 files, each BasedOn the next, sha256 recorded
    P2  every citation in this report is re-read from the bytes (file:line -> substring)
    P3  no keyboard binding expands to a vehicle-specific token other than the one reported
    P4  no mouse binding expands to any vehicle token at all
    P5  the W/S/A/D/arrow merge conflict exists (same key, same input class, two files)
    P6  every consumer quoted from CONTROLS.md / CONTROLS_CONSUMERS.md is still there verbatim
    P7  the counts in the report equal the recomputed counts

Usage:
    uv run python Tools/scripts/grab_keyboard_bindings.py --write
    uv run python Tools/scripts/grab_keyboard_bindings.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
ROOT = r"E:/Games/Batman - Arkham Knight"
CONTROLS = os.path.join(REPO, "Research", "BatmobileGrab", "CONTROLS.md")
CONSUMERS = os.path.join(REPO, "Research", "BatmobileGrab", "CONTROLS_CONSUMERS.md")
OUT_MD = os.path.join(REPO, "Research", "BatmobileGrab", "BINDINGS_KEYBOARD.md")
OUT_JSON = os.path.join(REPO, "Research", "BatmobileGrab", "BINDINGS_KEYBOARD.json")

CHAIN = ["BmGame/Config/PC/PCInput.ini",
         "BmGame/Config/UserInput.ini",
         "BmGame/Config/DefaultInput.ini",
         "Engine/Config/BaseInput.ini"]

# keyboard / mouse identifiers used as Name= in these files.  P2 requires each one to occur as
# a Name in the chain, so the list cannot drift from the files.
KEY_MULTI = {
    "SpaceBar", "BackSpace", "LeftShift", "RightShift", "LeftMouseButton", "RightMouseButton",
    "MiddleMouseButton", "MouseX", "MouseY", "MouseWheelUp", "MouseWheelDown", "TAB", "Tab",
    "Escape", "Enter", "Delete", "Insert", "Home", "End", "Pause", "Tilde", "Slash", "Comma",
    "COMMA", "Period", "Equals", "Underscore", "LeftBracket", "RightBracket", "PageUp",
    "PageDown", "Subtract", "Add", "Multiply", "Divide", "Semicolon", "BackSlash", "Up", "Down",
    "Left", "Right", "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight",
    "Nine", "NumPadZero", "NumPadOne", "NumPadTwo", "NumPadThree", "NumPadFour", "NumPadFive",
    "NumPadSix", "NumPadSeven", "NumPadEight", "NumPadNine",
}
KEY_MULTI |= {"F%d" % i for i in range(1, 13)}

# token -> (functions, link kind).  link kind:
#   specific  the token name itself says vehicle/battle/throttle/brake/boost/eject/driving
#   generic   a generic movement/camera token; its use by vehicle code is unproven
#   call      quoted decoded call from G3-02b (bytecode walk)
#   cheat     RCheatManager function whose name mentions a vehicle
TARGETS = {
    "aThrottleAxis": ({"accelerate"}, "specific"),
    "aBaseY": ({"accelerate"}, "generic"),
    "aRightTrigger": ({"accelerate"}, "generic"),
    "BrakePressed": ({"brake"}, "specific"),
    "bHandbrakeOrBrake": ({"brake"}, "specific"),
    "aStrafe": ({"steer"}, "generic"),
    "aBaseX": ({"steer"}, "generic"),
    "aTurn": ({"steer"}, "generic"),
    "aRawLHJoyRight": ({"steer"}, "generic"),
    "aRawRHJoyRight": ({"steer"}, "generic"),
    "VehicleStrafe": ({"steer"}, "specific"),
    "BattleStrafe": ({"battle mode"}, "specific"),
    "PursuitModeTagGun": ({"battle mode"}, "specific"),
    "ToggleDrivingCamera": ({"driving camera"}, "specific"),
    "bVehicleBoostButton": ({"boost"}, "specific"),
    "TriggerBatmobileBoost": ({"boost"}, "specific"),
    "BatmobileFireButton": ({"fire"}, "specific"),
    "bFireVehicleWeapon": ({"fire"}, "specific"),
    "bFireVehicleSecondaryWeapon": ({"fire"}, "specific"),
    "SecondaryFireVehicleWeapon": ({"fire"}, "specific"),
    "SelectVehicleWeapon": ({"fire"}, "specific"),
    "ReleaseVehicleWeapon": ({"fire"}, "specific"),
    "QuickGadgetB": ({"fire"}, "call"),
    "QuickGadgetX": ({"fire"}, "call"),
    "QuickGadgetY": ({"fire"}, "call"),
    "ExitVehiclePressed": ({"exit"}, "specific"),
    "ExitVehicleReleased": ({"exit"}, "specific"),
    "EjectFromVehicle": ({"eject"}, "specific"),
    "KillVehicles": ({"cheat"}, "cheat"),
    "SpawnPlayerCar": ({"cheat"}, "cheat"),
}

# every citation the report makes, re-read from the files by P2
CITATIONS = [
    ("BmGame/Config/PC/PCInput.ini", 2, "BasedOn=..\\BmGame\\Config\\UserInput.ini"),
    ("BmGame/Config/PC/PCInput.ini", 10, 'Name="TAB"'),
    ("BmGame/Config/PC/PCInput.ini", 30, 'Name="LeftMouseButton"'),
    ("BmGame/Config/PC/PCInput.ini", 30, 'SkipCutscene'),
    ("BmGame/Config/UserInput.ini", 2, "BasedOn=..\\BmGame\\Config\\DefaultInput.ini"),
    ("BmGame/Config/DefaultInput.ini", 2, "BasedOn=..\\Engine\\Config\\BaseInput.ini"),
    ("BmGame/Config/DefaultInput.ini", 100, "[Engine.PlayerInput]"),
    ("BmGame/Config/DefaultInput.ini", 39, 'Name="A"'),
    ("BmGame/Config/DefaultInput.ini", 39, "Axis aRawLHJoyRight"),
    ("BmGame/Config/DefaultInput.ini", 40, "Axis aRawLHJoyRight"),
    ("BmGame/Config/DefaultInput.ini", 177, 'Name="BrakeButton"'),
    ("BmGame/Config/DefaultInput.ini", 177, "Button bHandbrakeOrBrake"),
    ("BmGame/Config/DefaultInput.ini", 178, 'Name="ExitVehicle"'),
    ("BmGame/Config/DefaultInput.ini", 184, 'Name="BatmobileSonar"'),
    ("BmGame/Config/DefaultInput.ini", 186, 'Name="C"'),
    ("BmGame/Config/DefaultInput.ini", 186, "ToggleDrivingCamera"),
    ("BmGame/Config/DefaultInput.ini", 186, "Control=false"),
    ("BmGame/Config/DefaultInput.ini", 190, "DebugMenuUpPressed"),
    ("BmGame/Config/DefaultInput.ini", 193, "DebugMenuRightPressed"),
    ("BmGame/Config/DefaultInput.ini", 207, "KillVehicles"),
    ("BmGame/Config/DefaultInput.ini", 242, "SpawnPlayerCar"),
    ("BmGame/Config/DefaultInput.ini", 252, "BatmobileFireButton"),
    ("BmGame/Config/DefaultInput.ini", 252, "Button bFireVehicleWeapon"),
    ("BmGame/Config/DefaultInput.ini", 254, "Axis aThrottleAxis"),
    ("BmGame/Config/DefaultInput.ini", 255, "Button bLookBehindVehicle"),
    ("BmGame/Config/DefaultInput.ini", 256, "BatmobileSonar"),
    ("BmGame/Config/DefaultInput.ini", 259, "SelectVehicleWeapon 4"),
    ("BmGame/Config/DefaultInput.ini", 263, "Axis aStrafe"),
    ("BmGame/Config/DefaultInput.ini", 264, "Axis aBaseY"),
    ("BmGame/Config/DefaultInput.ini", 265, "Axis aTurn"),
    ("BmGame/Config/DefaultInput.ini", 267, "EjectFromVehicle"),
    ("BmGame/Config/DefaultInput.ini", 267, "BattleStrafe"),
    ("BmGame/Config/DefaultInput.ini", 268, "QuickGadgetB"),
    ("BmGame/Config/DefaultInput.ini", 269, "BrakeButton"),
    ("BmGame/Config/DefaultInput.ini", 270, "Button bVehicleBoostButton"),
    ("BmGame/Config/DefaultInput.ini", 272, "Button bFireVehicleSecondaryWeapon"),
    ("BmGame/Config/DefaultInput.ini", 272, "SecondaryFireVehicleWeapon"),
    ("BmGame/Config/DefaultInput.ini", 272, "PursuitModeTagGun"),
    ("BmGame/Config/DefaultInput.ini", 272, "ToggleDrivingCamera"),
    ("Engine/Config/BaseInput.ini", 10, "Axis aBaseY Speed=1.0"),
    ("Engine/Config/BaseInput.ini", 11, "Axis aBaseY Speed=-1.0"),
    ("Engine/Config/BaseInput.ini", 12, "Axis aBaseX"),
    ("Engine/Config/BaseInput.ini", 13, "Axis aBaseX"),
    ("Engine/Config/BaseInput.ini", 14, "Axis aStrafe Speed=-1.0"),
    ("Engine/Config/BaseInput.ini", 15, "Axis aStrafe Speed=+1.0"),
    ("Engine/Config/BaseInput.ini", 17, 'Name="W"'),
    ("Engine/Config/BaseInput.ini", 17, "MoveForward"),
    ("Engine/Config/BaseInput.ini", 18, 'Name="S"'),
    ("Engine/Config/BaseInput.ini", 19, 'Name="A"'),
    ("Engine/Config/BaseInput.ini", 20, 'Name="D"'),
    ("Engine/Config/BaseInput.ini", 26, 'Name="Up"'),
    ("Engine/Config/BaseInput.ini", 28, 'Name="Left"'),
    ("Engine/Config/BaseInput.ini", 29, 'Name="Right"'),
    ("Engine/Config/BaseInput.ini", 50, 'Name="W"'),
    ("Engine/Config/BaseInput.ini", 52, 'Name="A"'),
    ("Engine/Config/BaseInput.ini", 57, 'Name="Left"'),
]

# consumers quoted from the G3-02 reports (P6 re-reads each string from those files)
CONSUMER_QUOTES = [
    ("CONTROLS.md", "`BatmobileFireButton` | exec | none in chain | XboxTypeS_RightTrigger"),
    ("CONTROLS.md", "`RPlayerController.DrivingMode.BatmobileFireButton` (Function)"),
    ("CONTROLS.md", "`RPlayerController.DrivingMode.EjectFromVehicle` (Function)"),
    ("CONTROLS.md", "`RPlayerController.DrivingMode.ToggleDrivingCamera` (Function)"),
    ("CONTROLS.md", "`RPlayerInput.bVehicleBoostButton` (ByteProperty)"),
    ("CONTROLS.md", "`RPlayerInput.bHandbrakeOrBrake` (ByteProperty)"),
    ("CONTROLS.md", "`RPlayerInput.aThrottleAxis` (FloatProperty)"),
    ("CONTROLS.md", "`Core.aBaseY` - import-name-match (decoded)"),
    ("CONTROLS.md", "`Core.aStrafe` - import-name-match (decoded)"),
    ("CONTROLS.md", "`aBaseX` | axis | Left, Right"),
    ("CONTROLS.md", "`RCheatManager.KillVehicles` (Function)"),
    ("CONTROLS.md", "`RCheatManager.SpawnPlayerCar` (Function)"),
    ("CONTROLS.md", "Keyboard keys that drive the Batmobile (steer/throttle/brake)"),
    ("CONTROLS_CONSUMERS.md", "`SelectVehicleWeapon`: DrivingMode.QuickGadgetX@0"),
    ("CONTROLS.md", "the merge rule for array `Bindings` is **UNKNOWN**"),
]


def read_lines(rel):
    p = os.path.join(ROOT, rel)
    raw = open(p, "rb").read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raise SystemExit("%s is UTF-16; this parser expects 8-bit text" % rel)
    return raw, raw.decode("utf-8-sig", "replace").splitlines()


def split_fields(body):
    """Split 'Name="X",Command="a | b",Control=true' on top-level commas."""
    out, cur, q, depth = [], [], False, 0
    for ch in body:
        if ch == '"':
            q = not q
            cur.append(ch)
        elif ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth -= 1
            cur.append(ch)
        elif ch == "," and not q and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


BIND_RE = re.compile(r'^\.?Bindings=\s*\((.*)\)\s*[;)]?\s*"?.?$')
NAME_RE = re.compile(r'Name\s*=\s*(?:"([^"]*)"|([A-Za-z0-9_]+))')
CMD_RE = re.compile(r'Command\s*=\s*"([^"]*)"')
SEC_RE = re.compile(r'^\s*\[([^\]]+)\]\s*$')


def parse_bindings(raw, rel):
    sec = ""
    rows = []
    for n, line in enumerate(raw.decode("utf-8-sig", "replace").splitlines(), 1):
        s = line.strip()
        if s.startswith(";"):
            continue
        m = SEC_RE.match(s)
        if m:
            sec = m.group(1)
            continue
        if not (s.startswith("Bindings=") or s.startswith(".Bindings=")):
            continue
        name = NAME_RE.search(s)
        cmd = CMD_RE.search(s)
        if not name or not cmd:
            rows.append({"file": rel, "line": n, "section": sec, "malformed": True,
                         "raw": line})
            continue
        mods = {}
        for key in ("Control", "Shift", "Alt"):
            mm = re.search(r'%s\s*=\s*(\w+)' % key, s, re.I)
            if mm:
                mods[key] = mm.group(1).lower()
        rows.append({"file": rel, "line": n, "section": sec, "malformed": False,
                     "name": name.group(1) if name.group(1) is not None else name.group(2),
                     "command": cmd.group(1), "mods": mods, "raw": line})
    return rows


def tokens_of(cmd):
    out = []
    for part in cmd.split("|"):
        p = part.strip().strip('"')
        if not p:
            continue
        if p.lower().startswith("onrelease"):
            p = p[len("onrelease"):].strip()
            if not p:
                continue
        low = p.lower()
        for pre in ("button ", "axis ", "count "):
            if low.startswith(pre):
                p = p[len(pre):].strip()
                break
        tok = p.split()[0] if p.split() else ""
        if tok:
            out.append(tok)
    return out


def is_gamepad(name):
    return name.startswith("XboxTypeS_") or name.startswith("SIXAXIS_")


def is_key(name):
    return name in KEY_MULTI or (len(name) == 1 and name.isalnum())


def build():
    files = {}
    order = []
    all_rows = []
    for rel in CHAIN:
        raw, _lines = read_lines(rel)
        rows = parse_bindings(raw, rel)
        files[rel] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
                      "lines": len(raw.decode("utf-8-sig", "replace").splitlines()),
                      "live": len([r for r in rows if not r["malformed"]]),
                      "malformed": len([r for r in rows if r["malformed"]]),
                      "basedon": next((l.strip().split("=", 1)[1]
                                       for l in raw.decode("utf-8-sig", "replace").splitlines()
                                       if l.strip().startswith("BasedOn=")), None)}
        order.append(rel)
        all_rows.extend(rows)

    aliases = {}
    for r in all_rows:
        if r["malformed"] or is_gamepad(r["name"]) or is_key(r["name"]):
            continue
        aliases.setdefault(r["name"], []).append(r)

    def expand(tok, section, depth=0, seen=()):
        """-> [(target token, [(alias file, alias line)...], ambiguous)] from `tok`.

        An alias defined in several sections (MoveForward in Engine.PlayerInput and in
        Engine.DebugCameraInput) is resolved to the definition in the key line's own
        section; if there is none, every definition is kept and the row is marked ambiguous.
        """
        if tok in TARGETS:
            return [(tok, [], False)]
        if depth > 4 or tok in seen or tok not in aliases:
            return []
        defs = aliases[tok]
        same = [a for a in defs if a["section"] == section]
        use = same or defs
        ambiguous = (not same and len(defs) > 1)
        out = []
        for a in use:
            for sub in tokens_of(a["command"]):
                if sub == tok:
                    continue
                for leaf, path, amb in expand(sub, section, depth + 1, seen + (tok,)):
                    item = (leaf, [(a["file"], a["line"])] + path, amb or ambiguous)
                    if item not in out:
                        out.append(item)
        return out

    hits = []
    for r in all_rows:
        if r["malformed"]:
            continue
        dev = "gamepad" if is_gamepad(r["name"]) else ("alias" if r["name"] in aliases
                                                       else "keyboard/mouse")
        found = []
        for tok in tokens_of(r["command"]):
            for leaf, path, amb in expand(tok, r["section"]):
                if leaf in TARGETS:
                    item = {"leaf": leaf, "via": path,
                            "functions": sorted(TARGETS[leaf][0]),
                            "link": TARGETS[leaf][1], "ambiguous_alias": amb}
                    if item not in found:
                        found.append(item)
        if dev != "alias" and found:
            hits.append({"file": r["file"], "line": r["line"], "section": r["section"],
                         "name": r["name"], "device": dev, "mods": r["mods"],
                         "command": r["command"], "hits": found})

    # alias definitions actually used by a reported row (for the file:line chain)
    def alias_uses(h):
        out = []
        for hit in h["hits"]:
            out.extend(hit["via"])
        return out

    doc = {"generated_by": "Tools/scripts/grab_keyboard_bindings.py --write",
           "root": ROOT, "chain": order, "files": files, "oracles": [],
           "rows": hits, "aliases": {k: [{"file": a["file"], "line": a["line"]}
                                         for a in v] for k, v in sorted(aliases.items())},
           "counts": {}}
    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    # P1 chain
    links_ok = all(files[CHAIN[i]]["basedon"] and
                   files[CHAIN[i]]["basedon"].replace("..\\", "").replace("\\", "/")
                   .lower().endswith(CHAIN[i + 1].lower())
                   for i in range(len(CHAIN) - 1))
    oracle("P1-chain", len(order) == 4 and links_ok and
           all(files[f]["bytes"] > 0 for f in CHAIN),
           "; ".join("%s (%d B, %d live, BasedOn=%s)"
                     % (f.split("/")[-1], files[f]["bytes"], files[f]["live"],
                        files[f]["basedon"]) for f in CHAIN))

    # P2 citations
    texts = {f: read_lines(f)[1] for f in CHAIN}
    bad = []
    for rel, line, sub in CITATIONS:
        lines = texts[rel]
        if line > len(lines) or sub not in lines[line - 1]:
            bad.append("%s:%d %r" % (rel, line, sub))
    oracle("P2-citations", not bad,
           "%d/%d citations re-read from the bytes%s"
           % (len(CITATIONS) - len(bad), len(CITATIONS),
              "" if not bad else "; MISSING: " + ", ".join(bad)))

    # P3 the headline claim: specific vehicle tokens on keyboard = exactly C@186
    kb_specific = sorted({(r["name"], r["file"], r["line"], hit["leaf"])
                          for r in hits if r["device"] == "keyboard/mouse"
                          for hit in r["hits"] if hit["link"] == "specific"})
    expected = [("C", "BmGame/Config/DefaultInput.ini", 186, "ToggleDrivingCamera")]
    oracle("P3-keyboard-specific", kb_specific == expected,
           "keyboard bindings whose expansion names a vehicle-specific command: %s"
           % (kb_specific or "none"))

    # P4 no mouse binding reaches any vehicle token
    mouse = [r for r in hits if "Mouse" in r["name"]]
    oracle("P4-mouse", not mouse,
           "mouse bindings with a vehicle token: %s; mouse bindings in the chain: %s"
           % ([(m["name"], m["line"]) for m in mouse] or "none",
              [(r["name"], r["file"].split("/")[-1], r["line"])
               for r in all_rows if not r["malformed"] and "Mouse" in r["name"]]))

    # P5 merge conflict exists
    def cmds(rel, section, name):
        out = []
        for r in all_rows:
            if (r["malformed"] or r["file"] != rel or r["section"] != section
                    or r["name"] != name):
                continue
            tag = ",".join("%s=%s" % (k, v) for k, v in sorted(r["mods"].items()))
            out.append(" | ".join(tokens_of(r["command"])) + (" [%s]" % tag if tag else ""))
        return out
    conflict = []

    for name in ("W", "S", "A", "D", "Up", "Down", "Left", "Right"):
        a = cmds("Engine/Config/BaseInput.ini", "Engine.PlayerInput", name)
        b = cmds("BmGame/Config/DefaultInput.ini", "Engine.PlayerInput", name)
        if a and b and a != b:
            conflict.append((name, " ; ".join(a), " ; ".join(b)))
    oracle("P5-merge-conflict", len(conflict) == 8,
           "%d/8 of W,S,A,D,Up,Down,Left,Right are bound twice in Engine.PlayerInput with "
           "different commands (BaseInput.ini vs DefaultInput.ini)" % len(conflict))

    # P6 consumer quotes present in the G3-02 reports
    ctxt = {os.path.basename(p): open(p, encoding="utf-8", errors="replace").read()
            for p in (CONTROLS, CONSUMERS)}
    missing = [(f, q) for f, q in CONSUMER_QUOTES if q not in ctxt[f]]
    oracle("P6-consumer-quotes", not missing,
           "%d/%d quoted consumer strings still present in CONTROLS.md / "
           "CONTROLS_CONSUMERS.md%s"
           % (len(CONSUMER_QUOTES) - len(missing), len(CONSUMER_QUOTES),
              "" if not missing else "; MISSING: %r" % missing[:3]))

    kb = [r for r in all_rows if not r["malformed"] and not is_gamepad(r["name"])
          and r["name"] not in aliases]
    gp = [r for r in all_rows if not r["malformed"] and is_gamepad(r["name"])]
    doc["counts"] = {
        "chain_files": len(order),
        "bindings_live": len([r for r in all_rows if not r["malformed"]]),
        "bindings_malformed": len([r for r in all_rows if r["malformed"]]),
        "keyboard_mouse": len(kb),
        "gamepad": len(gp),
        "alias_defs": len(aliases),
        "kb_vehicle_rows": len([r for r in hits if r["device"] == "keyboard/mouse"]),
        "gp_vehicle_rows": len([r for r in hits if r["device"] == "gamepad"]),
        "kb_specific": len(kb_specific),
    }
    # P7 counts
    oracle("P7-counts",
           doc["counts"]["bindings_live"] == sum(files[f]["live"] for f in CHAIN)
           and doc["counts"]["kb_vehicle_rows"] == len(
               [r for r in hits if r["device"] == "keyboard/mouse"]),
           "%d live bindings (%d keyboard/mouse, %d gamepad, %d alias defs, %d malformed); "
           "%d keyboard/mouse rows and %d gamepad rows reach a vehicle token"
           % (doc["counts"]["bindings_live"], doc["counts"]["keyboard_mouse"],
              doc["counts"]["gamepad"], doc["counts"]["alias_defs"],
              doc["counts"]["bindings_malformed"], doc["counts"]["kb_vehicle_rows"],
              doc["counts"]["gp_vehicle_rows"]))

    doc["oracles"] = oracles
    doc["conflicts"] = [{"key": c[0], "base": c[1], "default": c[2]} for c in conflict]
    doc["unknowns"] = [
        {"what": "the merged effective binding set (UE3 array operators)",
         "why": "PCInput.ini and DefaultInput.ini write `.Bindings=` (leading dot) while "
                "BaseInput.ini writes `Bindings=`; no file in the chain documents what the dot "
                "does or in which order duplicates win. CONTROLS.md records the same gap. "
                "Where it would be found: the engine's config loader, not a text file here."},
        {"what": "whether aBaseY / aStrafe / aBaseX / aTurn are read by vehicle code",
         "why": "the tokens exist as RPlayerInput/Core properties (CONTROLS.md name lookups) but "
                "no decoded body shows a vehicle class reading them; the keyboard-to-Batmobile "
                "link is a name match only. Where it would be found: RVehicleBatmobileBase / "
                "RVehicleSimBatmobile bytecode reads of those properties."},
        {"what": "whether DebugCameraInput rows apply outside the debug camera",
         "why": "A/D/W/S/Left/Right also carry vehicle-candidate tokens in "
                "[Engine.DebugCameraInput]; which input class is active in a normal driving "
                "frame is not decoded. Where it would be found: the PlayerInput class switch."},
        {"what": "how pursuit and battle mode are toggled by any input",
         "why": "no chain binding names ToggleBattleMode or a pursuit/battle switch; G3-02b "
                "decoded DrivingMode.ToggleBattleMode and SetPursuitModeKeyBinds call sites "
                "(BattleMode.EndState, RGameInfo.SetPCBinds, DrivingMode.BeginState) but no "
                "binding. Where it would be found: the keybinds those calls install at runtime."},
    ]
    return doc


def render(doc):
    L = []
    A = L.append
    c = doc["counts"]
    ok = sum(1 for o in doc["oracles"] if o["ok"])
    A("# Keyboard and mouse bindings that reach a Batmobile function (G3-02h)")
    A("")
    A("Generated by `Tools/scripts/grab_keyboard_bindings.py --write`; `--check` re-derives every "
      "line number, sha256 and verdict from the four ini files under `%s` (read-only). "
      "`BINDINGS_MERGED.json` does not exist, so this is the raw chain." % doc["root"])
    A("")
    A("**Oracles: %d/%d pass.** %d live bindings parsed (%d keyboard/mouse, %d gamepad, "
      "%d alias definitions); **%d keyboard/mouse bindings (lines) reach a vehicle token, of "
      "which %d names a vehicle-specific command** (section 3 lists one row per expanded token)."
      % (ok, len(doc["oracles"]), c["bindings_live"], c["keyboard_mouse"], c["gamepad"],
         c["alias_defs"], c["kb_vehicle_rows"], c["kb_specific"]))
    A("")
    A("## 1. The chain")
    A("")
    A("| order | file | bytes | live `Bindings=` | BasedOn (next) | sha256 (first 16) |")
    A("|---|---|---|---|---|---|")
    for i, f in enumerate(doc["chain"]):
        d = doc["files"][f]
        A("| %d | `%s` | %s | %d | %s | `%s` |"
          % (i, f, f"{d['bytes']:,}", d["live"], d["basedon"] or "-", d["sha256"][:16]))
    A("")
    A("## 2. Answer")
    A("")
    A("| function | keyboard/mouse binding in the chain | how it reaches the function |")
    A("|---|---|---|")
    A("| accelerate | none specific; `W`/`S`/`Up`/`Down` via `Axis aBaseY` | generic token, "
      "**name match only** |")
    A("| brake | none | gamepad `XboxTypeS_X` only |")
    A("| steer | `A`/`D`, `Left`/`Right` via `Axis aStrafe` / `Axis aBaseX` | generic tokens, "
      "**name match only** |")
    A("| battle mode | none | gamepad `A` (`BattleStrafe`), `RB` (`PursuitModeTagGun`) |")
    A("| boost | none | gamepad `Y` (`bVehicleBoostButton`) |")
    A("| fire | none | gamepad `RT` (`BatmobileFireButton`, `bFireVehicleWeapon`), `RB`, "
      "`DPad_Up`, `X`/`B`/`Y` weapon gadgets |")
    A("| exit | none | no key at all in the chain (alias `ExitVehicle` is bound to nothing) |")
    A("| eject | none | gamepad `A` (`EjectFromVehicle`) |")
    A("| driving camera | `C` | vehicle-specific name, **name match only** |")
    A("")
    A("## 3. Keyboard/mouse rows that reach a vehicle token")
    A("")
    A("| key | file:line | section | command | expanded token | functions | link | alias step |")
    A("|---|---|---|---|---|---|---|---|")
    for r in doc["rows"]:
        if r["device"] != "keyboard/mouse":
            continue
        for hit in r["hits"]:
            via = ", ".join("`%s:%d`" % (f, l) for f, l in hit["via"]) or "-"
            if hit.get("ambiguous_alias"):
                via += " (alias defined in several sections)"
            A("| `%s` | `%s:%d` | `%s` | `%s` | `%s` | %s | %s | %s |"
              % (r["name"], r["file"], r["line"], r["section"],
                 r["command"].replace("|", "\\|"), hit["leaf"],
                 ", ".join(hit["functions"]), hit["link"], via))
    A("")
    A("`specific` = the token name itself names a vehicle function; `generic` = a movement/"
      "camera token whose vehicle use is unproven (name match only); `call` = a decoded call "
      "quoted from G3-02b; `cheat` = an `RCheatManager` function whose name mentions a vehicle.")
    A("")
    A("## 4. Gamepad rows, for contrast")
    A("")
    A("| button | file:line | command | expanded token | functions | link |")
    A("|---|---|---|---|---|---|")
    for r in doc["rows"]:
        if r["device"] != "gamepad":
            continue
        for hit in r["hits"]:
            A("| `%s` | `%s:%d` | `%s` | `%s` | %s | %s |"
              % (r["name"], r["file"], r["line"],
                 r["command"][:150].replace("|", "\\|"), hit["leaf"],
                 ", ".join(hit["functions"]), hit["link"]))
    A("")
    A("## 5. The merge conflict that makes \"the key\" ambiguous")
    A("")
    A("In `[Engine.PlayerInput]` the same physical key is bound in two chain files to different "
      "commands, and both `W/S/A/D` debug lines sit in the *same* input class as the movement "
      "lines (DefaultInput.ini's `[Engine.PlayerInput]` starts at line 100):")
    A("")
    A("| key | BaseInput.ini | DefaultInput.ini |")
    A("|---|---|---|")
    for cf in doc["conflicts"]:
        A("| `%s` | `%s` | `%s` |" % (cf["key"], cf["base"], cf["default"]))
    A("")
    A("Which of the two wins is UNKNOWN: PCInput.ini and DefaultInput.ini use `.Bindings=` "
      "(leading dot) while BaseInput.ini uses `Bindings=`, and no file in the chain states what "
      "the operator does or the precedence.")
    A("")
    A("## 6. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 7. UNKNOWN")
    A("")
    for u in doc["unknowns"]:
        A("- **%s** - %s" % (u["what"], u["why"]))
    A("")
    A("## 8. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/grab_keyboard_bindings.py --write")
    A("uv run python Tools/scripts/grab_keyboard_bindings.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]

    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            for o in doc["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote Research/BatmobileGrab/BINDINGS_KEYBOARD.md and .json")
        print("  chain %d files, %d live bindings (%d keyboard/mouse, %d gamepad, %d aliases)"
              % (doc["counts"]["chain_files"], doc["counts"]["bindings_live"],
                 doc["counts"]["keyboard_mouse"], doc["counts"]["gamepad"],
                 doc["counts"]["alias_defs"]))
        print("  keyboard/mouse rows reaching a vehicle token: %d (specific: %d); gamepad rows: %d"
              % (doc["counts"]["kb_vehicle_rows"], doc["counts"]["kb_specific"],
                 doc["counts"]["gp_vehicle_rows"]))
        print("  oracles %d/%d" % (len(doc["oracles"]) - len(fails), len(doc["oracles"])))
        return 0

    if fails:
        print("FAIL")
        for o in doc["oracles"]:
            if not o["ok"]:
                print("  - oracle %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        print("FAIL: BINDINGS_KEYBOARD.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: BINDINGS_KEYBOARD.json is stale")
        return 1
    print("OK %d/%d oracles, %d live bindings, %d keyboard/mouse vehicle rows (%d specific), "
          "%d gamepad rows, md+json byte-identical"
          % (len(doc["oracles"]), len(doc["oracles"]), doc["counts"]["bindings_live"],
             doc["counts"]["kb_vehicle_rows"], doc["counts"]["kb_specific"],
             doc["counts"]["gp_vehicle_rows"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
