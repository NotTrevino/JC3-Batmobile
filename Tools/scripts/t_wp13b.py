#!/usr/bin/env python3
"""T-WP13b - how many driver weapons a JC3 vehicle entity can carry.

Static only.  Reads, never writes, the decoded research artefacts:

  Research/JC3Grab/WEAPON_WIRING.jsonl   per-entity root slots (G2-11)
  Research/JC3Grab/INPUT.json            shipped keymap actions + scopes (G3-08)
  Research/JC3Grab/JC3_HUD_WEAPONS.json  the two HUD weapon clips (HUD-2)
  Research/JC3Grab/TETHER.json           tether + winch census (G2-34)
  Research/BatmobileGrab/DRIVINGMODE.json  BmAK DrivingMode bodies + bindings
  Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md  BmAK menu labels (MENU LABEL source)

Output: Working/Translation/T_WP13B.md

    python Tools/scripts/t_wp13b.py --write
    python Tools/scripts/t_wp13b.py --check
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
J = ROOT / "Research" / "JC3Grab"
B = ROOT / "Research" / "BatmobileGrab"
OUT = ROOT / "Working" / "Translation" / "T_WP13B.md"

SCHEMA = "t-wp13b/1"
SPARE_POINTERS = ["id:8580BA42", "id:CA86AA17"]

# The 11 BmAK weapons.  label is the BmAK menu text where one exists; the
# script proves every label it cites is present in the transcribed menu.
WEAPONS = [
    dict(id="WPN-1", name="Heavy Cannon", mode="battle", button="RT",
         label="60mm Cannon", slot="`main_weapon` (id:851CAABE)",
         verdict="decoded", why="the medium tank binds `w602_mediumtank_canon` to this root property (G2-11); the menu calls RT's gun the 60mm cannon, so the WPN id and the menu name differ"),
    dict(id="WPN-2", name="Vulcan chain gun", mode="battle", button="RB",
         label="Vulcan Gun", slot="second driver slot (`id:00568A74`)",
         verdict="decoded", why="`w603_mediumtank_mgun` sits on the second driver property; the only land chassis with both driver slots bound"),
    dict(id="WPN-3", name="Missile launcher", mode="battle", button="X",
         label="Missile Barrage", slot="spare `id:8580BA42`, or shared with the second driver slot by mode",
         verdict="derived", why="lock-on/homing is T-WP3b's card (7138); here only placement - JC3 has no third decoded driver property and the spare pointers are null on every armed root"),
    dict(id="WPN-4", name="EMP missile", mode="battle", button="B",
         label="EMP", slot="shares WPN-3's position",
         verdict="UNKNOWN", why="one menu button (B) carries EMP; whether the EMP missile and the EMP burst are one object or two is T-WP3b's card"),
    dict(id="WPN-5", name="EMP burst", mode="battle", button="B",
         label="EMP", slot="no weapon slot - entity pulse object",
         verdict="decoded", why="`CForcePulse` is an entity object (G2-16), not a root slot; the menu gives it no separate button"),
    dict(id="WPN-6", name="Power winch", mode="battle", button="d-pad RIGHT",
         label="Mission Select", slot="no weapon slot - rope tether + `transport_rope_winch` parts",
         verdict="decoded", why="operator decision 2026-11-05 takes d-pad RIGHT, displacing the menu's Mission Select arm; the winch borrows Rico's tether, see section 7"),
    dict(id="WPN-7", name="Drone hacker", mode="battle", button="Y",
         label="Drone Virus", slot="none decoded",
         verdict="UNKNOWN", why="no allegiance-switch class in the fleet; owned by G3-08d (7137), placed here only"),
    dict(id="WPN-8", name="Seismic sonar", mode="battle", button="d-pad",
         label="Scan", slot="none decoded",
         verdict="UNKNOWN", why="no sonar class in the fleet; Scan sits on a d-pad arm whose position is read from leader lines, not certain"),
    dict(id="WPN-9", name="Vehicle tracker", mode="pursuit", button="B",
         label="Tracker / Immobilizer", slot="none decoded",
         verdict="UNKNOWN", why="no tracker class in the fleet; pursuit B is a different weapon from battle B on the same physical button"),
    dict(id="WPN-10", name="Riot suppressor", mode="pursuit", button="",
         label="", slot="none decoded",
         verdict="UNKNOWN", why="no non-lethal flag in the member space and no menu row, so there is not even a BmAK button to borrow"),
    dict(id="WPN-11", name="Booster", mode="pursuit", button="Y",
         label="Afterburner", slot="no weapon slot - `arcade.nitro_boost` module block",
         verdict="decoded", why="the boost is a module block on 145 of 232 vehicle graphs, not a root slot"),
]


# --------------------------------------------------------------------------- io


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def is_weapon_value(v) -> bool:
    """A slot is bound when its decoded `target` names a weapon object."""
    if isinstance(v, dict) and "target" in v:
        return is_weapon_value(v["target"])
    if isinstance(v, str):
        return bool(v) and v not in ("00000000", "null", "None")
    if isinstance(v, dict):
        return any(is_weapon_value(x) for x in v.values())
    return False


def hist_str(h: dict[int, int]) -> str:
    return ", ".join(f"{k}: {v}" for k, v in sorted(h.items()))


def walk(o, fn, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            fn(path + "/" + str(k), k, v)
            walk(v, fn, path + "/" + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, fn, path + f"[{i}]")


# --------------------------------------------------------------- fleet census


def fleet_census(rows):
    """Every root's `slots` dict, keyed by the property name the file uses."""
    prop_roots: dict[str, int] = {}
    prop_bound: dict[str, int] = {}
    spare_seen = {k: 0 for k in SPARE_POINTERS}
    spare_nonnull = {k: 0 for k in SPARE_POINTERS}
    driver_hist: dict[int, int] = {}
    max_weapons = 0
    carried_no_slot: list[tuple[str, int, int]] = []
    root_total = 0
    roots_with_slots = 0

    for row in rows:
        counts = row.get("counts", {})
        ds = int(counts.get("driver_slots", 0) or 0)
        driver_hist[ds] = driver_hist.get(ds, 0) + 1
        w = int(counts.get("weapons", 0) or 0)
        b = int(counts.get("bound", 0) or 0)
        max_weapons = max(max_weapons, w)
        if w > b:
            carried_no_slot.append((row.get("entity", "?"), w, b))
        for root in row.get("roots", []):
            root_total += 1
            slots = root.get("slots") or {}
            if slots:
                roots_with_slots += 1
            for k, v in slots.items():
                prop_roots[k] = prop_roots.get(k, 0) + 1
                if is_weapon_value(v):
                    prop_bound[k] = prop_bound.get(k, 0) + 1
            others = {}
            walk(root.get("other_pointers") or {}, lambda p, k, v: others.__setitem__(k, v))
            for sp in SPARE_POINTERS:
                if sp in others:
                    spare_seen[sp] += 1
                    if others[sp] not in (None, "00000000", "null"):
                        spare_nonnull[sp] += 1
    return dict(prop_roots=prop_roots, prop_bound=prop_bound, spare_seen=spare_seen,
                spare_nonnull=spare_nonnull, driver_hist=driver_hist,
                max_weapons=max_weapons, carried_no_slot=carried_no_slot,
                root_total=root_total, roots_with_slots=roots_with_slots)


