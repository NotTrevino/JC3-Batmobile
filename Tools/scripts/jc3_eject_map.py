#!/usr/bin/env python3
"""G3-08b: map the BmAK Batmobile eject mechanic onto JC3's hold-A parachute exit.

Read-only. Writes (--write) or re-derives and compares (--check):
  Research/JC3Grab/EJECT_MAP.md

`Research/JC3Grab/INPUT.md` is NOT touched (another card owns it).

Sources, and what each proves
-----------------------------
JC3, re-read on every run:
  * `settings/keymap_gamepad.bin` + `settings/keymap_keyboard.bin`, every mounted copy,
    through the archive index and the project's RTPC keymap reader (`jc3_input`), which
    carries its own byte-accounting oracle.  -> the SHIPPED default binding table.
  * the player's own export `kepmap.txt` (JSON list of {action,key}; no secret in it).
    -> the LIVE binding table, and proof its schema has no hold/duration/context field.
  * `Research/Epe/serpente_civilian.xml`, the donor `.epe` kept as nested XML.
    -> the only vehicle-context condition that exists: the driver exit's speed gate.
  * `rico_base.asb` / `rico_base.afsmb` out of the archives. -> Rico's parachute-exit
    state and clip exist; the engine's eject ACTION is referenced nowhere.
  * the 232 decoded vehicle `.ee` dumps in `$JC3_RAW/entities`. -> byte census, split
    into asset-path hits and member-name hits (a raw substring is not a member).
BmAK, decoded by earlier cards and re-read here:
  * `BmGame/Config/DefaultInput.ini` line 267 -> A = `EjectFromVehicle`.
  * `Research/BatmobileGrab/DRIVINGMODE.json` (BmGame.upk export 104931).
  * `Research/BatmobileGrab/EJECT_VELOCITY.json` (launch call, receiver, special moves).
  * `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md` (menu labels, operator screenshots).

Labels in the output: decoded (file + offset/line), derived (rule + inputs),
operator-stated (the operator's statement, not a file), quoted (a number another card
decoded, not re-read here), UNKNOWN (what was tried, where it would be).

Usage:
  python -I Tools/scripts/jc3_eject_map.py --write
  python -I Tools/scripts/jc3_eject_map.py --check
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jc3_input as J  # noqa: E402  (keymap reader + archive index; nothing runs on import)
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "EJECT_MAP.md")
JC3_RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENTITIES = os.path.join(JC3_RAW, "entities")
BMAK = os.environ.get("BMAK_GAME", r"E:/Games/Batman - Arkham Knight")
DEFAULTINPUT = os.path.join(BMAK, "BmGame", "Config", "DefaultInput.ini")
DONOR = os.path.join(ROOT, "Research", "Epe", "serpente_civilian.xml")
DRIVINGMODE = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVINGMODE.json")
EJECT_VEL = os.path.join(ROOT, "Research", "BatmobileGrab", "EJECT_VELOCITY.json")
MENU = os.path.join(ROOT, "Research", "BatmobileGrab", "CONTROLS_MENU_SCREENS.md")
KEPMAP = os.environ.get(
    "JC3_KEPMAP",
    r"C:/Users/User/Documents/Square Enix/Just Cause 3/Saves/76561197960271872/kepmap.txt")

# Actions this card has to place, in both tables, with the JC3 menu wording where the
# operator's transcription has one.
ACTIONS = ["STUNT_JUMP", "OPEN_PARACHUTE", "JUMP", "ENTER_VEHICLE", "EXIT_VEHICLE",
           "USE_VEHICLE_MOD", "HANDBRAKE", "FIRE_VEHICLE_WEAPON_PRIMARY",
           "FIRE_VEHICLE_WEAPON_SECONDARY", "ACCELERATE", "REVERSE",
           "LOOK_BACK_CAM", "SOUND_HORN_SIREN", "OPEN_WINGSUIT", "GUI_PAUSE",
           "GUI_PDA", "WINGSUIT_TAKEOFF"]

FACE = ["A", "B", "X", "Y"]
SHOULDERS = ["LSHOULDER", "RSHOULDER", "LTRIGGER", "RTRIGGER",
             "LSTICKBUTTON", "RSTICKBUTTON", "START", "BACK", "RPADUP", "RPADDOWN"]

# export suffix -> shipped name (so the two tables can be compared key by key)
ALIAS = {"LTHUMB_PRESS": "LSTICKBUTTON", "RTHUMB_PRESS": "RSTICKBUTTON",
         "LTHUMB_UP": "LSTICKUP", "LTHUMB_DOWN": "LSTICKDOWN",
         "LTHUMB_LEFT": "LSTICKLEFT", "LTHUMB_RIGHT": "LSTICKRIGHT",
         "DPAD_UP": "RPADUP", "DPAD_DOWN": "RPADDOWN",
         "DPAD_LEFT": "RPADLEFT", "DPAD_RIGHT": "RPADRIGHT"}

CENSUS_TERMS = ["eject", "parachute", "bail", "launch", "catapult", "impulse",
                "hold_time", "holdtime", "keymap", "velocity", "nitro"]

RICO_ASB_TERMS = [b"PPparachute_vehicle_eject",
                  b"rico_vehi_car_low_driver_to_parachute.ban",
                  b"PPparachute_opened", b"S_STUNT_EXIT_VEHICLE"]
RICO_AFSMB_TERMS = [b"S_EXIT_VEHICLE_PARA", b"ACT_EXIT_VEHICLE",
                    b"ACT_EJECT_FROM_VEHICLE", b"ACT_STUNT_VEHICLE_EXIT",
                    b"S_EXIT_DRIVER_TO_HOOD_VEHICLE"]


def keyid(inp):
    s = inp.upper().replace("PC_", "")
    if s.startswith("GAMEPAD_"):
        s = s[len("GAMEPAD_"):]
    return ALIAS.get(s, s)


def jhash_hex(text):
    return b"%08X" % (hash_jenkins(text.encode()) & 0xFFFFFFFF)


def invert(pairs):
    """[(key, action)] -> {action: [keys]}"""
    out = {}
    for k, a in pairs:
        out.setdefault(a, []).append(k)
    for v in out.values():
        v.sort()
    return out


# ------------------------------------------------------------------ JC3 keymaps

def keymap():
    """The shipped tables, kept per device (the two bins share key spellings)."""
    rows = J.load_index(J.OUT)
    files, live = [], []
    for path in J.KEYMAPS:
        for r, data in J.read_entries(rows, path):
            bs, acc = J.parse_keymap(path, r, data)
            dev = "gamepad" if "gamepad" in path else "keyboard"
            for b in bs:
                b.update(file=path, mount=r["mount"], device=dev)
            files.append(dict(path=path, mount=r["mount"], archive=r["archive"],
                              entry_offset=r["offset"], **acc))
            live.extend(bs)
    active = {p: max((f["mount"] for f in files if f["path"] == p),
                     key=lambda m: J.MOUNT_RANK[m]) for p in J.KEYMAPS}
    sel = [b for b in live if b["mount"] == active[b["file"]]]
    per_dev = {}
    for dev in ("gamepad", "keyboard"):
        bs = [b for b in sel if b["device"] == dev]
        per_dev[dev] = dict(
            bindings=len(bs),
            by_key={},
            by_action=invert((keyid(b["input"]), b["action"]) for b in bs),
        )
        for b in bs:
            per_dev[dev]["by_key"].setdefault(keyid(b["input"]), []).append(b["action"])
        for v in per_dev[dev]["by_key"].values():
            v.sort()
    return dict(files=files, active=active, live=sel, devs=per_dev)


def kepmap():
    """The player's own export, split by device exactly as the keys are written."""
    with open(KEPMAP, encoding="utf-8", errors="replace") as f:
        rows = json.load(f)
    shapes = {tuple(sorted(r)) for r in rows}
    pairs = [(keyid(r["key"]), r["action"], r["key"]) for r in rows]
    gp = [(k, a) for k, a, raw in pairs if raw.upper().startswith("PC_GAMEPAD_")]
    kb = [(k, a) for k, a, raw in pairs if not raw.upper().startswith("PC_GAMEPAD_")]
    by_key = {}
    for k, a in gp:
        by_key.setdefault(k, []).append(a)
    for v in by_key.values():
        v.sort()
    return dict(path=KEPMAP, rows=rows, shapes=shapes, field_names=sorted({k for r in rows for k in r}),
                gamepad=dict(bindings=len(gp), by_key=by_key, by_action=invert(gp)),
                keyboard=dict(bindings=len(kb), by_action=invert(kb)))


