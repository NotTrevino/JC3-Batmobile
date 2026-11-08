"""t19_hud.py - T-19: finish the vehicle-HUD rows (weapon slots, icons, reticle, cooldown, heat, lock-on).

The card (`GRAB_BACKLOG.md` §7, `#### T-19`) says:

    Do: complete T-HUD5 (weapon slots/icons), lock-on, heat/cooldown mapping; keep T-HUD1…3.
    Out: rows in `T6_HUD_CAMERA.md`.
    Done: each HUD element mapped or omitted with proof.

T-HUD5 was one blocked row ("the HUD supports it, the entity does not"). This tool splits it into
one row per HUD element and pins every cell to a file:

  * `Research/BatmobileGrab/HUD_INTERFACES.json` (G1 HUD grab) - the BmAK setter and its argument
    signature, so the BmAK column is quoted from the interface, never remembered;
  * `Research/JC3Grab/JC3_HUD_WEAPONS.json` (G2-25) - the JC3 side: 2 slots, the cooldown fraction,
    the reticle shapes/looks, the icon ids, the one lock-on POI, and the `heat` block whose two
    zeros are the absence proof;
  * `Working/Translation/t7_weapons_edits.json` (T-11) - which weapon is bound to which driver slot,
    i.e. what the two clips will actually show.

Every row carries a `proof`: a dotted path into the G2-25 json plus the value it must hold, or the
absence count that must stay 0. `--check` re-evaluates every proof, re-renders the block and
compares. A row that claims `map` without a member behind it fails, and any G2-25 element that no
row covers fails.

The generated block lives between `<!-- T19-HUD-BEGIN -->` and `<!-- T19-HUD-END -->` inside
`Working/Translation/T6_HUD_CAMERA.md` §1, inserted before the "one HUD finding" paragraph on the
first `--write`. Rows T-HUD1…T-HUD10 are not rewritten: the block states that T-HUD5 is completed
by the new rows and that T-HUD1…3 are kept (both assertions are checked against the table).

Usage:
  python Tools/scripts/t19_hud.py --write
  python Tools/scripts/t19_hud.py --check
  python Tools/scripts/t19_hud.py --show T-HUD16
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WORK = os.path.join(ROOT, "Working", "Translation")
DOC = os.path.join(WORK, "T6_HUD_CAMERA.md")
JS = os.path.join(WORK, "t19_hud.json")
HUD_IFACE = os.path.join(ROOT, "Research", "BatmobileGrab", "HUD_INTERFACES.json")
JC3_HUD = os.path.join(ROOT, "Research", "JC3Grab", "JC3_HUD_WEAPONS.json")
T7_EDITS = os.path.join(WORK, "t7_weapons_edits.json")

BEGIN = "<!-- T19-HUD-BEGIN -->"
END = "<!-- T19-HUD-END -->"
ANCHOR = "**The one HUD finding that changes the plan:**"

# The G2-25 element names (its `wpn12` table). Every one must be covered by at least one row.
ELEMENTS = ["weapon slots", "reticle", "cannon cooldown", "Vulcan heat", "missile lock"]

# Rows. `bmak` names setters that must exist in HUD_INTERFACES.json (`bmak_module` / `bmak_setters`);
# `jc3` names the member strings; `proof` is (path, expected) evaluated against JC3_HUD_WEAPONS.json.
ROWS = [
    dict(id="T-HUD11", element="weapon slots",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetPrimaryWeapon", "UC_SetSecondaryWeapon", "UC_SetSpecialWeapons"],
         jc3="`InitVehicleWeapons(slot_index 0..1)` -> `MCI_vehicle_weapons0` / `MCI_vehicle_weapons1` "
             "(`EVEHICLE_WEAPON_SLOT_MAIN` 0, `..._ALTERNATIVE` 1) in `VehicleConstructor`",
         value="slot 0 = the cannon clone of `w602_mediumtank_canon` (`main_weapon`, T-11); "
               "slot 1 = the Vulcan clone of `w603_mediumtank_mgun` (root `id:00568A74`, T-11)",
         klass="decoded", disposition="map",
         limit="2 slots: the 3 special-weapon states (`UC_SetSpecialWeapons(int, int, int)`) have "
               "no member; the missile launcher is bound to no slot (T-WP13's blocked row)",
         verify="Q-3 #3: two clips show the two bound weapon ids",
         proof=[("slots.count", 2)]),
    dict(id="T-HUD12", element="weapon slots",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetPrimaryWeapon", "UC_SetSecondaryWeapon"],
         jc3="`InitVehicleWeapons(weapon_name)` -> `TXT_name` (the label under the slot)",
         value="BmAK's weapon name string passes through unchanged",
         klass="decoded", disposition="map",
         limit="`UpdateVehicleWeapons` cannot change the label: a slot that changes weapon needs "
               "`InitVehicleWeapons` again (G2-25 §2)",
         verify="Q-3 #3: the label reads the bound weapon, not the donor's",
         proof=[("init.params", "weapon_name")]),
    dict(id="T-HUD13", element="weapon slots",
         bmak_module="HudModuleBatmobile",
         bmak_setters=[],
         jc3="`weapon_icons/<weapon_id>.ddsc` - `GetWeaponIconName(weapon_id)`, `_sm.ddsc` for low "
             "res, ids -1 and 0 rejected",
         value="ids 602, 603, 618, 619: all four are in the shipped icon set, so both slots draw",
         klass="decoded", disposition="map",
         limit="the icon is a JC3 file named by the weapon id; BmAK has no icon id (0 of "
               "`HudModuleBatmobile`'s 37 setters name an icon). Id 614 must not be reused - its "
               "icon was never shipped (G2-25 §6)",
         verify="Q-3 #3: each slot shows its own weapon icon",
         proof=[("icons.ids", [602, 603, 618, 619])]),
    dict(id="T-HUD14", element="reticle",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetCannonCoolDown"],
         jc3="`UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)`; shape "
             "`E_RETICLE_CANNON = 8`, 5 look states, marker y -111 for shapes 8/11/12",
         value="the heavy vehicle reticle is shape 8 (`E_RETICLE_CANNON`)",
         klass="decoded", disposition="map (shape id UNKNOWN)",
         limit="no file maps `E_RETICLE_CANNON` to a vehicle cannon - the shape id is the closest "
               "named member, not a proven binding (G2-25 §4)",
         verify="Q-3 #3: the reticle appears with the cannon and hides with it",
         proof=[("reticle.shapes", "E_RETICLE_CANNON")]),
    dict(id="T-HUD15", element="reticle",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetMachineGunAccuracyFrame"],
         jc3="`UpdateWeaponReticle(reticle_size)` 5..30 px + `weapons_look` 5 states",
         value="accuracy frame -> `reticle_size`",
         klass="UNKNOWN", disposition="partial",
         limit="the BmAK frame is an index with no stated domain or pixel mapping, and "
               "`weapons_look` is a target relation, not an accuracy state: the member exists, the "
               "scale does not. Nothing is hand-substituted (G2-25 §4)",
         verify="Q-3 #3: the reticle tightens when the Vulcan settles",
         proof=[("reticle.params", "reticle_size")]),
    dict(id="T-HUD16", element="cannon cooldown",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetCannonCoolDown"],
         jc3="`weapon_cooldown` 0..1 in `InitVehicleWeapons` / `UpdateVehicleWeapons`; "
             "`SetCooldownRotation`: rot = cooldown x 360 over `MCI_mask_0_50` / `MCI_mask_50_100`; "
             "-1 hides `MCI_radial_loader_cooldown`",
         value="cooldown = BmAK state / 4 (state 0…4 -> 0.00, 0.25, 0.50, 0.75, 1.00)",
         klass="derived", disposition="map",
         limit="BmAK sends 5 categorical states (Ready / Blank / PreReady*), JC3 takes a fraction: "
               "the division by 4 is the only monotone map between the two domains, and its "
               "direction is a Q check, not a file fact",
         verify="Q-3 #3: the loader ring fills 0 -> full between shots and is hidden at rest "
                "(`weapon_cooldown = -1`)",
         proof=[("cooldown.rot_degrees", 360)]),
    dict(id="T-HUD17", element="Vulcan heat",
         bmak_module="HudModuleBatmobile",
         bmak_setters=[],
         jc3="none: `params_with_heat` empty and `body_mentions` 0 - no vehicle-weapon argument or "
             "body mentions heat (the movie's own heat code is the 11-state police wanted level)",
         value="named omission",
         klass="decoded", disposition="out (stated absence both sides)",
         limit="BmAK's heat is `HeatBarStart`/`HeatBarSize` on `Batmobile_Cannon_V2`, a weapon-entity "
               "script field with no `UC_*` setter (0 of 252 setters name heat); JC3 shows ammo, a "
               "cooldown loader and an overcharge tint, never a heat bar",
         verify="n/a - nothing to observe",
         proof=[("heat.params_with_heat", []), ("heat.body_mentions", 0)]),
    dict(id="T-HUD18", element="missile lock",
         bmak_module="HudModuleTargets",
         bmak_setters=["UC_SetBatmobileWeapon"],
         jc3="`POI_TYPE_LOCK_ON_TARGET = 21` -> `MCI_lock_on.MCI_reticle`, rotated 360 deg every "
             "1.5 s (`LOCK_ON_TARGET_ROTATION_TIME`), no progress bar",
         value="one rotating marker on the locked target",
         klass="decoded", disposition="partial",
         limit="the marker has no file link from an `AutoAim` tune to the POI (0 `CreatePoi` calls "
               "of type 21 in the movie), so who paints it stays UNKNOWN (G2-25 §5)",
         verify="Q-3 #3: the marker appears on the locked vehicle and rotates",
         proof=[("lockon.lock_on_type", 21), ("lockon.lock_on_rotation_time", 1.5)]),
    dict(id="T-HUD19", element="missile lock",
         bmak_module="HudModuleTargets",
         bmak_setters=["UC_SetBatmobileWeaponHit", "UC_SetBatmobileWeaponFailure"],
         jc3="none for the target-kind family; `MCI_safe_area_bottom_middle.MCI_missile_locked` "
             "flashes every 0.5 s - that is the *incoming* warning, a different instrument",
         value="named omission (6 kinds: Invalid, bomb, emp, friend, multi, plain)",
         klass="decoded", disposition="out",
         limit="JC3 ships one lock-on icon and one incoming warning; the missile-box family, the "
               "aim box, per-target health and the hit/failure events have no JC3 element (G2-25 §7)",
         verify="n/a",
         proof=[("bmak.missile_target_kinds", 6)]),
    dict(id="T-HUD20", element="weapon slots",
         bmak_module="HudModuleBatmobile",
         bmak_setters=["UC_SetWeaponFeedback"],
         jc3="`InitVehicleWeapons(infiniteAmmo = true)` hides the ammo counters and shows "
             "`MCI_inventory_infinity`",
         value="infiniteAmmo = true",
         klass="derived", disposition="map",
         limit="BmAK's Batmobile weapon HUD has no ammo setter (0 of the 37 setter names carry "
               "ammo/magazine), so there is no count to carry across",
         verify="Q-3 #3: no ammo counter appears in either slot",
         proof=[("init.params", "infiniteAmmo")]),
]


def _rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def _load():
    bmak = json.load(open(HUD_IFACE, encoding="utf-8"))
    jc3 = json.load(open(JC3_HUD, encoding="utf-8"))
    t7 = json.load(open(T7_EDITS, encoding="utf-8"))
    return bmak, jc3, t7


def _setter(bmak, module, name):
    for s in bmak.get(module, {}).get("setters", []):
        if s["name"] == name:
            return s
    return None


def _path(obj, dotted):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return KeyError(part)
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            return KeyError(part)
    return cur


def _eval_proof(jc3, path, expected):
    got = _path(jc3, path)
    if isinstance(got, KeyError):
        return False, f"path {path} missing"
    if isinstance(expected, list):
        # a list proof is "every listed member is present" (icons: ids; heat: empty)
        if not expected:
            return (got == []), f"{path} = {got!r}"
        want = set(expected)
        have = set(got) if isinstance(got, list) else set()
        return want <= have, f"{path} misses {sorted(want - have)}" if not want <= have \
            else f"{path} holds {sorted(want)}"
    if path.endswith(".params"):
        names = [p["name"] for p in got] if isinstance(got, list) else []
        return expected in names, f"{path} has {expected}: {expected in names}"
    if path.endswith(".shapes"):
        return expected in got, f"{path}[{expected}] = {got.get(expected) if isinstance(got, dict) else None}"
    if path.endswith(".missile_target_kinds"):
        return (isinstance(got, list) and len(got) == expected), f"{len(got) if isinstance(got, list) else '?'} kinds"
    return got == expected, f"{path} = {got!r} (want {expected!r})"


def build():
    bmak, jc3, t7 = _load()
    problems = []
    rows = []
    for spec in ROWS:
        setters = []
        for name in spec["bmak_setters"]:
            s = _setter(bmak, spec["bmak_module"], name)
            if s is None:
                problems.append(f"FAIL {spec['id']}: BmAK setter {spec['bmak_module']}.{name} is not in "
                                f"HUD_INTERFACES.json")
            else:
                setters.append(f"`{name}({s['args']})`" if s["args"] else f"`{name}()`")
        proofs = []
        for path, expected in spec["proof"]:
            ok, note = _eval_proof(jc3, path, expected)
            proofs.append({"path": path, "expected": expected, "ok": ok, "note": note})
            if not ok:
                problems.append(f"FAIL {spec['id']}: proof {path} does not hold - {note}")
        rows.append({
            "id": spec["id"], "element": spec["element"],
            "bmak": f"`{spec['bmak_module']}`: " + (", ".join(setters) if setters else
                                                   "no setter (the element is not an interface)"),
            "jc3": spec["jc3"], "value": spec["value"], "class": spec["klass"],
            "disposition": spec["disposition"], "limit": spec["limit"], "verify": spec["verify"],
            "proofs": proofs,
        })

    # every G2-25 element covered, and the coverage is what the card lists
    covered = {r["element"] for r in rows}
    for e in ELEMENTS:
        if e not in covered:
            problems.append(f"FAIL G2-25 element '{e}' has no row")
    wpn12 = [w["element"] for w in jc3.get("wpn12", [])]
    for e in wpn12:
        if e not in covered:
            problems.append(f"FAIL G2-25 wpn12 element '{e}' has no row")

    # T-11: the slot binding the two clips will show
    structural = t7.get("structural", [])
    bindings = [s["what"] for s in structural if "main_weapon" in s["what"] or "00568A74" in s["what"]]
    if len(bindings) < 2:
        problems.append(f"FAIL T-11 structural slots: expected 2 driver-slot bindings, found "
                        f"{len(bindings)}")

    doc = open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    kept = {}
    for m in re.finditer(r"^\| (T-HUD\d+) \|(.*)$", doc, re.M):
        rid = m.group(1)
        if rid in ("T-HUD1", "T-HUD2", "T-HUD3"):
            kept[rid] = m.group(2)
    for rid in ("T-HUD1", "T-HUD2", "T-HUD3"):
        if rid not in kept:
            problems.append(f"FAIL keep: {rid} is not in §1 of T6_HUD_CAMERA.md")
    t5 = re.search(r"^\| T-HUD5 \|(.*)$", doc, re.M)
    if t5 is None:
        problems.append("FAIL T-HUD5's original row is gone from §1")
    elif "blocked" not in t5.group(1):
        problems.append("FAIL T-HUD5's original row no longer records the pre-T-19 blocked state")

    payload = {
        "card": "T-19",
        "schema": 1,
        "sources": {"bmak_hud": _rel(HUD_IFACE), "jc3_hud": _rel(JC3_HUD),
                    "weapons": _rel(T7_EDITS), "doc": _rel(DOC)},
        "counts": {
            "rows": len(rows),
            "elements": len(covered),
            "mapped": sum(1 for r in rows if r["disposition"].startswith("map")),
            "partial": sum(1 for r in rows if r["disposition"].startswith("partial")),
            "out": sum(1 for r in rows if r["disposition"].startswith("out")),
            "proofs": sum(len(r["proofs"]) for r in rows),
            "kept": len(kept),
        },
        "slot_bindings": bindings,
        "rows": rows,
        "kept": sorted(kept),
    }
    return payload, problems


def render(payload):
    c = payload["counts"]
    L = []
    A = L.append
    A(BEGIN)
    A("### 1a. T-HUD5 completed - one row per HUD element (T-19, generated)")
    A("")
    A("T-HUD5 above is the pre-T-19 record: *\"the HUD supports it, the entity still has no weapon")
    A("component\"*. T-11 has since bound the weapons, so the one blocked row is split here into one")
    A("row per element, each cell quoted from a file:")
    A("`HUD_INTERFACES.json` (the BmAK setter **and its argument signature**), the G2-25 json (the")
    A("JC3 member, the icon ids, the one lock-on POI, and the two zeros that prove the heat bar is")
    A("absent on both sides) and `t7_weapons_edits.json` (which weapon the two clips actually show:"
      " the cannon on `main_weapon`, the Vulcan on root `id:00568A74`).")
    A("")
    A(f"{c['rows']} rows over {c['elements']}/5 G2-25 elements: **{c['mapped']} map**, "
      f"**{c['partial']} partial**, **{c['out']} out** (stated absence). Every row carries a proof")
    A(f"that `t19_hud.py --check` re-evaluates ({c['proofs']} proofs); a `map` with no member behind")
    A("it fails the check. T-HUD1…3 (HUD-1: speed, nitro, health) stay as they are - **kept**, not")
    A("rewritten - and the check asserts they are still in the table above.")
    A("")
    A("| # | element (G2-25) | BmAK source (interface) | JC3 element (decoded) | value / transform | "
      "class | now | proposed | verify |")
    A("|---|---|---|---|---|---|---|---|---|")
    for r in payload["rows"]:
        A(f"| {r['id']} | {r['element']} | {r['bmak']} | {r['jc3']} | {r['value']} | {r['class']} | "
          f"{r['disposition']} | {r['limit']} | {r['verify']} |")
    A("")
    A("**Proofs.** Each line is re-evaluated by `--check` against `Research/JC3Grab/JC3_HUD_WEAPONS.json`:")
    A("")
    A("| row | proof | what it means |")
    A("|---|---|---|")
    for r in payload["rows"]:
        for p in r["proofs"]:
            A(f"| {r['id']} | `{p['path']}` {p['note']} | {'holds' if p['ok'] else '**FAILS**'} |")
    A("")
    A("**Where the boundary is.** Two elements cannot be finished from the files and are recorded as")
    A("such rather than filled: the **heat bar** is absent on both sides (0 JC3 arguments, 0 body")
    A("mentions, 0 of 252 BmAK setters), and the **lock-on** is one marker whose painter is native")
    A("(0 `CreatePoi` calls of type 21). The Vulcan accuracy frame -> `reticle_size` scale is UNKNOWN")
    A("for the same reason: the member exists, the unit does not. Slot capacity (D-7's 11 weapons)")
    A("stays T-11's blocked row - this table only says what the HUD can draw: two clips.")
    A("")
    A(END)
    return "\n".join(L)


def splice(doc, block):
    """Replace the marked block, or insert it before the §1 closing paragraph on first run."""
    if BEGIN in doc and END in doc:
        head = doc.split(BEGIN, 1)[0]
        tail = doc.split(END, 1)[1]
        return head + block + tail
    if ANCHOR not in doc:
        raise SystemExit(f"anchor paragraph not found in {_rel(DOC)}: {ANCHOR}")
    head, tail = doc.split(ANCHOR, 1)
    return head + block + "\n\n" + ANCHOR + tail


def write():
    payload, problems = build()
    doc = open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    new = splice(doc, render(payload))
    with open(DOC, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    with open(JS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
        f.write("\n")
    summary(payload)
    for p in problems:
        print(p)
    print(f"doc -> {_rel(DOC)}")
    print(f"json -> {_rel(JS)}")
    return 1 if problems else 0


def summary(payload):
    c = payload["counts"]
    print(f"rows {c['rows']} over {c['elements']}/5 elements | map {c['mapped']} partial "
          f"{c['partial']} out {c['out']} | proofs {c['proofs']} | kept T-HUD1..3 {c['kept']}/3")


def check():
    payload, problems = build()
    doc = open(DOC, encoding="utf-8", newline="").read().replace("\r\n", "\n")
    if BEGIN not in doc or END not in doc:
        problems.append(f"FAIL {_rel(DOC)}: the T19 block markers are missing")
    else:
        got = doc.split(BEGIN, 1)[1].split(END, 1)[0]
        want = render(payload).split(BEGIN, 1)[1].split(END, 1)[0]
        if got != want:
            problems.append(f"FAIL {_rel(DOC)} stale: the regenerated block differs")
    if not os.path.exists(JS):
        problems.append(f"{_rel(JS)} missing")
    else:
        disk = json.load(open(JS, encoding="utf-8"))
        if disk != json.loads(json.dumps(payload)):
            problems.append(f"FAIL {_rel(JS)} stale: the payload differs")
    c = payload["counts"]
    if c["elements"] != 5:
        problems.append(f"FAIL {c['elements']}/5 G2-25 elements covered")
    if c["rows"] < 10:
        problems.append(f"FAIL only {c['rows']} rows: T-HUD5 needs one row per element and per member")
    for r in payload["rows"]:
        if not r["disposition"].startswith(("map", "partial", "out")):
            problems.append(f"FAIL {r['id']}: disposition {r['disposition']} is not map/partial/out")
        if not r["proofs"]:
            problems.append(f"FAIL {r['id']}: no proof")
        if any(not p["ok"] for p in r["proofs"]):
            problems.append(f"FAIL {r['id']}: a proof does not hold")

    summary(payload)
    stale_doc = any("stale: the regenerated block" in p for p in problems)
    stale_js = any(".json stale" in p for p in problems)
    print(f"doc match {not stale_doc}, json match {not stale_js}")
    if problems:
        for p in problems:
            print(p)
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


def show(rid):
    payload, _ = build()
    for r in payload["rows"]:
        if r["id"].lower() == rid.lower():
            print(json.dumps(r, indent=1, ensure_ascii=False))
            return 0
    raise SystemExit(f"no row {rid}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--show", metavar="ROW")
    a = ap.parse_args()
    if a.write:
        sys.exit(write())
    if a.check:
        sys.exit(check())
    sys.exit(show(a.show))


if __name__ == "__main__":
    main()