def slot_split(prop_roots):
    """Split the four decoded slots into driver and gunner by name.

    G2-11 recovered gunner slots as `mounted_weapon` / `mounted_weapon_2`; the two
    keys without `mounted` are the driver pair.  The split is asserted as an oracle
    rather than trusted.
    """
    keys = sorted(prop_roots)
    gunner = [k for k in keys if "mounted" in k.lower()]
    driver = [k for k in keys if "mounted" not in k.lower()]
    return driver, gunner


# ---------------------------------------------------------------- BmAK indices


def tok_value(arg: dict):
    tok = str(arg.get("tok", ""))
    if tok == "EX_IntOne":
        return 1
    if tok == "EX_IntZero":
        return 0
    if "value" in arg:
        return arg["value"]
    txt = str(arg.get("text", ""))
    return int(txt) if txt.isdigit() else None


def bmak_indices(dm):
    """command -> sorted indices from the decoded call arguments (QuickGadgetB/X/Y)."""
    out: dict[str, list[int]] = {}
    for fn in dm.get("functions", []):
        short = str(fn.get("path", "")).split(".", 1)[-1]
        for call in fn.get("calls", []):
            if str(call.get("target", "")) not in ("SelectVehicleWeapon", "ReleaseVehicleWeapon"):
                continue
            args = call.get("args") or []
            val = tok_value(args[0]) if args else None
            if val is not None and val not in out.get(short, []):
                out.setdefault(short, []).append(val)
    for k in out:
        out[k].sort()
    return out