# ------------------------------------------------------------------ donor .epe

def donor():
    tree = ET.parse(DONOR)
    exits = []
    for obj in tree.iter("object"):
        vals = {}
        for v in obj.findall("value"):
            n = v.get("name")
            if n:
                vals[n] = v
        if vals.get("_class") is None or vals["_class"].text != "CInteractionGraphExit":
            continue
        cond = None
        for sub in obj.findall("object"):
            sv = {v.get("name"): v for v in sub.findall("value") if v.get("name")}
            if sv.get("_class") is not None and \
                    sv["_class"].text == "CInteractionGraphParentVelocityCondition":
                cond = (float(sv["min"].text), float(sv["max"].text))
        exits.append(dict(name=vals["name"].text, state=vals["state"].text,
                          enabled=vals["enabled"].text, gate=cond,
                          object_id=obj.get("id"), name_hash=vals["name_hash"].text))
    counts = {}
    for e in exits:
        counts[e["state"]] = counts.get(e["state"], 0) + 1
    return dict(path=DONOR, exits=exits, state_counts=dict(sorted(counts.items())))


# ------------------------------------------------------------------ entity census

def census():
    """Byte census of the 232 vehicle module dumps, split by where the hit lives.

    A raw byte hit is not a member name: these dumps also carry asset paths, so
    `bullet_eject_capstone.effc`, `rpg_launcher/` and `gparachute_to_g*` trip a plain
    substring search.  Every hit is classified by its printable run:
      path   - the run contains '/', i.e. a VFS asset path
      member - no '/', i.e. a member/socket-style name (`crashing_impulse`,
               `launch_rail_l`)
    Only the member class can be an entity member.
    """
    names = sorted(os.listdir(ENTITIES)) if os.path.isdir(ENTITIES) else []
    stats = {t: dict(hits=0, path=0, member=0, files=0) for t in CENSUS_TERMS}
    runs = {t: {} for t in CENSUS_TERMS}
    rxs = {t: re.compile(re.escape(t.encode()), re.I) for t in CENSUS_TERMS}
    for fn in names:
        with open(os.path.join(ENTITIES, fn), "rb") as f:
            blob = f.read()
        for t in CENSUS_TERMS:
            ms = list(rxs[t].finditer(blob))
            if not ms:
                continue
            st = stats[t]
            st["files"] += 1
            for m in ms:
                st["hits"] += 1
                a, b = m.start(), m.end()
                while a > 0 and 32 <= blob[a - 1] < 127:
                    a -= 1
                while b < len(blob) and 32 <= blob[b] < 127:
                    b += 1
                run = blob[a:b].decode("latin-1")
                if "/" in run:
                    st["path"] += 1
                else:
                    st["member"] += 1
                    runs[t][run] = runs[t].get(run, 0) + 1
    return dict(dir=ENTITIES, files=len(names), stats=stats,
                member_runs={t: sorted(v.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
                             for t, v in runs.items()})


# ------------------------------------------------------------------ Rico animation data

def rico():
    rows = J.load_index(J.OUT)
    out = []
    for want, terms in (("rico_base.asb", RICO_ASB_TERMS),
                        ("rico_base.afsmb", RICO_AFSMB_TERMS)):
        cand = [r for r in rows if r["path"].lower().endswith(want)]
        if not cand:
            out.append(dict(name=want, found=False, searched=len(rows), terms=[]))
            continue
        r = max(cand, key=lambda x: J.MOUNT_RANK[x["mount"]])
        with open(os.path.join(J.DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
            f.seek(r["offset"])
            data = f.read(r["size"])
        got = []
        for t in terms:
            plain = data.count(t)
            got.append(dict(term=t.decode(), plaintext=plain,
                            hash_hex=data.count(jhash_hex(t.decode())),
                            first=(data.find(t) if plain else None)))
        out.append(dict(name=want, found=True, path=r["path"], mount=r["mount"],
                        archive=r["archive"], entry_offset=r["offset"],
                        size=len(data), terms=got, searched=len(rows)))
    return out


# ------------------------------------------------------------------ BmAK

def bmak_input():
    with open(DEFAULTINPUT, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    row = None
    for i, ln in enumerate(lines, 1):
        if ln.lstrip(".").startswith("Bindings=") and 'Name="XboxTypeS_A"' in ln:
            row = (i, ln)
    if row is None:
        raise SystemExit("no XboxTypeS_A binding line in DefaultInput.ini")
    lineno, text = row
    cmd = re.search(r'Command="([^"]*)"', text).group(1)
    tokens = [t.strip() for t in cmd.split("|") if t.strip()]
    eject_lines = [i for i, ln in enumerate(lines, 1)
                   if ln.lstrip(".").startswith("Bindings=") and "EjectFromVehicle" in ln]
    return dict(path=DEFAULTINPUT, lineno=lineno, line=text, tokens=tokens,
                eject_binding_lines=eject_lines,
                has_eject="EjectFromVehicle" in tokens,
                has_strafe="BattleStrafe" in tokens)


def drivingmode():
    with open(DRIVINGMODE, encoding="utf-8") as f:
        d = json.load(f)
    ej = [x for x in d["functions"] if x["export"] == 104931][0]
    calls = [dict(at=c["at"], target=c["target"], text=c.get("text")) for c in ej["calls"]]
    at = {}
    for c in calls:
        at[c["target"]] = c["at"]
        at[c["target"].split(".")[-1]] = c["at"]
    refs = [dict(at=r["at"], ref=r["ref"], kind=r["kind"], token=r["token"]) for r in ej["refs"]]
    ref_at = {r["ref"]: r["at"] for r in refs}
    return dict(path=DRIVINGMODE, export=ej["export"], path_name=ej["path"],
                command=ej["command"], script_bytes=ej["script_bytes"],
                unexplained=ej["unexplained_bytes"], calls=calls, at=at, refs=refs,
                ref_at=ref_at,
                boosting_out_ats=[r["at"] for r in refs if r["ref"].endswith("BoostingOut")],
                constants=ej["constants"], package=d.get("package"),
                exports=d.get("exports"), names=d.get("names"), version=d.get("version"))


def eject_velocity():
    with open(EJECT_VEL, encoding="utf-8") as f:
        d = json.load(f)
    vc = d["velocity_call"]
    return dict(path=EJECT_VEL, package=d.get("package"), at=vc["at"], callee=vc["callee"],
                vec=vc["args"][0]["value"], vec_token=vc["args"][0]["kind"],
                bool_kind=vc["args"][1]["kind"], arg_bytes=vc["arg_bytes"],
                receiver_object=vc["receiver_chain"][0]["object"]["ref"],
                receiver_component=vc["receiver_chain"][0]["prop"],
                guard=d["velocity_call_if"],
                special_moves=d["class_defaults"]["special_move_refs"],
                class_default_entries=d["class_defaults"]["count"],
                mode_id_entries=d["class_defaults"]["mode_id_count"],
                launch_sequence=d["launch_sequence"],
                package_sha1=d["package_sha1"], status=d["status"])


def menu():
    with open(MENU, encoding="utf-8", errors="replace") as f:
        text = f.read()
    rows = {}
    for ln in text.splitlines():
        if not ln.startswith("|"):
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells) >= 2:
            rows[cells[0]] = cells[1]
    return dict(path=MENU, rows=rows,
                eject=[k for k in rows if "Eject" in rows[k] or "Eject" in k],
                exit_=[k for k in rows if rows[k] == "Exit Batmobile"])


# ------------------------------------------------------------------ build

def build():
    km = keymap()
    kp = kepmap()
    dn = donor()
    ce = census()
    ri = rico()
    bi = bmak_input()
    dm = drivingmode()
    ev = eject_velocity()
    mn = menu()

    gp = km["devs"]["gamepad"]
    gp_ex = kp["gamepad"]

    def ctl(by_action, action):
        return sorted(by_action.get(action, []))

    # The control that carries BOTH STUNT_JUMP and OPEN_PARACHUTE, in each source.
    def shared(by_action):
        a = set(by_action.get("STUNT_JUMP", []))
        b = set(by_action.get("OPEN_PARACHUTE", []))
        return sorted(a & b)

    shared_shipped = shared(gp["by_action"])
    shared_export = shared(gp_ex["by_action"])
    face_rows = sorted({k for k in gp["by_key"] if k in FACE})
    eject_actions = sorted({a for d in (gp["by_action"], gp_ex["by_action"],
                                       km["devs"]["keyboard"]["by_action"],
                                       kp["keyboard"]["by_action"])
                            for a in d if re.search(r"(?i)eject", a)})

    def ex(name):
        for e in dn["exits"]:
            if e["name"] == name:
                return e
        return None

    para, plain = ex("exit.driver.moving.parachute"), ex("exit.driver.default")
    hood, roll = ex("exit.ai.driver.to.hood"), ex("exit.driver.roll.out")

    order = ["CantEjectFromBatmobile", "CheckSpaceAboveBatmobileCockpit",
             "DriverLeave", "RemoveBatmobileBindsAndSetBatmanBinds",
             "PlayCockpitOpenFast", "SetRBLinearVelocity", "TriggerSpecialMove"]
    order_ats = [dm["at"][t] for t in order if t in dm["at"]]

    launch_members = [r for r, _ in ce["member_runs"]["launch"]]

    checks = [
        ("the SHIPPED gamepad keymap puts STUNT_JUMP and OPEN_PARACHUTE on ONE control",
         len(shared_shipped) == 1,
         f"shared control(s): {shared_shipped}; "
         f"STUNT_JUMP={ctl(gp['by_action'], 'STUNT_JUMP')}, "
         f"OPEN_PARACHUTE={ctl(gp['by_action'], 'OPEN_PARACHUTE')}"),
        ("the player's EXPORT puts the same two actions on ONE control (gamepad A)",
         shared_export == ["A"],
         f"shared control(s): {shared_export}"),
        ("the two sources disagree about which control that is (reported, not merged)",
         shared_shipped != shared_export,
         f"shipped {shared_shipped} vs export {shared_export}"),
        ("the shipped gamepad keymap binds no face button (A/B/X/Y)",
         not face_rows,
         f"face-button rows: {len(face_rows)}; controls present: "
         f"{', '.join(sorted(gp['by_key']))}"),
        ("neither source carries a hold/duration/context field",
         kp["shapes"] == {("action", "key")}
         and set(km["files"][0]["property_types"]) == {"3"},
         f"export field sets {sorted(kp['shapes'])}; shipped property types "
         f"{km['files'][0]['property_types'] if km['files'] else '—'}"),
        ("no action name in any of the four tables mentions EJECT",
         not eject_actions, f"actions matching /EJECT/: {eject_actions}"),
        ("LB (LSHOULDER) is fire-secondary and carries no EXIT/EJECT",
         "FIRE_VEHICLE_WEAPON_SECONDARY" in gp["by_key"].get("LSHOULDER", [])
         and "FIRE_VEHICLE_WEAPON_SECONDARY" in gp_ex["by_key"].get("LSHOULDER", [])
         and not [a for a in gp["by_key"].get("LSHOULDER", []) + gp_ex["by_key"].get("LSHOULDER", [])
                  if re.search(r"(?i)EXIT|EJECT", a)],
         f"shipped {gp['by_key'].get('LSHOULDER')}; export {gp_ex['by_key'].get('LSHOULDER')}"),
        ("the donor's moving driver exit names S_EXIT_VEHICLE_PARA",
         para is not None and para["state"] == "S_EXIT_VEHICLE_PARA",
         f"state {para and para['state']}"),
        ("that exit's only gate is a parent-speed gate 5..999",
         para is not None and para["gate"] == (5.0, 999.0),
         f"gate {para and para['gate']}; plain exit gate {plain and plain['gate']}"),
        ("the donor also carries a driver exit naming the HOOD state",
         hood is not None and hood["state"] == "S_EXIT_DRIVER_TO_HOOD_VEHICLE",
         f"exit.ai.driver.to.hood -> {hood and hood['state']}"),
        ("BmAK A carries EjectFromVehicle, bound on exactly one line",
         bi["has_eject"] and len(bi["eject_binding_lines"]) == 1,
         f"line {bi['lineno']}; binding lines {bi['eject_binding_lines']}"),
        ("the eject body's steps sit in one strictly increasing byte order",
         order_ats == sorted(order_ats) and len(order_ats) == len(order),
         f"{dict(zip(order, order_ats))}"),
        ("the velocity call's vector is the literal (0,0,0)",
         all(abs(x) < 1e-9 for x in ev["vec"]), f"vector {ev['vec']}"),
        ("the velocity call's receiver is the car's Mesh, not the pawn",
         ev["receiver_object"].endswith("Car") and ev["receiver_component"] == "Core.Mesh",
         f"{ev['receiver_object']}.{ev['receiver_component']}"),
        ("the eject body stores a last-eject timestamp beside TimeSeconds",
         "RPlayerController.LastEjectFromBatmobileTime" in dm["ref_at"]
         and "Core.TimeSeconds" in dm["ref_at"],
         f"+{dm['ref_at'].get('RPlayerController.LastEjectFromBatmobileTime')} / "
         f"+{dm['ref_at'].get('Core.TimeSeconds')}"),
        ("the eject body references the boost byte BoostingOut",
         len(dm["boosting_out_ats"]) >= 2,
         f"{len(dm['boosting_out_ats'])} refs at {dm['boosting_out_ats']}"),
        ("the class defaults name special moves ending _To_Glide",
         len([m for m in ev["special_moves"] if m.endswith("_To_Glide")]) >= 2,
         f"{ev['special_moves']}"),
        ("no vehicle module dump carries an eject/parachute/bail/catapult MEMBER name",
         all(ce["stats"][t]["member"] == 0 for t in
             ("eject", "parachute", "bail", "catapult")),
         "; ".join(f"{t}: raw={ce['stats'][t]['hits']} path={ce['stats'][t]['path']} "
                   f"member={ce['stats'][t]['member']}"
                   for t in ("eject", "parachute", "bail", "catapult", "hold_time", "keymap"))),
        ("every member-style `launch` hit is a fighterjet socket name, not a driver launch",
         all("launch_rail" in r for r in launch_members) and ce["stats"]["launch"]["member"] > 0,
         f"{ce['stats']['launch']['member']} member hits: {launch_members[:4]}"),
        ("the only member-style `impulse` hit is the known train member",
         ce["stats"]["impulse"]["member"] > 0
         and all("crashing_impulse" in r for r, _ in ce["member_runs"]["impulse"]),
         f"{ce['stats']['impulse']['member']} member hits: "
         f"{[r for r, _ in ce['member_runs']['impulse']][:3]}"),
        ("the census is not blind: a term that must hit does hit",
         ce["stats"]["velocity"]["member"] > 0,
         f"velocity raw={ce['stats']['velocity']['hits']} "
         f"member={ce['stats']['velocity']['member']}"),
        ("Rico's animation set names the vehicle-to-parachute clip",
         any(t["term"] == "PPparachute_vehicle_eject" and t["plaintext"] > 0
             for r in ri if r["found"] for t in r["terms"]),
         "; ".join(f"{r['name']}: " + ", ".join(
             f"{t['term']}={t['plaintext']}" for t in r["terms"]) for r in ri)),
        ("Rico's state machine does not reference the eject ACTION",
         all(t["plaintext"] == 0 and t["hash_hex"] == 0
             for r in ri if r["found"] and r["name"] == "rico_base.afsmb"
             for t in r["terms"] if t["term"] == "ACT_EJECT_FROM_VEHICLE"),
         "; ".join(f"{t['term']}: plain={t['plaintext']} hash={t['hash_hex']}"
                   for r in ri if r["found"] and r["name"] == "rico_base.afsmb"
                   for t in r["terms"])),
        ("BmAK's menu labels A as eject and LB as exit",
         any("A" == k or k.startswith("A,") for k in mn["eject"]) and mn["exit_"],
         f"eject {[(k, mn['rows'][k]) for k in mn['eject']]}; "
         f"LB {[(k, mn['rows'][k]) for k in mn['exit_']]}"),
    ]

    return dict(km=km, kp=kp, dn=dn, ce=ce, ri=ri, bi=bi, dm=dm, ev=ev, mn=mn,
                gp=gp, gp_ex=gp_ex, kb=km["devs"]["keyboard"], kb_ex=kp["keyboard"],
                shared_shipped=shared_shipped, shared_export=shared_export,
                face_rows=face_rows, eject_actions=eject_actions,
                para=para, plain=plain, hood=hood, roll=roll,
                order=order, order_ats=order_ats, launch_members=launch_members,
                ctl=ctl, checks=checks)


# ------------------------------------------------------------------ markdown

def md(s):
    return str(s).replace("|", "\\|")


# Modes and debug tooling share these buttons; listing them makes the conflict table
# unreadable, so the per-button column keeps the gameplay actions only.
NOISE = re.compile(r"^(DEBUG_|DEV_|MOVIE_CAM_|MECH_|PLANE_|HELI_|BIKE_|SUBMERSIBLE_|"
                   r"FREEFLY|GUI_(?!PAUSE$|PDA$)|L1$|L2$|R1$|R2$|BTN_)")


def join_acts(acts, keep=6):
    good = [a for a in acts if not NOISE.match(a)]
    out = ", ".join("`" + a + "`" for a in good[:keep])
    if len(good) > keep:
        out += f" +{len(good) - keep} more"
    return out or "—"


def render(d):
    km, kp, dn, ce, ri, bi, dm, ev, mn = (d["km"], d["kp"], d["dn"], d["ce"],
                                          d["ri"], d["bi"], d["dm"], d["ev"], d["mn"])
    gp, gp_ex, kb, kb_ex = d["gp"], d["gp_ex"], d["kb"], d["kb_ex"]
    ctl = d["ctl"]
    L = []
    A = L.append
    A("# EJECT_MAP - the BmAK eject, step by step, against JC3 (G3-08b)")
    A("")
    A("Generated by `Tools/scripts/jc3_eject_map.py --write`. Do not edit by hand; "
      "`--check` re-reads every source and compares.")
    A("")
    A("**Short answer.** BmAK's eject is one button, a guard, a scripted `DriverLeave` on the "
      "pawn, a cockpit-open, a car velocity of `(0,0,0)` on one branch, and an animation "
      "special move whose names end `_To_Glide`. The launch is authored as a **move**, not as a "
      "velocity. On the JC3 side the two actions the operator names - *jump to roof* and "
      "*parachute out* - are **both on one control in both JC3 binding tables**, which is the "
      "press/hold pair's fingerprint but not its proof: neither table carries a hold flag or a "
      "duration, so the press/hold split is the **game's own menu** (operator screenshots) and "
      "the **holding time is UNKNOWN** in every file on this machine. The two tables also "
      "**disagree about which control it is**: the shipped `keymap_gamepad.bin` puts both on "
      f"**{' / '.join(d['shared_shipped'])}** and binds **no face button at all** "
      f"({len(d['face_rows'])} A/B/X/Y rows), while the player's export puts both on "
      f"**{' / '.join(d['shared_export'])}**. The only vehicle-context condition in JC3's data "
      "is the donor's parent-speed gate on the driver exit: below 5 the exit is "
      "`S_EXIT_VEHICLE`, from 5 up it is `S_EXIT_VEHICLE_PARA` - at speed the driver does leave "
      "through a parachute state. Nothing in the data aims the driver upward.")
    A("")
    A("Labels: **decoded** = read from a file (path + offset/line); **derived** = computed "
      "from decoded facts, rule given; **operator-stated** = the operator's statement, not a "
      "file; **quoted** = a number another card decoded that this script does not re-read; "
      "**UNKNOWN** = what was tried, where it would be.")
    A("")
    A("## 1. Sources")
    A("")
    A("| source | read for | layer / size |")
    A("|---|---|---|")
    for f in km["files"]:
        A(f"| `{f['path']}` | shipped bindings | {f['mount']}, {f['bindings']} bindings, "
          f"{f['size']} B, sha256 `{f['sha256'][:16]}`, entry @ {f['entry_offset']} |")
    A(f"| `{os.path.basename(kp['path'])}` | the player's own export | {len(kp['rows'])} rows, "
      f"fields `{', '.join(kp['field_names'])}` |")
    A(f"| `{os.path.basename(dn['path'])}` | donor graph: exits, states, gates | "
      f"{len(dn['exits'])} exits |")
    A("| `rico_base.asb`, `rico_base.afsmb` | Rico's clip + state machine | "
      + ", ".join(f"`{r['name']}` " + (f"{r['size']} B @ {r['entry_offset']}"
                                        if r["found"] else "NOT FOUND") for r in ri) + " |")
    A(f"| `{ce['dir']}` | module byte census | {ce['files']} dumps |")
    A(f"| `{os.path.basename(bi['path'])}` | BmAK A binding | line {bi['lineno']} |")
    A(f"| `{os.path.basename(dm['path'])}` | decoded `BmGame.upk` export {dm['export']} | "
      f"{dm['script_bytes']} script bytes, {dm['unexplained']} unattributed |")
    A(f"| `{os.path.basename(ev['path'])}` | eject velocity call + receiver | "
      f"`{ev['package']}` sha1 `{ev['package_sha1'][:16]}` |")
    A(f"| `{os.path.basename(mn['path'])}` | menu labels | menu-label source (operator) |")
    A("")
    A("## 2. The BmAK eject as steps")
    A("")
    A(f"Body `DrivingMode.EjectFromVehicle`, export **{dm['export']}**, "
      f"**{dm['script_bytes']}** script bytes, {len(dm['calls'])} call sites. Offsets are script "
      f"offsets in that body.")
    A("")
    A("| # | step | what the bytes say | label | evidence |")
    A("|---|---|---|---|---|")
    A(f"| 1 | input | gamepad **A** runs `EjectFromVehicle`; the same line also runs "
      f"`BattleStrafe`, `ContextSensitive`, `Run`, `CapeGlide`, `Evade` and 4 debug tokens | "
      f"decoded | `DefaultInput.ini:{bi['lineno']}`; the only line binding "
      f"`EjectFromVehicle` ({len(bi['eject_binding_lines'])}) |")
    A(f"| 2 | input shape | menu: **`A, A` (double press)** = "
      f"\"{mn['rows'].get('A, A (double press)', '(label not found)')}\"; LB = "
      f"\"{mn['rows'].get('LB', '(not found)')}\" | menu-label (operator screenshot) | "
      f"`{os.path.basename(mn['path'])}` |")
    A(f"| 3 | second-press timing | the body stores `LastEjectFromBatmobileTime` at "
      f"`+{dm['ref_at'].get('RPlayerController.LastEjectFromBatmobileTime')}` beside "
      f"`WorldInfo.TimeSeconds` (`+{dm['ref_at'].get('Core.TimeSeconds')}`), i.e. it writes a "
      f"timestamp; the body's float constants are {[c['value'] for c in dm['constants']]}, none "
      f"a sub-second window (`600.0` at `+827` sits between `VSizeSq2D()` "
      f"`+{dm['at']['VSizeSq2D']}` and the next call, so it reads as a distance threshold) | "
      f"timestamp decoded; window **UNKNOWN** | same body |")
    A(f"| 4 | guard | first call: `{dm['calls'][0]['text']}` at `+{dm['calls'][0]['at']}` | call "
      f"decoded, condition **UNKNOWN** | same body (`CONTROLS_NATIVE.md`: 0 natives for "
      f"`EjectFromVehicle`) |")
    A(f"| 5 | space above cockpit | `CheckSpaceAboveBatmobileCockpit()` at "
      f"`+{dm['at']['CheckSpaceAboveBatmobileCockpit']}` | decoded | same body |")
    A(f"| 6 | Batman leaves the seat | `DriverLeave(true, <0x2d>, FFInRange)` "
      f"`+{dm['at']['DriverLeave']}`; `RemoveBatmobileBindsAndSetBatmanBinds()` "
      f"`+{dm['at']['RemoveBatmobileBindsAndSetBatmanBinds']}`; `PlayCockpitOpenFast()` "
      f"`+{dm['at']['PlayCockpitOpenFast']}` | decoded calls | same body |")
    A(f"| 7 | car state change | `{ev['callee']}({ev['vec_token']}, {ev['bool_kind']})` at "
      f"`+{ev['at']}` on **`{ev['receiver_object']}.{ev['receiver_component']}`**; vector "
      f"`{ev['vec']}`, inside `if (FFInRange)` at `+{ev['guard']['at']}` | decoded | "
      f"`{os.path.basename(ev['path'])}`, raw args `{ev['arg_bytes']}` |")
    A(f"| 8 | what moves Batman | `{dm['calls'][-2]['text']}` at "
      f"`+{dm['at']['TriggerSpecialMove']}` - an animation special move, not a velocity | call "
      f"decoded, trajectory **UNKNOWN** | same body; defaults name "
      f"{', '.join('`' + m + '`' for m in ev['special_moves'])} "
      f"({ev['class_default_entries']} eject/velocity entries, {ev['mode_id_entries']} with a "
      f"mode id) |")
    A(f"| 9 | \"into glide\" | the move names end **`_To_Glide`**; the body references "
      f"`CapeGlideTarget` (`+{dm['ref_at'].get('RPlayerController.CapeGlideTarget')}`) and "
      f"`AttackGlide` (`+{dm['ref_at'].get('RPlayerController.AttackGlide')}`) | names decoded, "
      f"which glide runs **UNKNOWN** | class defaults + refs |")
    A(f"| 10 | car afterwards | the only motion statement is the zero vector at `+{ev['at']}` on "
      f"the `FFInRange` branch; the body ends `ClearTimer()` at `+{dm['at']['ClearTimer']}` | "
      f"decoded calls; the *rotation* the operator reports is **operator-stated** | same body |")
    A(f"| 11 | battle mode, moving | `BoostingOut` referenced {len(dm['boosting_out_ats'])} "
      f"times ({', '.join('+%d' % x for x in dm['boosting_out_ats'])}), `CurrentEjectType` at "
      f"`+{dm['ref_at'].get('RPlayerController.CurrentEjectType')}` | refs decoded, branch "
      f"**UNKNOWN** | same body |")
    A(f"| 12 | exit is a different action | LB exit and A eject are two menu rows; the config "
      f"chain has `ExitVehiclePressed` with **no key** | menu-label + decoded absence | "
      f"`CONTROLS_MENU_SCREENS.md`; `CONTROLS.md` UNKNOWN list |")
    A("")
    A("The Firefly takedown sits in the same body "
      f"(`GetHeavyTankExclusionZone` `+{dm['at']['GetHeavyTankExclusionZone']}`, "
      f"`PlayThought` `+{dm['at']['PlayThought']}`, "
      f"`InRangeForTakedownPrompt` `+{dm['at']['InRangeForTakedownPrompt']}`, "
      f"`InRangeForActualTakedown` `+{dm['at']['InRangeForActualTakedown']}`, "
      f"`InitiateTakedownMove(self)` `+{dm['at']['InitiateTakedownMove']}`, "
      f"`VSizeSq2D()` `+{dm['at']['VSizeSq2D']}`); which branch reaches it is not decoded.")
    A("")
    A("## 3. JC3: which control carries the pair")
    A("")
    A("| action | shipped `keymap_gamepad.bin` (mounted) | player's export (gamepad) | JC3 menu label |")
    A("|---|---|---|---|")
    labels = {"STUNT_JUMP": "JUMP TO ROOF (A press)", "OPEN_PARACHUTE": "OPEN PARACHUTE (HOLD A)",
              "ENTER_VEHICLE": "—", "EXIT_VEHICLE": "—", "USE_VEHICLE_MOD": "—",
              "HANDBRAKE": "HANDBRAKE (X)", "FIRE_VEHICLE_WEAPON_PRIMARY": "fire primary (RB)",
              "FIRE_VEHICLE_WEAPON_SECONDARY": "fire secondary (LB)",
              "ACCELERATE": "accelerate (RT)", "REVERSE": "reverse (LT)",
              "LOOK_BACK_CAM": "look back (hold RS)", "SOUND_HORN_SIREN": "sound horn (LS press)",
              "GUI_PAUSE": "pause (Start)", "GUI_PDA": "commlink (Back)"}
    for a in ACTIONS:
        s = ctl(gp["by_action"], a)
        e = ctl(gp_ex["by_action"], a)
        A(f"| `{a}` | {', '.join('`' + x + '`' for x in s) or '—'} | "
          f"{', '.join('`' + x + '`' for x in e) or '—'} | {labels.get(a, '—')} |")
    A("")
    A(f"So the **shipped** table holds both `STUNT_JUMP` and `OPEN_PARACHUTE` on "
      f"**{' / '.join(d['shared_shipped'])}** and binds **no face button** "
      f"({len(d['face_rows'])} rows for A/B/X/Y; the controls it does use are "
      f"{', '.join('`' + k + '`' for k in sorted(gp['by_key']))}). The **export** holds both on "
      f"**{' / '.join(d['shared_export'])}** and is the one that matches the menu. That the two "
      f"actions share one control in *both* tables is the press/hold pair's fingerprint; it is "
      f"not proof of it, because **multiple actions on one key is the normal shape here** - the "
      f"export also puts `GUI_OK`, `BTN_A` and `JUMP` on that same A.")
    A("")
    A("### 3.1 What the tables cannot answer")
    A("")
    A("| question | answer | why |")
    A("|---|---|---|")
    A(f"| press or hold? | **UNKNOWN** in the files; the menu says press = roof, hold = "
      f"parachute | every binding is one `(input, action)` pair with two `stringZ` properties "
      f"and nothing else (`INPUT.md` byte accounting); the export's {len(kp['rows'])} rows all "
      f"have the shape `{sorted(kp['shapes'])[0]}` |")
    A(f"| hold duration | **UNKNOWN** | 0 hold/duration/tap words in {gp['bindings']} gamepad + "
      f"{kb['bindings']} keyboard mounted bindings + {len(kp['rows'])} export rows; `settings/parachuteparams.bin` (344 B) carries "
      f"asset paths only (`parachute.bsk`, `parachute.asb`); `text/master.stringlookup` (3,567 B) "
      f"is a name lookup, 0 `parachute` hits |")
    A(f"| which vehicle context | **the exit graph's speed gate**: `{d['para']['name']}` -> "
      f"`{d['para']['state']}` gate `{d['para']['gate']}`; `{d['plain']['name']}` -> "
      f"`{d['plain']['state']}` gate `{d['plain']['gate']}` | decoded from "
      f"`CInteractionGraphParentVelocityCondition` `min`/`max` in the donor `.epe`; no vehicle "
      f"entity names an input action (0 `keymap` hits) |")
    A(f"| a launch velocity | **no member**: 0 launch/impulse/force members in the donor's "
      f"{len(dn['exits'])} exits; member-style census of {ce['files']} dumps: "
      + ", ".join(f"`{t}` {ce['stats'][t]['member']}" for t in
                  ("eject", "parachute", "bail", "launch", "catapult", "impulse", "hold_time"))
      + f" (`launch` = fighterjet sockets, `impulse` = `crashing_impulse`) | byte census, raw "
      f"hits split out as asset paths |")
    A(f"| an eject action name | **no**: {len(d['eject_actions'])} names match `/EJECT/` across "
      f"4 tables | shipped + export, both devices |")
    A("")
    A("### 3.2 Rico's side: the state exists, the action does not")
    A("")
    A("| file | term | plaintext | Jenkins hex | first offset |")
    A("|---|---|---|---|---|")
    for r in ri:
        if not r["found"]:
            A(f"| `{r['name']}` | **not in the index** | - | - | {r['searched']} rows searched |")
            continue
        for t in r["terms"]:
            A(f"| `{r['name']}` ({r['size']} B) | `{t['term']}` | {t['plaintext']} | "
              f"{t['hash_hex']} | {t['first'] if t['first'] is not None else '—'} |")
    A("")
    A("## 4. Mapping: BmAK step -> JC3 equivalent -> what is lost")
    A("")
    A("| BmAK step | JC3 equivalent | what is lost or different |")
    A("|---|---|---|")
    A(f"| **A press #1** (`EjectFromVehicle`, BmAK side, `DefaultInput.ini:{bi['lineno']}`) | "
      f"`STUNT_JUMP` (press A) = *jump to roof*; the matching **state** is the donor's "
      f"`{d['hood']['name']}` -> `{d['hood']['state']}` | same button, different outcome: JC3 "
      f"stands the player on the hood, BmAK starts the eject. Under the priority rule BmAK "
      f"wins, so this JC3 outcome is dropped inside the car. Whether BmAK's first press already "
      f"ejects or only arms the second is **UNKNOWN** |")
    A(f"| **A press #2 (double press)** = \"Eject Into Glide\" | `OPEN_PARACHUTE` (hold A) + the "
      f"donor's `{d['para']['name']}` -> `{d['para']['state']}` at gate `{d['para']['gate']}` | "
      f"the *parachute out of a moving vehicle* half is a real carrier; the press/hold "
      f"threshold has no file evidence, and entry to the exit is the graph's speed gate, not an "
      f"input action |")
    A(f"| **battle mode: no eject while moving, boost instead** (operator-stated) | nothing: JC3 "
      f"has no battle mode and no speed-gated input | needs a build-side condition; BmAK's side "
      f"is only the `BoostingOut` byte ({len(dm['boosting_out_ats'])} refs, branch **UNKNOWN**) |")
    A(f"| **car breaks straight after eject** (operator-stated) | none: BmAK zeroes the car's "
      f"velocity (`{ev['vec']}` on `{ev['receiver_component']}`) and stops; JC3's exits carry no "
      f"motion member | no JC3 carrier for a straight break; the zero vector is a *stop* |")
    A(f"| **LB exit** (pursuit: jumps out, car breaks right; battle: straight - operator-stated) "
      f"| JC3 `EXIT_VEHICLE` is on "
      f"{', '.join('`' + x + '`' for x in ctl(gp_ex['by_action'], 'EXIT_VEHICLE')) or '—'} "
      f"(export); donor `{d['plain']['name']}` -> `{d['plain']['state']}`, roll-out "
      f"`{d['roll']['name']}` -> `{d['roll']['state']}` | BmAK's LB is JC3's **fire secondary**, "
      f"so secondary fire is displaced; JC3's own exit button is superseded by LB |")
    A(f"| **glide after the eject** | BmAK: special moves ending `_To_Glide`; JC3: the "
      f"`{d['para']['state']}` state | BmAK's glide is an authored move whose numbers are not in "
      f"`BmGame.upk`; JC3's is a state whose behaviour is native |")
    A("")
    A("## 5. Who owns which button inside the Batmobile")
    A("")
    A("Priority (operator-stated): inside the car BmAK wins; a JC3 action only fills a BmAK "
      "step that has no BmAK button; JC3 keeps **pause** and **commlink**.")
    A("")
    A("| button | BmAK | JC3 (export, = the menu; debug/mode rows hidden) | owner |")
    A("|---|---|---|---|")
    rows5 = [
        ("A", f"eject (`DefaultInput.ini:{bi['lineno']}`)", "A", "**BmAK**"),
        ("LB (`LSHOULDER`)", "exit (menu; `ExitVehiclePressed` has no key)", "LSHOULDER",
         "**BmAK** - secondary fire displaced"),
        ("Y", "afterburner (config `bVehicleBoostButton`)", "Y",
         "split: **ENTER stays JC3's** (operator rule); Y's exit/boost part is BmAK's"),
        ("B", "tracker/immobilizer, EMP", "B", "**BmAK** - `USE_VEHICLE_MOD` displaced"),
        ("X", "brake/reverse, missile barrage", "X",
         "**conflict**: JC3 `HANDBRAKE` is the same idea on the same button"),
        ("RB", "cycle view `ToggleDrivingCamera`", "RSHOULDER", "**BmAK** - primary fire displaced"),
        ("RT", "accelerate", "RTRIGGER", "same"),
        ("LT", "battle mode (hold)", "LTRIGGER", "**BmAK** - reverse displaced"),
        ("LS press", "sonar", "LSTICKBUTTON", "**BmAK** - horn displaced"),
        ("RS press", "look behind", "RSTICKBUTTON", "same"),
        ("Start", "pause `UserPause` (`:262`)", "START", "**JC3 keeps priority**"),
        ("Back", "WayneTech `OpenLevelUpOrMap` (`:261`)", "BACK",
         "**JC3 keeps priority** on commlink; BmAK's map row loses"),
    ]
    for label, bm, key, owner in rows5:
        A(f"| {label} | {bm} | {join_acts(gp_ex['by_key'].get(key, []))} | {owner} |")
    A("")
    A("JC3's car page also lists **NITROUS (hold B)** and **TURBO JUMP (B)**, but no table has "
      f"a `NITRO`/`BOOST`/`TURBO` action: `B` carries "
      f"{join_acts(gp_ex['by_key'].get('B', []))} in the export and "
      f"{join_acts(gp['by_key'].get('B', []))} in the shipped table (the shipped gamepad "
      f"table has no B row at all), so the nitrous trigger is **UNKNOWN** (the "
      f"`arcade.nitro_boost` module block exists; the trigger is native).")
    A("")
    A("## 6. UNKNOWNs")
    A("")
    A("1. **The JC3 hold threshold.** Tried: both keymap bins (every mounted copy), the player's "
      "export, `settings/parachuteparams.bin`, `text/master.stringlookup`, the donor `.epe`, "
      "Rico's `.asb`/`.afsmb`, 232 entity dumps. No hold/duration/tap field. Would be in: native "
      "input code, or an input table not in the index.")
    A("2. **Which table is live, and which control JC3 really uses.** The shipped gamepad bin "
      f"binds no face button at all and puts the pair on "
      f"{' / '.join(d['shared_shipped'])}; the export puts it on "
      f"{' / '.join(d['shared_export'])} and matches the menu. Both are in the install. Would "
      f"be in: a runtime observation (no game runs here).")
    A("3. **Which action a vehicle consumes.** No vehicle entity names an input action "
      f"(`keymap` in {ce['stats']['keymap']['files']}/{ce['files']} dumps); the action -> exit "
      f"link is native.")
    A("4. **The launch trajectory.** BmAK's `TriggerSpecialMove` carries a reference only; the "
      "special-move asset is outside `BmGame.upk`, and JC3's exits carry 0 launch members.")
    A("5. **BmAK's double-press window and first-press behaviour.** A timestamp is written; no "
      "window constant exists in the body.")
    A(f"6. **The battle-mode moving condition and boost fallback.** `BoostingOut` "
      f"({len(dm['boosting_out_ats'])} refs) and `CurrentEjectType` are present, but "
      f"{dm['unexplained']} of {dm['script_bytes']} bytes are unattributed jump tokens, so the "
      f"branch is not decoded.")
    A("7. **The car's post-eject rotation.** Operator-stated; no decoded vector, and no JC3 exit "
      "member can carry it.")
    A(f"8. **`CantEjectFromBatmobile`'s condition.** First call at `+{dm['calls'][0]['at']}` with "
      f"two unnamed 1-byte tokens; its body is not decoded.")
    A("")
    A("## 7. Checks (`--check` re-runs these)")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for name, ok, detail in d["checks"]:
        A(f"| {md(name)} | **{'PASS' if ok else 'FAIL'}** | {md(detail)} |")
    A("")
    A(f"{sum(1 for _, ok, _ in d['checks'] if ok)}/{len(d['checks'])} checks pass.")
    A("")
    A("## 8. Reproduce")
    A("")
    A("```")
    A("python -I Tools/scripts/jc3_eject_map.py --write   # this file")
    A("python -I Tools/scripts/jc3_eject_map.py --check   # re-read the sources and compare")
    A("```")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")

    d = build()
    text = render(d)
    failed = [n for n, ok, _ in d["checks"] if not ok]
    for name, ok, detail in d["checks"]:
        print(("PASS " if ok else "FAIL ") + name + " :: " + str(detail)[:150])
    print(f"{len(d['checks']) - len(failed)}/{len(d['checks'])} checks pass")

    if a.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {OUT_MD} ({len(text)} bytes)")
        return 1 if failed else 0

    if not os.path.exists(OUT_MD):
        print(f"MISSING {OUT_MD}")
        return 1
    with open(OUT_MD, encoding="utf-8") as f:
        disk = f.read()
    same = disk == text
    print(("MATCH " if same else "MISMATCH ") + OUT_MD)
    if not same:
        import difflib
        for ln in list(difflib.unified_diff(disk.splitlines(), text.splitlines(),
                                            "disk", "derived", lineterm=""))[:40]:
            print(ln)
    ok = same and not failed
    print("CHECK OK" if ok else "CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
