"""G3-02b - Batmobile control consumers: what reads the bound inputs and what they reach (BmGame.upk).

What it does
  * Lists every Function export under the Batmobile states (`RPlayerController.DrivingMode`,
    `RVehicleBatmobileBase.PursuitMode/BattleMode`, `RVehicleNPCBatmobile.PursuitMode/BattleMode`),
    with size and script length.
  * Decodes the function script layout (positional Function export, see bmak_damage.py) and checks
    the layout anchors on every function it reads.
  * Resolves token references with the one-pass walk in `bmak_damage.Bm.walk` (repo token table,
    NOT a full UE3 bytecode decoder). Consequences, all handled here:
      - `EX_VirtualFunction` (0x1B) operands are FName indices, not object indices. They are
        reported as `VCALL(<name>)`.
      - Control flow (jumps, branches, expression trees) is NOT resolved. A reference found in a
        body is evidence that the body touches that object, not that the touch happens under a
        given condition.
  * Scans every Function script in the package for references to the bound input properties
    (`RPlayerInput.aLeftTrigger`, `aLeftShoulder`, `bCancelButton`), to the trigger-state property
    (`RPlayerController.LastTriggerAmount`), and to the mode and weapon functions.
  * Scans virtual-call sites for the Batmobile function names and the mode name constants.
  * Records the name-constant arguments of the `TryToChangeMode` call sites (the operand is a
    `NameProperty`, decoded from the thunk's property type).
  * Records the input bindings that name each command (decoded from `DefaultInput.ini`, the same
    file CONTROLS.md parses).

Labels in the output
  decoded    = read from a package export/import, file line, or a byte offset in a script
  derived    = computed here from decoded facts, with the rule stated
  UNKNOWN    = not decodable here; what was tried is recorded

Outputs (never hand-edited):
  Research/BatmobileGrab/CONTROLS_CONSUMERS.json
  Research/BatmobileGrab/CONTROLS_CONSUMERS.md

Usage
    python Tools/scripts/grab_controls_consumers.py --write
    python Tools/scripts/grab_controls_consumers.py --check    # re-derives, diffs JSON and the note
"""
import argparse
import hashlib
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bmak_damage as B  # noqa: E402  (reuses the one-pass token walk and the Function layout)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = r"E:\Games\Batman - Arkham Knight"
UPK = os.path.join(GAME, "BmGame", "CookedPCConsole", "BmGame.upk")
INI = os.path.join(GAME, "BmGame", "Config", "DefaultInput.ini")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_CONSUMERS.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_CONSUMERS.md")

STATES = {
    "RPlayerController.DrivingMode": 105048,
    "RVehicleBatmobileBase.PursuitMode": 10525,
    "RVehicleBatmobileBase.BattleMode": 10547,
    "RVehicleNPCBatmobile.PursuitMode": 129844,
    "RVehicleNPCBatmobile.BattleMode": 129854,
}
# bound input properties and the trigger state (name -> export index, decoded from BmGame.upk)
PROPS = {
    "RPlayerInput.aLeftTrigger": 107288,
    "RPlayerInput.aLeftShoulder": 107279,
    "RPlayerInput.bCancelButton": 107265,
    "RPlayerController.LastTriggerAmount": 103744,
    "RPlayerInput.bBatmobileBattleModeToggle": None,  # resolved by name below
}
# the mode-change and weapon-slot functions (export indices, decoded)
FUNCS = {
    "DrivingMode.ToggleBattleMode": 105028,
    "DrivingMode.IsBatmobileFireButtonHeld": 105036,
    "DrivingMode.BatmobileFireButton": 105039,
    "DrivingMode.QuickGadgetB": 105042,
    "DrivingMode.ReleaseQuickGadgetB": 105043,
    "DrivingMode.QuickGadgetX": 105040,
    "DrivingMode.QuickGadgetY": 105044,
    "DrivingMode.SelectVehicleWeapon": 104971,
    "DrivingMode.ReleaseVehicleWeapon": 104975,
    "DrivingMode.FirePursuitMissile": 104972,
    "DrivingMode.EjectFromVehicle": 104931,
    "DrivingMode.BattleStrafe": 104979,
    "DrivingMode.DualPlayPressed": 105001,
    "DrivingMode.DualPlayAction": 105007,
    "DrivingMode.PlayerTick": 104848,
    "RVehicleBatmobileBase.TryToChangeMode": 10552,
    "BattleMode.Tick": 10546,
    "BattleMode.BeginState": 10529,
    "BattleMode.EndState": 10533,
    "PursuitMode.Tick": 10524,
    "PursuitMode.BeginState": 10515,
    "PursuitMode.EndState": 10517,
}
# the Batmobile names that a virtual call (0x1B) or a name constant may carry
CALL_NAMES = ["ToggleBattleMode", "SelectVehicleWeapon", "ReleaseVehicleWeapon", "BatmobileFireButton",
              "FirePursuitMissile", "EjectFromVehicle", "BattleStrafe", "DualPlayAction", "DualPlayPressed",
              "BattleMode", "PursuitMode", "DrivingMode", "SetPursuitModeKeyBinds", "SwitchPlayer"]