def binding_texts(dm):
    """command -> [(button name, raw binding text)]."""
    out: dict[str, list[tuple[str, str]]] = {}
    for cmd, rows in (dm.get("bindings") or {}).items():
        for row in rows:
            text = row.get("text", "")
            m = re.search(r'Name="([^"]+)"', text)
            out.setdefault(cmd, []).append((m.group(1) if m else "?", text))
    return out


def bmak_index_buttons(dm):
    """[(index, button, command)]: one button per weapon index, decoded on both sides."""
    binds = binding_texts(dm)
    pairs: list[tuple[int, str, str]] = []
    for cmd, idxs in bmak_indices(dm).items():
        if cmd.startswith("Release") or cmd.startswith("QuickGadget") is False:
            continue
        for btn, _ in binds.get(cmd, []):
            for i in idxs:
                pairs.append((i, btn, cmd))
    for cmd, rows in binds.items():
        if cmd.startswith("Release"):
            continue  # the release row carries the same binding text under its own key
        for btn, text in rows:
            for m in re.finditer(r"SelectVehicleWeapon (\d+)", text):
                pairs.append((int(m.group(1)), btn, cmd))
    seen, out = set(), []
    for p in sorted(pairs):
        if p[:2] not in seen:
            seen.add(p[:2])
            out.append(p)
    return out


def bmak_select_body_calls_fire(dm) -> bool:
    for fn in dm.get("functions", []):
        if fn.get("path") == "DrivingMode.SelectVehicleWeapon":
            return any(c.get("target") == "RVehicleWeapon.TryToFireWeapon"
                       for c in fn.get("calls", []))
    return False


# ---------------------------------------------------------------- menu labels


def parse_menu(md_path: Path):
    modes: dict[str, list[tuple[str, str]]] = {}
    mode = None
    for line in md_path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            title = m.group(1).lower()
            mode = "battle" if "battle" in title else "pursuit" if "pursuit" in title else None
            if mode:
                modes.setdefault(mode, [])
            continue
        if mode and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 2 and cells[0] and not set(cells[0]) <= set("-: "):
                if cells[0].lower() == "button":
                    continue
                modes[mode].append((cells[0], cells[1]))
    return modes


def label_found(menu, mode, label) -> bool:
    return any(label in cell or label == btn for btn, cell in menu.get(mode, []))


# ------------------------------------------------------------------- JC3 input


def jc3_input(ip):
    return {a: (v.get("gamepad", ""), v.get("keyboard", ""), v.get("scope", ""))
            for a, v in ip["actions"].items()}


def input_switch_actions(actions):
    """Weapon *selectors* (not fire actions), and which are vehicle-scoped."""
    sel = sorted(a for a in actions
                 if "WEAPON" in a and re.search(r"SELECT|NEXT|PREV|SWITCH|CYCLE", a))
    veh = sorted(a for a in sel if actions[a][2] == "land-vehicle")
    return sel, veh


# ---------------------------------------------------------------- winch census


def winch_census(tether):
    w = tether.get("winch", {})
    non_dialogue = tether.get("index", {}).get("tether_non_dialogue", []) or []
    return dict(entities=w.get("entities", 0), part_rows=w.get("part_rows", 0),
                functional=w.get("functional_winch_classes", 0),
                module_types=w.get("module_types", 0),
                bmak=w.get("bmak", ""),
                tether_rows=tether.get("index", {}).get("tether", 0),
                non_dialogue=non_dialogue)


# ------------------------------------------------------------------ document


