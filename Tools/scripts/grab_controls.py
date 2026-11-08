#!/usr/bin/env python3
"""G3-02: Batman: Arkham Knight Batmobile controls, read from the shipped files.

Read-only. Writes (with --write) or re-derives and compares (with --check):
  Research/BatmobileGrab/CONTROLS.md    human-readable table + UNKNOWN list
  Research/BatmobileGrab/CONTROLS.json  the same data

Sources (nothing is guessed; every row carries a label):
  decoded  read from a file (file + line) or from a package name/export table
  derived  computed from decoded facts; the rule is stated in the row
  UNKNOWN  not decodable here; the attempt and where it would be are recorded

Steps:
  1. PC ini chain: PCInput.ini -> BasedOn -> ... (every file in the chain is parsed).
  2. Every Bindings line in every chain file is parsed (operator, Name, Command, flags, line).
  3. Command tokens are split on '|' and classified (Button / Axis / Count / OnRelease / exec).
  4. Name-table lookup in BmGame.upk for every token and for Button variables.
  5. Export lookup: which export (function/state/property) carries that name, and its owning class.

Not done (recorded as UNKNOWN): UE3 array-merge semantics across the BasedOn chain, the
runtime meaning of OnRelease, the exec flag of functions, and bytecode of consumers.
Other config files in BmGame\\Config (BmInput.ini, BmGame.ini, BmEngine.ini) are read for
evidence and reported; BmInput.ini is not in the BasedOn chain of PCInput.ini.

Usage:
  python -I grab_controls.py --write
  python -I grab_controls.py --check
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import upk_read  # noqa: E402  (package reader from this folder)

GAME = Path("E:/Games/Batman - Arkham Knight")
CONFIG = GAME / "BmGame" / "Config"
START_INI = CONFIG / "PC" / "PCInput.ini"
UPK = GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"
OUT_DIR = Path("E:/Modding/JustCause3/JC3-Batmobile/Research/BatmobileGrab")
OUT_MD = OUT_DIR / "CONTROLS.md"
OUT_JSON = OUT_DIR / "CONTROLS.json"

SCHEMA = "g3-02-controls/1"

# Keyword rule for "vehicle keyword" (decoded name match, not a behaviour claim).
VEHICLE_RE = re.compile(
    r"(?i)vehicle|batmobile|driv|car$|boost|turret|sonar|eject|brake|throttle|winch|"
    r"tag ?gun|pursuit|abseil|lookbehind|linelaunch|handbrake"
)
# Generic axes / buttons that are also the on-foot movement or camera tokens. They are
# listed as "vehicle candidate": the chain does not say the Batmobile consumes them.
CANDIDATE_TOKENS = {
    "aBaseY", "aBaseX", "aStrafe", "aTurn", "aLookup", "aUp", "aRawLHJoyUp", "aRawLHJoyRight",
    "aRawRHJoyUp", "aRawRHJoyRight", "aLeftTrigger", "aRightTrigger", "aThrottleAxis",
    "bLeftStickDown", "bHandbrakeOrBrake",
}
MODE_RE = re.compile(r"(?i)pursuit|battlemode|battle|mode")

PHYS_KEY_RE = re.compile(
    r"^(?:[A-Za-z]|[0-9]|F(?:1[0-2]|[1-9])|NumPad[A-Za-z0-9]+|One|Two|Three|Four|Five|Six|"
    r"Seven|Eight|Nine|Zero|Escape|Tab|Enter|Pause|Add|Subtract|Multiply|Divide|Equals|"
    r"Underscore|COMMA|Period|Semicolon|Slash|SLASH|BackSlash|Tilde|LeftShift|RightShift|"
    r"LeftControl|RightControl|LeftAlt|RightAlt|BackSpace|Delete|SpaceBar|Up|Down|Left|Right|"
    r"PageUp|PageDown|Home|End|LeftBracket|RightBracket|LeftMouseButton|RightMouseButton|"
    r"MouseX|MouseY|MouseScrollUp|MouseScrollDown|MiddleMouseButton)$"
)
GAMEPAD_RE = re.compile(r"^(?:XboxTypeS_|SIXAXIS_|Gamepad_)")

SECTION_RE = re.compile(r"^\s*\[(.+?)\]\s*$")
KV_RE = re.compile(r"^\s*([.+\-!]?)([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
BASEDON_RE = re.compile(r"^\s*BasedOn\s*=\s*(.+?)\s*$")
NAME_Q_RE = re.compile(r'\bName\s*=\s*"([^"]*)"')
NAME_U_RE = re.compile(r"\bName\s*=\s*([A-Za-z0-9_]+)")
CMD_Q_RE = re.compile(r'\bCommand\s*=\s*"([^"]*)"')
FLAG_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(True|False|true|false)\b")


def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rel(p):
    """Path shown in outputs: relative to the game folder when inside it, else as given."""
    p = Path(p)
    try:
        return p.relative_to(GAME).as_posix()
    except ValueError:
        return p.as_posix()


# ---------------------------------------------------------------- ini chain

def read_ini_lines(path):
    raw = Path(path).read_bytes().decode("latin-1")
    return raw.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def ini_chain(start):
    """Follow BasedOn= from the start file. Returns list of (path, based_on_text or None)."""
    chain = []
    seen = set()
    cur = Path(start)
    while cur is not None:
        key = str(cur).lower()
        if key in seen:
            chain.append((cur, "CYCLE-STOP"))
            break
        seen.add(key)
        if not cur.exists():
            chain.append((cur, "MISSING"))
            break
        based = None
        section = None
        for line in read_ini_lines(cur):
            m = SECTION_RE.match(line)
            if m:
                section = m.group(1)
                continue
            if section == "Configuration":
                b = BASEDON_RE.match(line)
                if b:
                    based = b.group(1)
                    break
        chain.append((cur, based))
        if based is None:
            break
        # Derived rule: every BasedOn path in this chain resolves only against BmGame\ (the
        # parent of Config), not against the directory of the file that names it (PCInput.ini
        # sits in Config\PC\). The UE3 rule itself is not stated in any file here.
        cur = (CONFIG.parent / based).resolve()
    return chain


def parse_binding_value(value):
    """Parse the value of a Bindings line. Returns dict with name, command, flags, problems."""
    problems = []
    name = None
    mq = NAME_Q_RE.search(value)
    if mq:
        name = mq.group(1)
    else:
        mu = NAME_U_RE.search(value)
        if mu:
            name = mu.group(1)
    command = None
    mc = CMD_Q_RE.search(value)
    if mc:
        command = mc.group(1)
    flags = {}
    for fm in FLAG_RE.finditer(value):
        k = fm.group(1)
        if k in ("Name", "Command"):
            continue
        flags[k] = fm.group(2).lower() == "true"
    if value.count('"') % 2:
        problems.append("unbalanced quotes")
    if value.count("(") != value.count(")"):
        problems.append("unbalanced parentheses")
    if value.rstrip().endswith(";"):
        problems.append("trailing ';' after value")
    if name is None:
        problems.append("no Name")
    if command is None:
        problems.append("no Command")
    return {"name": name, "command": command, "flags": flags, "problems": problems}


def parse_token(tok):
    t = tok.strip()
    if not t:
        return None
    if t.startswith("Button "):
        arg = t[len("Button "):].strip()
        return {"kind": "button", "name": arg.split()[0] if arg else "", "args": arg, "raw": t}
    if t.startswith("Count "):
        arg = t[len("Count "):].strip()
        return {"kind": "count", "name": arg.split()[0] if arg else "", "args": arg, "raw": t}
    if t.startswith("Axis "):
        arg = t[len("Axis "):].strip()
        parts = arg.split()
        return {"kind": "axis", "name": parts[0] if parts else "", "args": arg, "raw": t}
    if t.lower().startswith("onrelease "):
        arg = t[len("onrelease "):].strip()
        return {"kind": "onrelease", "name": arg.split()[0] if arg else "", "args": arg, "raw": t}
    parts = t.split()
    return {"kind": "exec", "name": parts[0], "args": " ".join(parts[1:]), "raw": t}


def tokens_of(command):
    if not command:
        return []
    out = []
    for piece in command.split("|"):
        pt = parse_token(piece)
        if pt is not None:
            out.append(pt)
    return out


def device_of(name):
    if name is None:
        return "none"
    if GAMEPAD_RE.match(name):
        return "gamepad"
    if PHYS_KEY_RE.match(name):
        return "keyboard/mouse"
    return "alias"


def parse_ini_chain_bindings(chain):
    rows = []
    for idx, (path, based) in enumerate(chain):
        if not path.exists():
            continue
        section = None
        occ = {}
        for lineno, line in enumerate(read_ini_lines(path), 1):
            m = SECTION_RE.match(line)
            if m:
                section = m.group(1)
                occ[section] = occ.get(section, 0) + 1
                continue
            if line.strip().startswith(";"):
                continue
            kv = KV_RE.match(line)
            if not kv:
                continue
            op, key, value = kv.group(1), kv.group(2), kv.group(3)
            if key != "Bindings":
                continue
            info = parse_binding_value(value)
            cmd_tokens = tokens_of(info["command"])
            rows.append({
                "file": rel(path),
                "chain_index": idx,
                "line": lineno,
                "section": section,
                "section_occurrence": occ.get(section, 1),
                "operator": op or "(plain)",
                "raw_value": value,
                "input_name": info["name"],
                "device": device_of(info["name"]),
                "command": info["command"],
                "tokens": cmd_tokens,
                "flags": info["flags"],
                "problems": info["problems"],
            })
    return rows


# ---------------------------------------------------------------- package lookup

def name_lookup(pkg, token):
    """Exact and case-insensitive name lookup in the BmGame name table, plus export owners."""
    low = token.lower()
    in_table = token in pkg.names
    ci_table = any(n.lower() == low for n in pkg.names)
    exports = []
    for i, e in enumerate(pkg.exports, 1):
        if e["name"].lower() == low:
            cls = pkg.class_name(e["class_index"])
            exports.append({
                "export_index": i,
                "name": e["name"],
                "class": cls,
                "outer_path": pkg.object_path(e["outer_index"]),
                "outer_class": pkg.object_class(e["outer_index"]),
            })
            if len(exports) >= 12:
                break
    imports = []
    for i, imp in enumerate(pkg.imports, 1):
        if imp["name"].lower() == low:
            imports.append({"import_index": -i, "name": imp["name"], "class": imp["class_name"],
                            "package": imp["class_package"]})
            if len(imports) >= 6:
                break
    return {"in_name_table": in_table, "case_insensitive_in_name_table": ci_table,
            "exports": exports, "imports": imports}


def census_vehicle_names(pkg):
    """Vehicle/mode-related names in the name table, with the export/class they appear on."""
    hits = []
    for i, e in enumerate(pkg.exports, 1):
        if e["name"] is None:
            continue
        if VEHICLE_RE.search(e["name"]) and pkg.class_name(e["class_index"]) == "Function":
            outer = pkg.object_path(e["outer_index"])
            hits.append({"export_index": i, "name": e["name"], "outer_path": outer})
    return hits


STATE_OUTER_RE = re.compile(r"^(RPlayerController|RPlayerControllerCombat|RVehicle\w*)$")
STATE_NAME_RE = re.compile(r"(?i)driv|pursu|battle|mode")


def state_census(pkg):
    """States (class 'State') declared directly on a player-controller or vehicle class, whose
    names carry a mode word. Decoded from the export table only."""
    out = []
    for i, e in enumerate(pkg.exports, 1):
        if pkg.class_name(e["class_index"]) != "State" or not e["name"]:
            continue
        outer = pkg.object_path(e["outer_index"]) or ""
        if STATE_OUTER_RE.match(outer) and STATE_NAME_RE.search(e["name"]):
            out.append({"export_index": i, "state": e["name"], "outer_class": outer})
    return out


def owners_of_functions(pkg, token_names):
    """For every export whose outer chain is a Batmobile/vehicle/player class, keep the
    functions whose names match a token. Decoded from export table only."""
    wanted = {t.lower() for t in token_names}
    out = []
    for i, e in enumerate(pkg.exports, 1):
        if e["name"].lower() in wanted:
            outer = pkg.object_path(e["outer_index"]) or ""
            cls = pkg.class_name(e["class_index"])
            out.append({"export_index": i, "name": e["name"], "class": cls, "outer_path": outer})
    return out


# ---------------------------------------------------------------- derive

def classify_hold(tokens):
    """Derived from token names only. The runtime meaning of OnRelease is UNKNOWN."""
    has_release = any(t["kind"] == "onrelease" for t in tokens)
    has_pressed = any(t["kind"] == "exec" and t["name"].endswith("Pressed") for t in tokens)
    if has_release and has_pressed:
        return "press/release pair (derived from 'XPressed' + 'OnRelease ...' tokens)"
    if has_release:
        return "OnRelease handler only (derived)"
    if has_pressed:
        return "press token, no OnRelease handler in this line (derived)"
    return "no press/release token in this line (derived)"


def hold_for(token, line_tokens):
    """Per-token, derived from token names only. OnRelease runtime meaning is UNKNOWN."""
    name = token["name"]
    if token["kind"] in ("button", "axis", "count"):
        return "%s token (derived): state/axis, press-vs-hold meaning UNKNOWN" % token["kind"]
    if name.endswith("Pressed"):
        base = name[:-len("Pressed")]
        partners = [t["name"] for t in line_tokens if t["kind"] == "onrelease"
                    and t["name"] in (base + "Released", base + "Released".replace("Released", "Release"))]
        if partners:
            return "press/release pair: %s + OnRelease %s (derived from names)" % (name, partners[0])
        return "press token %s, no matching OnRelease partner in its line (derived)" % name
    if any(t["kind"] == "onrelease" for t in line_tokens) and not name.endswith("Released"):
        return "exec token %s; line has an OnRelease handler for other tokens (derived)" % name
    return "exec token %s; no press/release pattern (derived)" % name


def derive():
    if not START_INI.exists():
        raise SystemExit("missing " + str(START_INI))
    chain = ini_chain(START_INI)
    chain_info = []
    for path, based in chain:
        chain_info.append({
            "file": rel(path),
            "exists": path.exists(),
            "based_on": based,
            "sha256": sha256_file(path) if path.exists() else None,
            "bytes": path.stat().st_size if path.exists() else None,
        })
    rows = parse_ini_chain_bindings(chain)

    # Other shipped config files: which ones carry any Batmobile/vehicle command.
    other_files = []
    for p in sorted(CONFIG.glob("*.ini")):
        n = 0
        for line in read_ini_lines(p):
            if KV_RE.match(line) and re.search(r"(?i)vehicle|batmobile|driv|boost|sonar|brake|eject", line):
                n += 1
        other_files.append({"file": rel(p), "vehicle_keyword_lines": n,
                            "in_pc_chain": any(c["file"] == rel(p) for c in chain_info)})

    # Classify every binding line and token.
    all_token_names = set()
    for r in rows:
        for t in r["tokens"]:
            if t["name"]:
                all_token_names.add(t["name"])
    relevance_rows = []
    for r in rows:
        names = [r["input_name"] or ""] + [t["name"] for t in r["tokens"]]
        veh_kw = any(VEHICLE_RE.search(x) for x in names if x)
        veh_cand = any(t["name"] in CANDIDATE_TOKENS for t in r["tokens"])
        if veh_kw:
            rel_label = "vehicle keyword in name or command (name match only)"
        elif veh_cand:
            rel_label = "vehicle candidate: generic token also used on foot; consumer UNKNOWN"
        else:
            rel_label = None
        r["relevance"] = rel_label
        r["hold_press"] = classify_hold(r["tokens"])
        relevance_rows.append(r)

    upk_info = {"path": rel(UPK), "bytes": UPK.stat().st_size}
    pkg = None
    lookups = {}
    funcs = []
    census = []
    states = []
    if UPK.exists():
        pkg = upk_read.Package(str(UPK))
        upk_info.update({"name_count": pkg.name_count, "export_count": pkg.export_count,
                         "import_count": pkg.import_count, "version": pkg.version,
                         "licensee": pkg.licensee})
        for tok in sorted(all_token_names | {r["input_name"] for r in rows if r["input_name"]
                                              and device_of(r["input_name"]) == "alias"}):
            lookups[tok] = name_lookup(pkg, tok)
        funcs = owners_of_functions(pkg, all_token_names)
        census = census_vehicle_names(pkg)
        states = state_census(pkg)
    else:
        upk_info["status"] = "MISSING"

    # Mode candidates: functions/states/properties on vehicle or player classes with mode words.
    mode_hits = []
    if pkg is not None:
        for i, e in enumerate(pkg.exports, 1):
            if e["name"] and MODE_RE.search(e["name"]) and VEHICLE_RE.search(
                    pkg.object_path(e["outer_index"]) or ""):
                mode_hits.append({"export_index": i, "name": e["name"],
                                  "class": pkg.class_name(e["class_index"]),
                                  "outer_path": pkg.object_path(e["outer_index"])})
                if len(mode_hits) >= 2000:
                    break

    # Alias table: Names that are not physical keys. A key line whose Command is an alias
    # name is expanded to that alias's Command (derived from the chain; recursive, cycle-guarded).
    alias_defs = {}
    for r in rows:
        if r["device"] == "alias" and r["input_name"]:
            alias_defs.setdefault(r["input_name"], []).append(r)
    alias_refs = {k: [] for k in alias_defs}

    def expand(tokens, row, via=(), depth=0, key_row=None):
        """row = the line that holds these tokens; key_row = the physical-key line the chain starts at."""
        key_row = key_row or row
        out = []
        for t in tokens:
            if t["kind"] == "exec" and t["name"] in alias_defs and t["name"] not in via and depth < 8:
                alias_refs[t["name"]].append({"from": "%s:%d" % (key_row["file"], key_row["line"]),
                                              "input": key_row["input_name"]})
                for ad in alias_defs[t["name"]]:
                    out.extend(expand(ad["tokens"], ad, via + (t["name"],), depth + 1, key_row))
            else:
                out.append({"token": t, "via": list(via), "row": row, "key_row": key_row})
        return out

    leaves = []
    for r in rows:
        if r["device"] == "alias":
            continue  # alias definitions are reached through expand(), not listed as keys
        for lf in expand(r["tokens"], r):
            leaves.append(lf)

    def relevant(t):
        return bool(t["name"]) and (VEHICLE_RE.search(t["name"]) or t["name"] in CANDIDATE_TOKENS)

    groups = {}
    for lf in leaves:
        t = lf["token"]
        if not relevant(t) or t["kind"] in ("onrelease", "count"):
            continue
        groups.setdefault(t["name"], []).append(lf)

    actions = []
    for tname in sorted(groups):
        items = groups[tname]
        bindings = []
        for lf in items:
            krow = lf["key_row"]
            drow = lf["row"]
            bindings.append({
                "input_name": krow["input_name"],
                "device": krow["device"],
                "source": "%s:%d" % (krow["file"], krow["line"]),
                "section": krow["section"],
                "section_occurrence": krow["section_occurrence"],
                "line_command": krow["command"],
                "token_as_written": lf["token"]["raw"],
                "defined_at": "%s:%d" % (drow["file"], drow["line"]),
                "defined_in_section": drow["section"],
                "via_alias": lf["via"],
                "hold_press": hold_for(lf["token"], drow["tokens"]),
                "problems": drow["problems"],
            })
        lk = lookups.get(tname) if pkg is not None else None
        if lk is None:
            consumer = {"status": "UNKNOWN", "tried": "BmGame.upk name table (package not read)"}
        elif lk["exports"]:
            e0 = lk["exports"][0]
            consumer = {"status": "name-match (decoded)",
                        "owner": ("%s.%s" % (e0["outer_path"], e0["name"])) if e0["outer_path"] else e0["name"],
                        "class": e0["class"], "export_index": e0["export_index"],
                        "exports_with_name": len(lk["exports"]),
                        "declared_in_state": e0["outer_path"] if e0.get("outer_class") == "State" else None,
                        "all_owners": ["%s (%s)" % ((x["outer_path"] or "") + "." + x["name"], x["class"])
                                       for x in lk["exports"]],
                        "note": "name match only; not proven that this export consumes the token"}
        elif lk["imports"]:
            i0 = lk["imports"][0]
            consumer = {"status": "import-name-match (decoded)", "owner": i0["package"] + "." + i0["name"],
                        "class": i0["class"], "note": "name match only"}
        else:
            consumer = {"status": "UNKNOWN",
                        "tried": "exact and case-insensitive name lookup in BmGame.upk exports/imports",
                        "in_name_table": lk["in_name_table"]}
        kinds = sorted({lf["token"]["kind"] for lf in items})
        actions.append({
            "token": tname,
            "token_kinds": kinds,
            "relevance": ("vehicle keyword in token name (name match only)" if VEHICLE_RE.search(tname)
                          else "vehicle candidate: generic movement/camera token also used on foot; "
                               "Batmobile use UNKNOWN"),
            "bindings": bindings,
            "keyboard": sorted({b["input_name"] for b in bindings if b["device"] == "keyboard/mouse"}),
            "gamepad": sorted({b["input_name"] for b in bindings if b["device"] == "gamepad"}),
            "consumer": consumer,
            "mode": "UNKNOWN (no decoded input-to-mode gate; see mode_candidates)",
        })

    unused_alias = sorted(k for k, v in alias_refs.items() if not v)
    alias_table = {k: {"defined_at": ["%s:%d (section %s)" % (x["file"], x["line"], x["section"])
                                      for x in alias_defs[k]],
                       "referenced_by_key_lines": alias_refs[k]} for k in sorted(alias_defs)}

    return {
        "schema": SCHEMA,
        "scope": "Batman: Arkham Knight, Batmobile controls (PC). Shipped config files and BmGame.upk.",
        "start_ini": rel(START_INI),
        "ini_chain": chain_info,
        "precedence_note": "chain order shown; how array Bindings entries merge across BasedOn is "
                           "UNKNOWN (not decoded from any file here)",
        "other_config_files": other_files,
        "bindings_total": len(rows),
        "bindings_with_vehicle_relevance": len([r for r in relevance_rows if r["relevance"]]),
        "bindings_by_device": {d: len([r for r in rows if r["device"] == d])
                               for d in ("gamepad", "keyboard/mouse", "alias", "none")},
        "problem_lines": [{"file": r["file"], "line": r["line"], "problems": r["problems"],
                           "raw_value": r["raw_value"]} for r in rows if r["problems"]],
        "upk": upk_info,
        "actions": actions,
        "alias_table": alias_table,
        "aliases_not_referenced_by_any_key_line": unused_alias,
        "token_lookup": lookups,
        "function_owners_of_tokens": funcs,
        "vehicle_function_census_count": len(census),
        "vehicle_function_census": census[:400],
        "mode_candidates": mode_hits,
        "state_census": states,
        "all_bindings": [{k: v for k, v in r.items() if k != "tokens"} | {
            "tokens": [t["raw"] for t in r["tokens"]]} for r in rows],
        "unknown": [],
    }


UNKNOWN_ITEMS = [
    {"item": "Merged effective binding set across the BasedOn chain (UE3 array merge with '.', '-', '+', '!' operators)",
     "tried": "parsed each file's operators and lines; no file in the chain documents the merge rule",
     "where": "UE3 config loader (engine binary), not present as text in these files"},
    {"item": "Runtime meaning of OnRelease <token> and of 'Button bX' / 'Count bX' tokens",
     "tried": "token classified from its text only",
     "where": "PlayerInput processing in the engine binary; not decoded"},
    {"item": "Which of BmInput.ini or the PC chain is actually loaded at runtime",
     "tried": "BmInput.ini is not referenced by any BasedOn line; it has an [IniVersion] block (game-written style)",
     "where": "engine config loading order; not decoded"},
    {"item": "User's live bindings (remaps)",
     "tried": "%USERPROFILE%\\Documents\\WB Games\\Batman Arkham Knight\\ contains only GFXSettings and STEAMID/SaveData; no input ini there",
     "where": "unknown whether the game stores remaps elsewhere; not searched outside Documents"},
    {"item": "Which script function a Batmobile action calls (exec body, state transitions)",
     "tried": "exact name lookup in BmGame.upk exports; owner class recorded",
     "where": "function bytecode in BmGame.upk (not disassembled here)"},
    {"item": "Exec flag of named token functions (whether the name is callable by the input layer)",
     "tried": "export table read; function flags are inside the export data, not parsed",
     "where": "BmGame.upk function export header"},
    {"item": "Which declaration runs when a state-declared function and a class-level function share a name (e.g. BatmobileFireButton on DrivingMode and on RPlayerController)",
     "tried": "both exports found and recorded (owner_path shows the state or class); runtime dispatch not decoded",
     "where": "RPlayerController bytecode / state machine in BmGame.upk"},
    {"item": "Input(s) that move between PursuitMode and BattleMode (both states exist on RVehicleBatmobileBase, decoded)",
     "tried": "names containing Pursuit/Mode/Battle on vehicle-related outers (mode_candidates); PursuitModeTagGun is bound on XboxTypeS_RightShoulder, but no decoded code links it to a mode change",
     "where": "RVehicleBatmobile / RPlayerController function bodies in BmGame.upk"},
    {"item": "Keyboard keys that drive the Batmobile (steer/throttle/brake)",
     "tried": "keyboard bindings with vehicle candidate tokens (W/A/S/D map to MoveForward/StrafeLeft which use Axis aBaseY / aStrafe); no keyboard binding names a vehicle-specific command",
     "where": "consumer of aBaseY / aStrafe in vehicle code (bytecode, UNKNOWN)"},
    {"item": "Gamepad analogue inputs for throttle and steering in the vehicle",
     "tried": "XboxTypeS_RightTriggerAxis binds aThrottleAxis; aBaseY/aStrafe/aTurn bound on sticks; consumers unknown",
     "where": "vehicle input code in BmGame.upk"},
    {"item": "Keys that exit or eject from the Batmobile, with their target state",
     "tried": "EjectFromVehicle on XboxTypeS_A; ExitVehiclePressed on alias ExitVehicle (no key); exec token exports checked",
     "where": "RVehicleBatmobile / RPlayerController bytecode"},
    {"item": "Packages other than BmGame.upk (Engine, other script packages)",
     "tried": "not searched; the task scope is BmGame.upk",
     "where": "CookedPCConsole other .upk files"},
]


def finalize(data):
    data["unknown"] = UNKNOWN_ITEMS
    return data


# ---------------------------------------------------------------- render

def md_escape(s):
    if s is None:
        return ""
    return str(s).replace("|", "\\|")


def render_md(d):
    L = []
    L.append("# CONTROLS - Batman: Arkham Knight, Batmobile (G3-02)")
    L.append("")
    L.append("Generated by `Tools/scripts/grab_controls.py --write`. Do not edit by hand; `--check` re-derives and compares.")
    L.append("")
    L.append("Labels: `decoded` = read from a file (file:line) or a package name/export; `derived` = computed from decoded facts (rule given); `UNKNOWN` = not decodable here, see the UNKNOWN list.")
    L.append("")
    L.append("## Sources")
    L.append("")
    L.append("PC ini chain (decoded, `BasedOn=` lines, start file `%s`):" % d["start_ini"])
    L.append("")
    L.append("| order | file | exists | BasedOn | sha256 (first 16) |")
    L.append("|---|---|---|---|---|")
    for i, c in enumerate(d["ini_chain"]):
        L.append("| %d | `%s` | %s | `%s` | `%s` |" % (i, c["file"], c["exists"], md_escape(c["based_on"]),
                                                  (c["sha256"] or "")[:16]))
    L.append("")
    L.append("Chain-order precedence is shown; the merge rule for array `Bindings` is **UNKNOWN** (see list).")
    L.append("")
    L.append("Bindings parsed: **%d** (decoded, all chain files). By device (derived from the Name field): %s."
             % (d["bindings_total"], ", ".join("%s %d" % (k, v) for k, v in d["bindings_by_device"].items())))
    L.append("")
    L.append("Lines flagged as malformed (decoded, kept as written): %d" % len(d["problem_lines"]))
    for p in d["problem_lines"]:
        L.append("- `%s:%d` - %s" % (p["file"], p["line"], "; ".join(p["problems"])))
    L.append("")
    L.append("Other config files (decoded, count of lines naming a vehicle keyword): ")
    for o in d["other_config_files"]:
        if o["vehicle_keyword_lines"]:
            L.append("- `%s`: %d (%s)" % (o["file"], o["vehicle_keyword_lines"],
                                          "in PC chain" if o["in_pc_chain"] else "NOT in PC chain"))
    L.append("")
    L.append("## Action table")
    L.append("")
    L.append("One row per vehicle-relevant command token after alias expansion. Token = the command as written (exec name, `Button bX`, or `Axis aX`). "
             "Keyboard / gamepad = the physical Name of the line that carries the token (decoded). "
             "Via alias = alias Names the token was reached through (decoded chain). "
             "Consumer = name-match export in BmGame.upk (decoded), which is NOT proof that it consumes the token. "
             "Hold/press = derived from the token pattern of the defining line.")
    L.append("")
    L.append("| token | kinds | keyboard | gamepad | via alias | source(s) (decoded) | consumer (name match) | hold / press (derived) | mode | relevance |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for a in d["actions"]:
        via = sorted({", ".join(b["via_alias"]) or "-" for b in a["bindings"]})
        srcs = "<br>".join("`%s` %s [%s]" % (b["source"], b["input_name"], b["defined_in_section"]) for b in a["bindings"])
        holds = sorted({b["hold_press"] for b in a["bindings"]})
        c = a["consumer"]
        if c["status"].startswith("name-match"):
            cons = "`%s` (%s) - %s%s" % (md_escape(c["owner"]), c["class"], c["status"],
                                         ("; declared in state `%s`" % c["declared_in_state"]) if c.get("declared_in_state") else "")
        elif c["status"].startswith("import"):
            cons = "`%s` - %s" % (md_escape(c["owner"]), c["status"])
        else:
            cons = "UNKNOWN (%s)" % c.get("tried", "")
        L.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            md_escape(a["token"]), ", ".join(a["token_kinds"]),
            ", ".join(a["keyboard"]) or "none in chain", ", ".join(a["gamepad"]) or "none in chain",
            "; ".join(via), srcs, cons, "; ".join(holds), a["mode"], a["relevance"]))
    L.append("")
    L.append("Note: an alias defined in more than one section (e.g. `MoveForward` in Engine.PlayerInput and in Engine.DebugCameraInput) is listed for each definition; which section applies at runtime is UNKNOWN.")
    L.append("")
    L.append("## Alias table (decoded)")
    L.append("")
    L.append("Named actions defined without a physical key. A key line whose Command names one of these is expanded to its Command.")
    L.append("")
    L.append("| alias | defined at | referenced by key lines |")
    L.append("|---|---|---|")
    for k, v in d["alias_table"].items():
        refs = "; ".join("`%s` (%s)" % (x["from"], x["input"]) for x in v["referenced_by_key_lines"]) or "none"
        L.append("| `%s` | %s | %s |" % (k, "; ".join(v["defined_at"]), refs))
    L.append("")
    L.append("## Pursuit / battle mode")
    L.append("")
    L.append("Mode gate for each action: **UNKNOWN** (no decoded input-to-mode link). Names containing mode words on vehicle-related outers (decoded from the export table, %d hits; first 40 shown):" % len(d["mode_candidates"]))
    L.append("")
    L.append("| export | name | class | outer |")
    L.append("|---|---|---|---|")
    for m in d["mode_candidates"][:40]:
        L.append("| %d | `%s` | %s | `%s` |" % (m["export_index"], m["name"], m["class"], md_escape(m["outer_path"])))
    L.append("")
    L.append("States on player-controller and vehicle classes with a mode word (decoded from the export table): %d"
             % len(d["state_census"]))
    L.append("")
    L.append("| export | state | declared on |")
    L.append("|---|---|---|")
    for st in d["state_census"]:
        L.append("| %d | `%s` | `%s` |" % (st["export_index"], st["state"], st["outer_class"]))
    L.append("")
    L.append("## Token lookups in BmGame.upk (decoded)")
    L.append("")
    L.append("| token | in name table | exports with that name | first owner |")
    L.append("|---|---|---|---|")
    for tok in sorted(d["token_lookup"]):
        lk = d["token_lookup"][tok]
        owner = ""
        if lk["exports"]:
            e0 = lk["exports"][0]
            owner = "`%s` (%s)" % (md_escape((e0["outer_path"] or "") + "." + e0["name"]), e0["class"])
        elif lk["imports"]:
            owner = "import `%s.%s`" % (lk["imports"][0]["package"], lk["imports"][0]["name"])
        L.append("| `%s` | %s | %d | %s |" % (tok, lk["in_name_table"], len(lk["exports"]), owner))
    L.append("")
    L.append("## UNKNOWN / not reached")
    L.append("")
    for u in d["unknown"]:
        L.append("- **%s** - tried: %s. Would be in: %s." % (u["item"], u["tried"], u["where"]))
    L.append("")
    L.append("## Package")
    L.append("")
    L.append("`%s`: %s" % (d["upk"]["path"], json.dumps({k: v for k, v in d["upk"].items() if k != "path"}, sort_keys=True)))
    L.append("")
    return "\n".join(L) + "\n"


def to_json_text(d):
    return json.dumps(d, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write CONTROLS.md and CONTROLS.json")
    g.add_argument("--check", action="store_true", help="re-derive and compare with the written files")
    a = ap.parse_args()
    d = finalize(derive())
    md = render_md(d)
    js = to_json_text(d)
    if a.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(md, encoding="utf-8", newline="\n")
        OUT_JSON.write_text(js, encoding="utf-8", newline="\n")
        print("wrote %s and %s" % (OUT_MD, OUT_JSON))
        print("bindings %d, actions %d, tokens looked up %d" % (d["bindings_total"], len(d["actions"]), len(d["token_lookup"])))
        return 0
    ok = True
    for path, text in ((OUT_MD, md), (OUT_JSON, js)):
        if not path.exists():
            print("MISSING %s" % path)
            ok = False
            continue
        if path.read_text(encoding="utf-8") != text:
            print("DIFFERS %s" % path)
            ok = False
        else:
            print("same    %s" % path)
    print("check ok" if ok else "check FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