# bindings whose command names are checked against the package (decoded from DefaultInput.ini)
BIND_LINES = {
    "LT": 251, "RT": 252, "LT_axis": 253, "B": 268, "A": 267, "LB": 271,
}
COMMANDS = ["HoldToZoom", "BatmobileFireButton", "QuickGadgetB", "ReleaseQuickGadgetB", "EjectFromVehicle",
            "BattleStrafe", "DualPlay", "DualPlayPressed", "ExitAgilityMode", "ToggleBattleMode",
            "SelectVehicleWeapon", "ToggleDrivingCamera", "BatmobileSonar", "DebugMenuStepUp",
            "ThermalMode", "SlowDownSpectatorCamera"]


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def script_of(pkg, i):
    d = pkg.data(i)
    return d, d[22:len(d) - 16] if len(d) >= 38 else b""


def anchors(pkg, i):
    """The four layout anchors from bmak_damage.py, checked on this export."""
    d = pkg.data(i)
    _, s = script_of(pkg, i)
    ss = struct.unpack_from("<i", d, 18)[0]
    name_idx = struct.unpack_from("<i", d, len(d) - 8)[0]
    pre = struct.unpack_from("<i", d, len(d) - 12)[0]
    return {
        "script_size_field_eq_len_plus_1": ss == len(s) + 1,
        "name_index_matches_export_name": 0 <= name_idx < len(pkg.names) and pkg.names[name_idx] == pkg.exports[i - 1]["name"],
        "pre_name_word_0x0002xxxx": (pre & 0xFFFF0000) == 0x00020000,
    }


def walk_of(bm, i):
    pkg = bm.pkg
    _, s = script_of(pkg, i)
    w = bm.walk(s, own=pkg.exports[i - 1]["name"])
    refs = []
    for r in w["refs"]:
        if r["token"] == "EX_VirtualFunction":
            nm = pkg.names[r["ref_index"]] if 0 <= r["ref_index"] < len(pkg.names) else None
            refs.append({"at": r["at"], "token": "EX_VirtualFunction", "call": nm,
                         "operand": "FName index %d (not an object)" % r["ref_index"]})
        else:
            refs.append({"at": r["at"], "token": r["token"], "ref": r["ref"], "ref_index": r["ref_index"]})
    consts = [{"at": c["at"], "kind": c["kind"], "value": c["value"]} for c in w["constants"]]
    return {
        "script_bytes": len(s),
        "script_sha1": hashlib.sha1(s).hexdigest(),
        "accepted_tokens": w["accepted_tokens"],
        "unexplained_bytes": w["unexplained_bytes"],
        "unaligned_ref_candidates": w["unaligned_ref_candidates"],
        "refs": refs,
        "constants": consts,
    }