def build() -> tuple[str, list[tuple[str, bool, str]]]:
    wiring = load_jsonl(J / "WEAPON_WIRING.jsonl")
    ip = json.loads((J / "INPUT.json").read_text(encoding="utf-8"))
    hud = json.loads((J / "JC3_HUD_WEAPONS.json").read_text(encoding="utf-8"))
    tether = json.loads((J / "TETHER.json").read_text(encoding="utf-8"))
    dm = json.loads((B / "DRIVINGMODE.json").read_text(encoding="utf-8"))
    menu = parse_menu(B / "CONTROLS_MENU_SCREENS.md")

    cen = fleet_census(wiring)
    driver_keys, gunner_keys = slot_split(cen["prop_roots"])
    drv_bound = sum(cen["prop_bound"].get(k, 0) for k in driver_keys)
    gun_bound = sum(cen["prop_bound"].get(k, 0) for k in gunner_keys)
    max_driver = max(cen["driver_hist"]) if cen["driver_hist"] else 0
    spare_all_null = all(cen["spare_nonnull"][s] == 0 for s in SPARE_POINTERS)
    armed = len(wiring)

    pairs = bmak_index_buttons(dm)
    indices = sorted({i for i, _, _ in pairs})
    buttons = sorted({b for _, b, _ in pairs})
    fire_body = bmak_select_body_calls_fire(dm)

    actions = jc3_input(ip)
    sel, veh = input_switch_actions(actions)
    winch = winch_census(tether)
    hud_slots = hud["slots"]["count"]
    hud_show = "ShowVehicleSlot" in json.dumps(hud)

    labels_ok = all(label_found(menu, w["mode"], w["label"]) for w in WEAPONS if w["label"])

    oracles: list[tuple[str, bool, str]] = []
    oracles.append(("O1-eleven-weapons", [w["id"] for w in WEAPONS] == [f"WPN-{i}" for i in range(1, 12)],
                    "11 rows WPN-1..WPN-11, none omitted"))
    oracles.append(("O2-four-slots-per-root", len(cen["prop_roots"]) == 4 and
                    all(v == cen["root_total"] for v in cen["prop_roots"].values()) and
                    cen["root_total"] > 0,
                    f"{cen['roots_with_slots']}/{cen['root_total']} roots carry a slots dict; "
                    + ", ".join(f"`{k}` x{v}" for k, v in sorted(cen["prop_roots"].items()))))
    oracles.append(("O3-driver-two-gunner-two", len(driver_keys) == 2 and len(gunner_keys) == 2,
                    f"driver {driver_keys}; gunner {gunner_keys}"))
    oracles.append(("O4-max-two-driver-slots", max_driver == 2,
                    f"driver_slots histogram {hist_str(cen['driver_hist'])}; {armed} armed graphs; max {max_driver}"))
    oracles.append(("O5-spare-pointers-null", spare_all_null,
                    " + ".join(f"`{s}` seen {cen['spare_seen'][s]}, non-null {cen['spare_nonnull'][s]}" for s in SPARE_POINTERS)))
    oracles.append(("O6-carried-but-unbound", len(cen["carried_no_slot"]) >= 1,
                    f"{len(cen['carried_no_slot'])} graph(s) carry a weapon component with no slot; max components {cen['max_weapons']}"))
    oracles.append(("O7-bmak-four-indices", indices == [1, 2, 3, 4],
                    f"indices {indices} from the QuickGadget bodies plus the d-pad-up binding literal"))
    oracles.append(("O8-bmak-one-button-each", len(buttons) == 4 and len(pairs) == 4,
                    "one button per index: " + ", ".join(f"{i}->{b}" for i, b, _ in pairs)))
    oracles.append(("O9-bmak-index-is-fire", fire_body,
                    "`DrivingMode.SelectVehicleWeapon` calls `RVehicleWeapon.TryToFireWeapon`, so an index is a fire path, not a stored selection"))
    oracles.append(("O10-no-jc3-selector", len(veh) == 0,
                    f"weapon selector actions {sel or 'none'}; land-vehicle scoped {veh or 'none'}"))
    oracles.append(("O11-hud-two-slots", hud_slots == 2 and hud_show,
                    f"HUD slots {hud_slots} (`MCI_vehicle_weapons0/1`); `ShowVehicleSlot` present: {hud_show}"))
    oracles.append(("O12-winch-parts", winch["entities"] > 0 and winch["part_rows"] > 0,
                    f"`transport_rope_winch` on {winch['entities']} entit(ies), {winch['part_rows']} part rows, "
                    f"{winch['functional']} functional winch classes"))
    oracles.append(("O13-menu-labels", labels_ok,
                    "every cited BmAK menu label found in the transcribed screens"))

    L: list[str] = []
    A = L.append
    A("# T-WP13b - can't a vehicle just have multiple weapon slots?")
    A("")
    A(f"Generated by `Tools/scripts/t_wp13b.py --write` (schema `{SCHEMA}`); `--check` rebuilds this")
    A("file from the decoded artefacts and fails on any change. Static only: no game process was")
    A("started, no install was touched, no git, and no other task's files were edited.")
    A("")
    A("Second pass on the 11-weapon question. The first pass (`T_WP13_PROPOSAL.md`) answered")
    A("\"2 bound slots, a third index with no member\" and hung WPN-3/WPN-4 on that index. It measured")
    A("the two *bound* driver pointers and stopped there; it also called `SelectVehicleWeapon` a")
    A("selector, which the decoded body contradicts.")
    A("")
    A("## 0. Answer")
    A("")
    A("**Yes - the entity carries four slot properties and two spare object pointers, and the fleet")
    A("already ships weapons no slot points at. What JC3 limits is not the slot count but the number")
    A("of *fire paths*: two.**")
    A("")
    A(f"- Root slots, all four on every one of the {cen['root_total']} fleet roots:")
    A("  " + ", ".join(f"`{k}` x{v}" for k, v in sorted(cen["prop_roots"].items())) + ".")
    A(f"  Driver-fired: **2** ({', '.join('`'+k+'`' for k in driver_keys)}), {drv_bound} bound pointers")
    A(f"  across {armed} armed graphs. Gunner seats own the other two ({gun_bound} bound).")
    A(f"- Each root also holds two more object pointers, `{'`, `'.join(SPARE_POINTERS)}`: present on")
    A(f"  {cen['spare_seen'][SPARE_POINTERS[0]]} roots, **non-null on none**. Same class, same root, same object")
    A("  reference shape as a weapon slot - the only decoded place to write a third and fourth")
    A("  driver weapon. Whether the engine fires a weapon behind them is **UNKNOWN**.")
    A(f"- Weapons without a slot already ship: max **{cen['max_weapons']}** weapon components on one entity, and")
    A(f"  {len(cen['carried_no_slot'])} graph(s) carry a component no slot points at. Three weapons on a vehicle")
    A("  is normal engine data; *firing* the third from the driver seat is the missing member.")
    A("- BmAK's own car does not use a switchable pair. `DrivingMode.SelectVehicleWeapon` is a **fire**")
    A("  body (`RVehicleWeapon.TryToFireWeapon` twice), and BmAK addresses **four** indices, one")
    A("  button each: " + ", ".join(f"{i} -> `{b}`" for i, b, _ in pairs) + ".")
    A("  So BmAK's model is \"N slots, one button each\"; JC3's primary/secondary pair is the borrowed")
    A("  thing to amend, not a ceiling. Under the operator's 2026-11-05 rule (BmAK buttons win inside")
    A("  the car) the amendment is legitimate: add fire paths, do not wait for a JC3 switch.")
    A("")
    A("Against the 11 weapons: **2 decoded slot carriers** (WPN-1, WPN-2), **2 spare pointers** that")
    A("can hold WPN-3/WPN-4 if the engine test passes, **slot sharing by mode** for the rest - which")
    A("is precisely how BmAK behaves (B is EMP in battle, Tracker in pursuit) - and **3 decoded")
    A("absences** that need no slot at all (WPN-5 entity pulse, WPN-6 tether, WPN-11 nitro block).")
    A("")
    A("## 1. The four slot properties and who fires them")
    A("")
    A("| slot property | seat | roots carrying | roots bound |")
    A("|---|---|---:|---:|")
    for k in driver_keys:
        A(f"| `{k}` | driver | {cen['prop_roots'][k]} | {cen['prop_bound'].get(k, 0)} |")
    for k in gunner_keys:
        A(f"| `{k}` | gunner | {cen['prop_roots'][k]} | {cen['prop_bound'].get(k, 0)} |")
    A("")
    A("This is the operator's question answered on the first pass's own list: of `main_weapon`,")
    A("`mounted_weapon`, `mounted_weapon_2` and `secondary (id:00568A74)`, **two are driver-fired and")
    A("two belong to a gunner seat**. `mounted_weapon` sits on `interaction.seat.gunner1` with state")
    A("`S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON`, so the engine fires it only while a pawn holds that")
    A("seat. Whether a driver can fire a gunner slot with nobody in it has no decoded answer.")
    A("")
    A(f"Driver slots per armed graph: {{{hist_str(cen['driver_hist'])}}} - max {max_driver}; no fleet vehicle has three.")
    A("")
    A("## 2. The spare pointers - the amendment path")
    A("")
    A("| pointer | roots carrying it | non-null |")
    A("|---|---:|---:|")
    for sp in SPARE_POINTERS:
        A(f"| `{sp}` | {cen['spare_seen'][sp]} | {cen['spare_nonnull'][sp]} |")
    A("")
    A("They are not decoration: properties of the same `.epe` root class as the weapon slots, holding")
    A("the same kind of object reference. Three readings remain, and the files separate none:")
    A("")
    A("1. unused weapon slots the engine would fire if pointed at a weapon;")
    A("2. pointers for non-weapon objects (lights, damage FX) that happen to be null here;")
    A("3. retired properties nothing reads.")
    A("")
    A("**UNKNOWN**, and it is a 5-minute experiment rather than a 500-line implementation: point")
    A("`id:8580BA42` at a copy of `w602_mediumtank_canon` on the medium tank and see whether a third")
    A("driver weapon fires. Until then WPN-3/WPN-4 are *candidate* carriers only.")
    A("")
    A("## 3. Weapons a vehicle already carries without a slot")
    A("")
    A("| entity | components | bound | carried, unbound |")
    A("|---|---:|---:|---:|")
    for ent, w, b in cen["carried_no_slot"][:8]:
        A(f"| `{Path(ent).name}` | {w} | {b} | {w - b} |")
    A("")
    A("The fighter jet and fighter-bomber each ship a third weapon object with no slot, and the")
    A("monorail missile car ships `w614_monorailmissilecar_missile` with **zero** bound slots. A")
    A("modded extra weapon lands in exactly that state unless a pointer *and* a fire action reach it -")
    A("which is why the second half of this card is about fire paths, not counts.")
    A("")
    A("## 4. What could switch between them")
    A("")
    A("### 4a. BmAK's own model (decoded)")
    A("")
    A("| index | button | command |")
    A("|---|---|---|")
    for i, btn, cmd in pairs:
        A(f"| {i} | `{btn}` | `{cmd}` |")
    A("")
    A("**An index is a fire path, not a selection.** `DrivingMode.SelectVehicleWeapon` (export")
    A("104971) calls `ReadyToFire()`, `IsFiring()`, `RVehicleWeapon.TryToFireWeapon()` twice, and")
    A("raises `RSeqEvent_BatmobileRiddlerButton`; `QuickGadgetB/X/Y` forward the literals 1/2/3 and")
    A("d-pad up binds literal 4. No decoded body stores an active-slot variable. Press a button, the")
    A("car fires that button's weapon - that is the model JC3 has to be given.")
    A("")
    A("### 4b. JC3's shipped input table")
    A("")
    A("| action | gamepad | keyboard | scope |")
    A("|---|---|---|---|")
    for a in ["FIRE_VEHICLE_WEAPON_PRIMARY", "FIRE_VEHICLE_WEAPON_SECONDARY",
              "NEXT_WEAPON", "PREV_WEAPON", "USE_VEHICLE_MOD", "VEHICLE_RELEASE_GRAPPLE",
              "FIRE_GRAPPLE"]:
        g, k, s = actions.get(a, ("-", "-", "-"))
        A(f"| `{a}` | {g or '-'} | {k or '-'} | {s or '-'} |")
    A("")
    A(f"Weapon *selector* actions in the shipped keymaps: {', '.join('`'+a+'`' for a in sel) or 'none'}.")
    A(f"`land-vehicle` scoped: **{len(veh) or 'none'}**. `NEXT_WEAPON`/`PREV_WEAPON` are keyboard-only and")
    A("`on-foot`, so nothing shipped lets a driver cycle or select a slot. The vehicle-scope buttons")
    A("still free are `USE_VEHICLE_MOD` (d-pad right - now the winch) and `VEHICLE_RELEASE_GRAPPLE`")
    A("(d-pad down).")
    A("")
    A("**Consequence.** Do not add a switch; add *fire paths*, one button per weapon, exactly as BmAK")
    A("does. The two HUD clips and two fire actions are then what must be extended - not the slot")
    A("count, which the entity already exceeds.")
    A("")
    A("## 5. The 11 weapons")
    A("")
    A("| BmAK weapon | menu label (button, mode) | candidate JC3 carrier | status |")
    A("|---|---|---|---|")
    for w in WEAPONS:
        if w["label"]:
            cell = f"{w['label']} ({w['button']}, {w['mode']})"
        elif w["button"]:
            cell = f"no menu row (new binding {w['button']})"
        else:
            cell = "**no menu row, no button**"
        A(f"| **{w['id']}** {w['name']} | {cell} | {w['slot']} - {w['why']} | **{w['verdict']}** |")
    A("")
    A("Label/id mismatches are recorded, not smoothed over:")
    A("")
    A("- **60mm Cannon vs WPN-1 Heavy Cannon** - one gun, two names; WPN-1 keeps the slot either way.")
    A("- **EMP (B) vs WPN-4 + WPN-5** - one menu button, two WPN ids. Either the burst is the missile's")
    A("  effect (one object) or BmAK has two objects on one button; T-WP3b owns EMP homing.")
    A("- **B in two modes** - `EMP` in battle, `Tracker / Immobilizer` in pursuit, same physical")
    A("  button: direct evidence that BmAK reuses one slot across modes.")
    A("- **No menu item lacks a WPN id**, but **WPN-10 Riot suppressor has no menu item** - the only")
    A("  weapon with neither a button nor a slot.")
    A("")
    A("## 6. Placement that keeps BmAK behaviour")
    A("")
    A("| JC3 position | holds | status |")
    A("|---|---|---|")
    A("| `main_weapon` | WPN-1 Heavy Cannon (60mm) | decoded |")
    A("| second driver slot | WPN-2 Vulcan chain gun | decoded |")
    A("| `id:8580BA42` (spare) | WPN-3 Missile launcher, or shared with WPN-2 per mode | UNKNOWN until the engine test |")
    A("| `id:CA86AA17` (spare) | WPN-4 EMP missile, or shared with WPN-3 | UNKNOWN until the engine test |")
    A("| shared position | WPN-9 tracker (pursuit) / WPN-8 sonar (battle) | derived - mode swap |")
    A("| no slot | WPN-5 EMP burst (entity pulse), WPN-11 Booster (nitro block) | decoded |")
    A("| d-pad RIGHT, no slot | WPN-6 Power winch (section 7) | decoded parts, runtime borrowed |")
    A("| no carrier | WPN-7 Drone hacker (7137 owns it), WPN-10 Riot suppressor | UNKNOWN |")
    A("")
    A("**Slot sharing is the fallback if the spares do not fire**, and it is BmAK's own behaviour: one")
    A("slot, the active mode's weapon, swapped when `TryToChangeMode` runs (BattleMode/PursuitMode")
    A("payloads 5269/61474 are decoded). All 11 ids stay reachable with two pointers that way; the")
    A("status is derived, not decoded.")
    A("")
    A("## 7. The Power Winch on d-pad RIGHT, borrowed from the grapple")
    A("")
    A(f"Tether census (`TETHER.json`): **{winch['tether_rows']}** file-index rows match tether, "
      f"{len(winch['non_dialogue'])} of them")
    A("non-dialogue, and `transport_rope_winch` is present on")
    A(f"**{winch['entities']}** vehicle entit(ies) over **{winch['part_rows']}** part rows, with "
      f"**{winch['functional']}** functional winch")
    A("classes. The non-dialogue tether rows, all of them:")
    A("")
    for p in winch["non_dialogue"]:
        A(f"- `{p}`")
    A("")
    A("What the borrow needs:")
    A("")
    A("| need | JC3 member | evidence |")
    A("|---|---|---|")
    A("| fire while driving | `FIRE_GRAPPLE` = LSHOULDER, no scope | INPUT.json |")
    A("| push / release on foot | `PUSH_GRAPPLE`, `RELEASE_GRAPPLE` = d-pad RIGHT, on-foot | INPUT.json |")
    A("| release while driving | `VEHICLE_RELEASE_GRAPPLE` = d-pad DOWN, land-vehicle | INPUT.json |")
    A("| the winch's own button | d-pad RIGHT, ships as `USE_VEHICLE_MOD` (turbo jump) | INPUT.json + operator decision |")
    A("| rope geometry | `transport_rope_winch` parts, 4 entities, 40 part rows | TETHER.json |")
    A("| tether runtime | character-side; tether strings sit in graphs/textures/audio, not vehicle entity classes | TETHER.json index |")
    A("")
    A("So the **button** is free under the priority rule, the **geometry** exists on a fleet vehicle,")
    A("and the **runtime** is Rico's grapple, which the vehicle graphs do not carry. A vehicle-to-object")
    A("tether still needs vehicle-side attach/reel/release members, and those are **UNKNOWN**: no rope")
    A("class, no attach-point list, no tether state in the decoded vehicle members. The one member")
    A("that proves vehicles consume tether state is `VEHICLE_RELEASE_GRAPPLE` - and it sits on d-pad")
    A("down, already shared with `STUNT_JUMP`/`OPEN_PARACHUTE` in the shipped layout.")
    A("")
    A("Note the BmAK side is not a match target: MODLOG section 86/87 records `RBatmobileWinch`")
    A(f"yielding \"at best a force, never a mass\", and this repo's tether census agrees - {winch['functional']}")
    A("functional winch classes fleet-wide.")
    A("")
    A("## 8. What is still UNKNOWN")
    A("")
    A("- **Whether the spare pointers fire a weapon.** Null on every armed root; the reader is native")
    A("  and not in the decoded packages. 5-minute test: point one spare at a copied cannon.")
    A("- **Whether a driver can fire a gunner slot.** `mounted_weapon` is seat-gated; no decoded body")
    A("  fires it without a pawn in `gunner1`.")
    A("- **Which BmAK index is which weapon.** 1-4 decoded, the object behind an index is not")
    A("  (`DRIVINGMODE.md` section 4 gap); the button/index table above is derived.")
    A("- **How JC3 adds a third fire path.** `TryToFireWeapon` has 0 rows in `INDEX.jsonl` - JC3's")
    A("  per-weapon fire is native, so there is no decoded script to extend from two to N.")
    A("- **The winch's vehicle-side attach/reel/release members** (section 7).")
    A("- **WPN-10 Riot suppressor**: no menu row, no member, no button. Needs an operator decision or")
    A("  a BmAK control that this pass could not find.")
    A("")
    A("## 9. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for name, ok, why in oracles:
        A(f"| `{name}` | {'PASS' if ok else 'FAIL'} | {why} |")
    A("")
    A("## 10. Reproduce")
    A("")
    A("```")
    A("python Tools/scripts/t_wp13b.py --write")
    A("python Tools/scripts/t_wp13b.py --check")
    A("```")
    A("")
    A("Read-only inputs: `WEAPON_WIRING.jsonl`, `INPUT.json`, `JC3_HUD_WEAPONS.json`, `TETHER.json`,")
    A("`DRIVINGMODE.json`, `CONTROLS_MENU_SCREENS.md`.")
    A("")
    return "\n".join(L), oracles


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "--check"
    if mode not in ("--write", "--check"):
        print("usage: t_wp13b.py [--write|--check]", file=sys.stderr)
        return 2
    text, oracles = build()
    failed = [n for n, ok, _ in oracles if not ok]
    if mode == "--write":
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text, encoding="utf-8")
        print(f"wrote {OUT.relative_to(ROOT)} ({len(text.splitlines())} lines)")
        print(f"oracles {len(oracles) - len(failed)}/{len(oracles)} pass")
        if failed:
            print("FAILED: " + ", ".join(failed) + "\n" + "\n".join(
                f"  {n}: {why}" for n, ok, why in oracles if not ok), file=sys.stderr)
            return 1
        return 0
    if not OUT.exists():
        print(f"missing {OUT.relative_to(ROOT)} - run --write", file=sys.stderr)
        return 1
    on_disk = OUT.read_text(encoding="utf-8")
    if on_disk != text:
        print("CHECK FAIL: document differs from a fresh rebuild", file=sys.stderr)
        for i, (a, b) in enumerate(zip(on_disk.splitlines(), text.splitlines())):
            if a != b:
                print(f"  first diff line {i + 1}:\n   disk: {a[:160]}\n   new : {b[:160]}", file=sys.stderr)
                break
        return 1
    if failed:
        print("CHECK FAIL: " + ", ".join(failed), file=sys.stderr)
        return 1
    print(f"CHECK OK: {len(oracles)} oracles, 11 weapons, 4 slots + 2 spare pointers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