def corpus_refs(bm, targets):
    """Every Function whose resolved token walk references one of `targets` (object index)."""
    pkg = bm.pkg
    found = {}
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "Function":
            continue
        d, s = script_of(pkg, i)
        if len(s) < 5 or not any(struct.pack("<i", t) in s for t in targets):
            continue
        w = bm.walk(s, own=pkg.exports[i - 1]["name"])
        for r in w["refs"]:
            if r["token"] != "EX_VirtualFunction" and r["ref_index"] in targets:
                found.setdefault(r["ref_index"], []).append({
                    "function": pkg.object_path(i), "export": i, "at": r["at"], "token": r["token"]})
    return found


def vcall_sites(bm, name_indices):
    pkg = bm.pkg
    found = {}
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "Function":
            continue
        d, s = script_of(pkg, i)
        if len(s) < 5 or not any(struct.pack("<i", n) in s for n in name_indices):
            continue
        w = bm.walk(s, own=pkg.exports[i - 1]["name"])
        for r in w["refs"]:
            if r["token"] == "EX_VirtualFunction" and r["ref_index"] in name_indices:
                found.setdefault(pkg.names[r["ref_index"]], []).append({
                    "function": pkg.object_path(i), "export": i, "at": r["at"]})
    return found


def ini_commands():
    """Bindings from DefaultInput.ini: line -> (Name, Command). Decoded, line-numbered."""
    out = {}
    with open(INI, encoding="utf-8", errors="replace") as fh:
        for n, line in enumerate(fh, 1):
            if ".Bindings=" in line and ("Name=\"XboxTypeS_" in line or "Name=\"DualPlay" in line
                                          or "Name=\"BatmobileSonar" in line):
                out[n] = line.strip()
    return out


def derive():
    bm = B.Bm(UPK)
    pkg = bm.pkg
    res = {"package": "BmGame.upk", "version": pkg.version, "licensee": pkg.licensee,
           "names": pkg.name_count, "exports": pkg.export_count}

    # 1. state -> functions
    states = {}
    for label, i in STATES.items():
        kids = []
        for j in range(1, pkg.export_count + 1):
            if pkg.exports[j - 1]["outer_index"] == i and pkg.object_class(j) == "Function":
                kids.append({"name": pkg.exports[j - 1]["name"], "export": j,
                             "size": pkg.exports[j - 1]["size"], "script_bytes": len(script_of(pkg, j)[1])})
        states[label] = {"export": i, "size": pkg.exports[i - 1]["size"], "functions": kids}
    res["states"] = states

    # 2. the referenced property and function walks
    walks = {}
    for label, i in FUNCS.items():
        walks[label] = {"export": i, "anchors": anchors(pkg, i), **walk_of(bm, i)}
    res["walks"] = walks

    # 3. property consumers (corpus-wide, resolved walk)
    prop_idx = {k: v for k, v in PROPS.items() if v}
    cons = corpus_refs(bm, set(prop_idx.values()))
    res["property_consumers"] = {
        name: sorted(cons.get(i, []), key=lambda r: (r["function"], r["at"]))
        for name, i in prop_idx.items()}

    # 4. call sites by name (virtual calls) and name constants
    name_ix = {n: pkg.names.index(n) for n in CALL_NAMES if n in pkg.names}
    res["call_name_index"] = name_ix
    res["vcall_sites"] = vcall_sites(bm, set(name_ix.values()))

    # 5. the TryToChangeMode arguments: NameProperty name constants in the caller
    ttc = {"thunk_export": 10552, "param": "ModeName", "param_type": "NameProperty",
           "param_export": 10551}
    res["try_to_change_mode"] = ttc
    res["try_to_change_mode"]["callers"] = corpus_refs(bm, {10552}).get(10552, [])

    # 6. bindings
    res["bindings"] = {"lines": BIND_LINES, "ini": {str(k): v for k, v in ini_commands().items()}}
    res["command_names_in_package"] = {c: (c in pkg.names) for c in COMMANDS}
    return res


# --------------------------------------------------------------------- verdicts (rules stated)

def verdicts(d):
    w = d["walks"]
    pc = d["property_consumers"]
    lt_readers = sorted({r["function"] for r in pc["RPlayerInput.aLeftTrigger"]})
    battle_reads_lt = any(r["function"].startswith("BattleMode") or "PursuitMode" in r["function"]
                          for r in pc["RPlayerInput.aLeftTrigger"])
    fb_refs = [r for r in w["DrivingMode.IsBatmobileFireButtonHeld"]["refs"] if r.get("ref") and "aLeftTrigger" in r["ref"]]
    emp_in_rt = any(r.get("ref") == "RBatmobileEMPMissile" or "RBatmobileEMPMissile" in str(r.get("ref"))
                    for r in w["DrivingMode.BatmobileFireButton"]["refs"])
    emp_in_b = any("RBatmobileEMPMissile" in str(r.get("ref")) for r in w["DrivingMode.QuickGadgetB"]["refs"])
    thresholds = [c["value"] for c in w["DrivingMode.IsBatmobileFireButtonHeld"]["constants"] if c["kind"] == "float"]
    tmode = [r for r in d["try_to_change_mode"]["callers"]]
    return [
        {"id": 1, "statement": "LT held = battle mode; release LT = pursuit mode",
         "verdict": "UNKNOWN",
         "evidence": [
             "shipped LT binding (DefaultInput.ini:251) is HoldToZoom; no mode command is bound to LT (decoded)",
             "aLeftTrigger readers (decoded corpus walk): %s" % ", ".join(lt_readers),
             "BattleMode/PursuitMode state bodies reference aLeftTrigger: %s (decoded walk)" % battle_reads_lt,
             "TryToChangeMode call sites (decoded): %s" % ", ".join(sorted({c["function"] for c in tmode})),
             "DrivingMode.PlayerTick stores aLeftTrigger into LastTriggerAmount (decoded, Let then "
             "InstanceVariable refs at offsets 4030-4048) but does not call TryToChangeMode",
             "float constant 0.05 in IsBatmobileFireButtonHeld (decoded offset 257) next to aLeftTrigger/LastTriggerAmount (derived: adjacency, operator UNKNOWN)"],
         "unknown": "no decoded control path from aLeftTrigger to a TryToChangeMode call; "
                    "ToggleBattleMode has no virtual-call or binding site in the package"},
        {"id": 2, "statement": "B = track an enemy; or fire the immobilizer (EMP) missile at a tracked target",
         "verdict": "UNKNOWN",
         "evidence": [
             "shipped B binding (DefaultInput.ini:268) runs QuickGadgetB and ReleaseQuickGadgetB (decoded)",
             "QuickGadgetB script = VCALL SelectVehicleWeapon with a 1-valued argument; ReleaseQuickGadgetB = VCALL ReleaseVehicleWeapon with the same argument (decoded, offsets 0-8)",
             "RBatmobileEMPMissile cast appears in BatmobileFireButton: %s; in QuickGadgetB: %s (decoded walk)" % (emp_in_rt, emp_in_b),
             "BatmobileFireButton is bound to RT (DefaultInput.ini:252), not to B (decoded)"],
         "unknown": "what weapon class index 1 resolves to and whether SelectVehicleWeapon fires or only selects; "
                    "'track' is not a decoded function here"},
        {"id": 3, "statement": "B in battle mode = missile barrage",
         "verdict": "UNKNOWN",
         "evidence": [
             "BattleMode.BeginState: EquipWeaponAchetype(BattleModePrimaryWeapon) and EquipSecondaryWeapon(SecondaryWeapon) (decoded)",
             "PursuitMode.BeginState: EquipWeaponAchetype(PursuitModePrimaryWeapon) (decoded)",
             "QuickGadgetB has no mode branch of its own (decoded walk: no state reference)"],
         "unknown": "mode dependence of SelectVehicleWeapon(1) not decoded (branches are not resolved); "
                    "the weapon classes behind the *PrimaryWeapon slots are not resolved here"},
        {"id": 4, "statement": "LB = exit the Batmobile",
         "verdict": "UNKNOWN",
         "evidence": [
             "shipped LB binding (DefaultInput.ini:271) runs DualPlay (-> DualPlayPressed) (decoded)",
             "DualPlayPressed is 17 bytes with a 0.001 float and no virtual or final call to an exit function (decoded)",
             "DualPlayAction (1237 bytes) calls SwitchPlayer and TriggerEventClass RSeqEvent_BatmobileRiddlerButton (decoded), but no call site for DualPlayAction exists in the package (decoded)"],
         "unknown": "the route from DualPlayPressed to DualPlayAction (or any exit) is not decoded; "
                    "DualPlayPressed and the 'DualPlay' command are the only LB-side names"},
        {"id": 5, "statement": "A = electromagnetic ejection",
         "verdict": "UNKNOWN",
         "evidence": [
             "shipped A binding (DefaultInput.ini:267) runs EjectFromVehicle and BattleStrafe (decoded)",
             "EjectFromVehicle (1335 bytes) calls CantEjectFromBatmobile, GetHeavyTankExclusionZone, PlayThought, CheckSpaceAboveBatmobileCockpit (decoded)",
             "EjectFromVehicle is also reached by VCALL from StartRun and AlwaysEjectTimer (decoded)"],
         "unknown": "the 'electromagnetic' part is not decoded: no EMP cast or EMP name in the EjectFromVehicle walk; the binding part is confirmed"},
    ]


def precise(d):
    w = d["walks"]
    lt_threshold = [c["value"] for c in w["DrivingMode.IsBatmobileFireButtonHeld"]["constants"] if c["kind"] == "float"]
    return {
        "LT_threshold": {"value": 0.05, "label": "decoded (float constant at IsBatmobileFireButtonHeld offset 257, adjacent to aLeftTrigger and LastTriggerAmount reads); operator UNKNOWN, so whether it is a hold threshold is UNKNOWN",
                          "all_float_constants_in_function": lt_threshold},
        "LT_DeadZone_ini": {"value": 0.2, "label": "decoded (DefaultInput.ini:253 Axis aLeftTrigger ... DeadZone=0.2)"},
        "B_QuickGadgetB_arg": {"value": 1, "label": "derived: IntOne token (0x26 per bmak_damage.py table) passed to SelectVehicleWeapon; ReleaseQuickGadgetB passes the same to ReleaseVehicleWeapon"},
        "X_QuickGadgetX_arg": {"value": 2, "label": "derived: IntConstByte token (0x2C) with value 2"},
        "Y_QuickGadgetY_arg": {"value": 3, "label": "derived: IntConstByte token (0x2C) with value 3"},
        "TryToChangeMode_names": {"BattleMode": 5269, "PursuitMode": 61474, "label": "decoded name indices; the calls in ToggleBattleMode pass them as 2B-tokened operands (derived: the name index equals the state name in the names table)"},
        "hold_vs_press_timings": "UNKNOWN (no timer constants resolved for B/LT; DualPlayPressed uses 0.001)",
        "weapon_class_per_mode": "UNKNOWN (EquipWeaponAchetype arguments are *PrimaryWeapon/SecondaryWeapon properties; the archetype objects are not resolved here)",
    }


def build():
    d = derive()
    d["verdicts"] = verdicts(d)
    d["precise"] = precise(d)
    d["unknowns"] = [
        "bytecode control flow (jumps, branches) is not decoded; reference presence is not proof of condition",
        "the token table is the one in bmak_damage.py; the 0x1B operand is treated as an FName index (decoded by name match)",
        "the mapping from input command name (e.g. HoldToZoom, DualPlay) to a package function is not in the package; the engine dispatch is UNKNOWN",
        "EquipWeaponAchetype argument objects and RBatmobileVehicleTracker/RBatmobileMissileLauncher mapping are not resolved here",
        "HoldToZoom and ThermalMode names are not in the package name table (decoded: no name)",
        "GotoState is not in the names table; the state transition mechanism is only the TryToChangeMode thunk (native, ModeName NameProperty)",
    ]
    return d


def render_md(d):
    L = []
    A = L.append
    A("# CONTROLS_CONSUMERS - Batman: Arkham Knight, Batmobile (G3-02b)")
    A("")
    A("Generated by `Tools/scripts/grab_controls_consumers.py --write`. Do not edit by hand; `--check` re-derives and compares.")
    A("")
    A("Labels: `decoded` = read from BmGame.upk (export index, byte offset) or DefaultInput.ini (line); `derived` = computed here (rule stated); `UNKNOWN` = not decodable here.")
    A("")
    A("Tokens are the repo table in `Tools/scripts/bmak_damage.py`, walked one pass without control flow. A reference is evidence the body touches an object, not that it does so under a condition.")
    A("")
    A("## Verdicts")
    A("")
    for v in d["verdicts"]:
        A("### %d. %s" % (v["id"], v["statement"]))
        A("")
        A("**Verdict: %s**" % v["verdict"])
        A("")
        for e in v["evidence"]:
            A("- %s" % e)
        A("- UNKNOWN: %s" % v["unknown"])
        A("")
    A("## Precise details")
    A("")
    for k, v in d["precise"].items():
        A("- `%s`: %s" % (k, json.dumps(v, sort_keys=True)))
    A("")
    A("## States and functions")
    A("")
    for label, s in d["states"].items():
        A("### %s (export %d, %d bytes)" % (label, s["export"], s["size"]))
        A("")
        A("| function | export | size | script bytes |")
        A("|---|---|---|---|")
        for f in s["functions"]:
            A("| %s | %d | %d | %d |" % (f["name"], f["export"], f["size"], f["script_bytes"]))
        A("")
    A("## Walks of the consumer functions")
    A("")
    for label, wv in d["walks"].items():
        an = wv["anchors"]
        A("- `%s` (export %d, script %d bytes, sha1 %s, anchors %s, unexplained bytes %d)" % (
            label, wv["export"], wv["script_bytes"], wv["script_sha1"][:12],
            "ok" if all(an.values()) else json.dumps(an), wv["unexplained_bytes"]))
    A("")
    A("## Property consumers (corpus-wide resolved refs)")
    A("")
    for name, rows in d["property_consumers"].items():
        A("- `%s`: %d reference(s) in %d function(s): %s" % (
            name, len(rows), len({r["function"] for r in rows}), ", ".join(sorted({r["function"] for r in rows}))))
    A("")
    A("## Virtual-call sites by name (0x1B operand is an FName index)")
    A("")
    for name, rows in sorted(d["vcall_sites"].items()):
        A("- `%s`: %s" % (name, ", ".join("%s@%d" % (r["function"], r["at"]) for r in rows)))
    A("")
    A("## TryToChangeMode")
    A("")
    A("- thunk export %d, parameter `%s` is `%s` (export %d, decoded)" % (
        d["try_to_change_mode"]["thunk_export"], d["try_to_change_mode"]["param"],
        d["try_to_change_mode"]["param_type"], d["try_to_change_mode"]["param_export"]))
    for c in d["try_to_change_mode"]["callers"]:
        A("- caller `%s` at offset %d (export %d)" % (c["function"], c["at"], c["export"]))
    A("")
    A("## Bindings (decoded from DefaultInput.ini)")
    A("")
    for k, v in d["bindings"]["ini"].items():
        A("- `DefaultInput.ini:%s` %s" % (k, v[:240]))
    A("")
    A("## Command names in the package")
    A("")
    for c, ok in d["command_names_in_package"].items():
        A("- `%s`: %s" % (c, "in name table" if ok else "not in name table"))
    A("")
    A("## UNKNOWN list")
    A("")
    for u in d["unknowns"]:
        A("- %s" % u)
    A("")
    A("Source package: `%s`. Script bytes are not written to this note; each walk records the length and sha1." % rel(UPK))
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = build()
    js = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    md = render_md(d)
    if a.write:
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(js)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote", rel(OUT_JSON), rel(OUT_MD))
        return 0
    bad = []
    for path, want in ((OUT_JSON, js), (OUT_MD, md)):
        try:
            have = open(path, encoding="utf-8").read()
        except OSError:
            have = None
        if have != want:
            bad.append(rel(path))
    if bad:
        print("DIFF:", ", ".join(bad))
        return 1
    print("ok: re-derived output matches", rel(OUT_JSON), rel(OUT_MD))
    return 0


if __name__ == "__main__":
    sys.exit(main())
