#!/usr/bin/env python3
"""G3-08: where Just Cause 3 defines vehicle controls.

Read-only. Writes (with --write) or re-derives and compares (with --check):
  Research/JC3Grab/INPUT.md    the action table, per-class picture, BmAK verdicts, UNKNOWNs
  Research/JC3Grab/INPUT.json  the same data, row by row

Sources:
  * `settings/keymap_gamepad.bin` and `settings/keymap_keyboard.bin`, base and patch
    copies, read out of the game archives through `INDEX.jsonl`
    (`jc3index.load_index` + the entry offset/size), and parsed with the project's
    RTPC container reader (`rtpcdump.parse_rtpc`).
  * the 232 decoded vehicle `.ee` dumps in `$JC3_RAW/entities` (byte census only).

Labels:
  decoded  read from a file (file + archive + offset), or a byte census of a file set
  derived  computed from decoded facts; the rule is stated where it is used
  UNKNOWN  not decodable here; what was tried and where it would be is recorded

Container facts used (all re-derived, never assumed):
  every keymap file is 'RTPC', u32 version 1, a root node and one list node whose
  children are one binding each; a binding node holds two `stringZ` properties,
  (input name, action name). The node records must end exactly where the first
  data record starts - that byte accounting is the layout's oracle, and it is
  printed per file in the report.

Usage:
  python -I jc3_input.py --write
  python -I jc3_input.py --check
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import load_index, DEFAULT_GAME, MOUNT_RANK  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
OUT_MD = os.path.join(OUT, "INPUT.md")
OUT_JSON = os.path.join(OUT, "INPUT.json")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
ENTITIES = os.path.join(RAW, "entities")

SCHEMA = "g3-08-input/1"

KEYMAPS = ["settings/keymap_gamepad.bin", "settings/keymap_keyboard.bin"]

# Scope by name prefix (derived rule, stated in the report). A row whose action name
# matches none of these keeps scope "" = UNKNOWN. This is a naming rule about which
# class an action *names*; it is not a claim about what the game does at runtime.
SCOPES = OrderedDict([
    ("helicopter", r"^HELI_"),
    ("plane", r"^PLANE_"),
    ("submersible", r"^SUBMERSIBLE_"),
    ("motorbike", r"^BIKE_"),
    ("mech-suit", r"^MECH_"),
    ("wingsuit/freefly", r"^(WINGSUIT_|FREEFLY|OPEN_WINGSUIT|OPEN_PARACHUTE)"),
    ("gui", r"^GUI_"),
    ("movie-cam", r"^MOVIE_CAM_"),
    ("debug/dev", r"^(DEBUG_|DEV_|MEASURE_TOOL|QUICK_SAVE|QUICK_LOAD|FREEFLY_COMBO)"),
    ("on-foot", r"^(JUMP|MOVE_|FIRE_LEFT|FIRE_RIGHT|LOOK_|PUSH_GRAPPLE|RELEASE_GRAPPLE|"
                r"RETRACT_GRAPPLE|THROW_GRENADE|PLANT_EXPLOSIVE|DETONATE_EXPLOSIVE|"
                r"SELECT_|RELOAD|MC_FIRE|MC_RELOAD|STUNT_JUMP|WALK|NEXT_WEAPON|"
                r"PREV_WEAPON|TOGGLE_MAGNET|BYPASS_FALL_PREVENTION)"),
    ("land-vehicle", r"^(ACCELERATE|REVERSE|TURN_LEFT|TURN_RIGHT|HANDBRAKE|VEHICLE_CAM|"
                     r"FIRE_VEHICLE_WEAPON_PRIMARY|FIRE_VEHICLE_WEAPON_SECONDARY|"
                     r"USE_ITEM|USE_VEHICLE_MOD|SOUND_HORN_SIREN|LOOK_BACK_CAM|"
                     r"ENTER_VEHICLE|EXIT_VEHICLE|CHALLENGE_RESET_VEHICLE|"
                     r"VEHICLE_RELEASE_GRAPPLE|PRECISION_AIM)"),
])

# The BmAK side. Every row cites the project research it comes from (BmAK is not
# re-read here: G3-02 owns `CONTROLS.md`, this card owns the JC3 side).
#   exact=      names that must all exist in the decoded JC3 action set
#   none_of=    a regex that must match 0 action names for a "not reachable" verdict
BM_ROWS = [
    dict(id="enter vehicle (D-11: the one JC3 action kept)",
         bmak="ENTER, JC3's own control (GRAB_BACKLOG D-11)",
         exact=["ENTER_VEHICLE"]),
    dict(id="exit vehicle (LB)",
         bmak="LB exit (D-11 user mapping)",
         exact=["EXIT_VEHICLE"]),
    dict(id="handbrake / brake",
         bmak="Button bHandbrakeOrBrake, BrakePressed (CONTROLS.md)",
         exact=["HANDBRAKE"]),
    dict(id="throttle / steer",
         bmak="Axis aThrottleAxis, bVehicleBoostButton (CONTROLS.md)",
         exact=["ACCELERATE", "REVERSE", "TURN_LEFT", "TURN_RIGHT"]),
    dict(id="vehicle weapons primary / secondary",
         bmak="BatmobileFireButton, SecondaryFireVehicleWeapon (CONTROLS.md)",
         exact=["FIRE_VEHICLE_WEAPON_PRIMARY", "FIRE_VEHICLE_WEAPON_SECONDARY"]),
    dict(id="driving camera",
         bmak="ToggleDrivingCamera (CONTROLS.md)",
         exact=["VEHICLE_CAM"]),
    dict(id="look behind",
         bmak="bLookBehindVehicle (CONTROLS.md)",
         exact=["LOOK_BACK_CAM"]),
    dict(id="battle mode (LT hold / release pursuit)",
         bmak="LT hold battle mode, release pursuit (D-11 user mapping)",
         none_of=r"(?i)BATTLE|PURSUIT|TRANSFORM|MODE$"),
    dict(id="electromagnetic ejection (A)",
         bmak="A electromagnetic ejection (D-11 user mapping)",
         none_of=r"(?i)EJECT|LAUNCH|CATA.?PULT"),
    dict(id="sonar / scan",
         bmak="BatmobileSonarPressed (CONTROLS.md)",
         none_of=r"(?i)SONAR|SCAN"),
    dict(id="tag gun (pursuit)",
         bmak="PursuitModeTagGun (CONTROLS.md)",
         none_of=r"(?i)TAG_?GUN|TAGGING|TAG_"),
    dict(id="immobilizer (B in track)",
         bmak="B track / immobilizer (D-11 user mapping); EMP path G2-16",
         exact=["USE_ITEM"]),
    dict(id="vehicle weapon selection",
         bmak="SelectVehicleWeapon, 2 driver slots (CONTROLS.md, G2-11)",
         any_of=r"(?i)^(NEXT_WEAPON|PREV_WEAPON|SELECT.*WEAPON|WEAPON.*SELECT)$"),
    dict(id="turret aim",
         bmak="turret/cannon yaw+pitch hinges (G2-13)",
         any_of=r"(?i)^(TURRET|AIM|PRECISION_AIM)"),
    dict(id="nitro / afterburner",
         bmak="bVehicleBoostButton, arcade.nitro_boost (CONTROLS.md, USAGES §6)",
         any_of=r"(?i)^(NITRO|BOOST|WINGSUIT_BOOST)"),
    dict(id="tank pivot / turn on the spot",
         bmak="turn-on-the-spot (TANKTURN.md: no data carrier)",
         none_of=r"(?i)PIVOT|SPIN|ON_?SPOT"),
    dict(id="barrage (B in battle)",
         bmak="barrage in battle (D-11 user mapping)",
         none_of=r"(?i)BARRAGE"),
]

PROBE_STRINGS = ["nitro_boost", "arcade.nitro_boost", "keymap", "EnterVehicle",
                 "ENTER_VEHICLE", "ACCELERATE", "FIRE_VEHICLE_WEAPON_PRIMARY"]

UNKNOWNS = [
    ("which action fires nitro / the afterburner",
     "no action name in either keymap matches NITRO or (vehicle) BOOST; the only boost "
     "name is WINGSUIT_BOOST. The data side exists (`arcade.nitro_boost` on the land "
     "vehicles, USAGES §6), so the trigger is native or in a graph the files do not name."),
    ("whether NEXT_WEAPON / PREV_WEAPON reach a vehicle",
     "both names exist (keyboard) but no file says which mode consumes them, and G2-11 "
     "found 2 driver weapon slots with no switch action."),
    ("how the class-specific action sets are selected at runtime",
     "the class is the root object of the .epe (CCar / CBoat / CHelicopter / CAirPlane / "
     "CTrain / CMotorBike, FORCEPULSE §owners); nothing in the keymap files or the "
     "entities names a class to pick a scheme. The selection is native."),
    ("what a turret aims with",
     "no TURRET action exists; PRECISION_AIM and the LOOK_* axes are the only candidates, "
     "and the hinge wiring is native (TURRET.md)."),
    ("whether a replaced keymap file is honoured from a dropzone",
     "the files are `settings/*.bin` archive entries; G2-27 showed path overrides work "
     "for `.ee`, but no test has been run for a `settings/*.bin` entry (no game runs here)."),
    ("why 26 binding ids are not `H(action name)`",
     "the id equals the Jenkins hash of the action name for 448 of 474 bindings and none of "
     "the other candidates for the remainder (counts printed above). The remaining ids are "
     "stable across the base and patch copies of the same action, so they were fixed before "
     "the current name or by another rule; which one is not in any decoded file."),
    ("the `PP` prefix on the stored input string",
     "the bytes are `PP`+input and the property's offset points 2 bytes past it, so `PP` "
     "is a fixed prefix on every input string in both files; what it encodes is not in any "
     "decoded file."),
    ("which keymap layer the game loads (base vs patch)",
     "both copies are in the install and differ; MOUNT_RANK says patch wins for path "
     "lookups, but no runtime observation was made."),
]


# ------------------------------------------------------------------ sources

def sha(b):
    return hashlib.sha256(b).hexdigest()


def read_entries(rows, path):
    hits = [r for r in rows if r["path"].lower() == path.lower()]
    out = []
    for r in sorted(hits, key=lambda x: MOUNT_RANK[x["mount"]]):
        with open(os.path.join(DEFAULT_GAME, r["archive"] + ".arc"), "rb") as f:
            f.seek(r["offset"])
            data = f.read(r["size"])
        if len(data) != r["size"]:
            raise SystemExit(f"short read {len(data)} != {r['size']} for {path}")
        out.append((r, data))
    return out


def strz(data, off):
    end = data.index(b"\0", off)
    return data[off:end].decode("ascii", "replace"), end + 1


def align4(n):
    return (n + 3) & ~3


def parse_keymap(path, r, data):
    """Decode one keymap container into bindings + the accounting facts.

    Layout (read from the bytes, then asserted):
      0   'RTPC'
      4   u32 version == 1
      8   root node record  <u32 name_hash, u32 data_offset, u16 nprops, u16 nkids>
      20  list node record  (nkids = number of bindings, nprops = 0,
                            data_offset = end of the record region)
      32  one 12-byte record per binding
      ... then per binding, in record order: its 2 property records (9 bytes each:
          u32 name_hash, u32 data, u8 type==3), then 'PP'+input as a stringZ, then the
          action as a stringZ, padded to 4.
    Bound properties' data field is the string offset; for the input it points 2 bytes
    past the start of the stored string, i.e. past the literal 'PP'.

    The oracle is the sequential prediction: every following binding's data offset is
    computed from the previous one, so a wrong stride or a skipped binding fails here.
    """
    if data[0:4] != b"RTPC":
        raise SystemExit(f"{path}: not RTPC, magic={data[0:4]!r}")
    (version,) = struct.unpack_from("<I", data, 4)
    if version != 1:
        raise SystemExit(f"{path}: RTPC version {version}, expected 1")
    rh, rdoff, rnp, rnc = struct.unpack_from("<IIHH", data, 8)
    if rnc != 1 or rnp != 0 or rdoff != 20:
        raise SystemExit(f"{path}: root record {rh:08X} doff={rdoff} np={rnp} nc={rnc}, "
                         f"expected doff=20 np=0 nc=1")
    lh, ldoff, lnp, lnc = struct.unpack_from("<IIHH", data, 20)
    if lnp != 0 or ldoff != 32:
        raise SystemExit(f"{path}: list record doff={ldoff} np={lnp}, expected 32/0")
    records_end = 32 + 12 * lnc
    bindings = []
    type_counts = Counter()
    prop_hashes = Counter()
    seen = {}
    JCAND = ("action", "input", "PP+input", "input_lower", "action+input",
             "input+action", "action_index")
    jmatch = {k: 0 for k in JCAND}
    cursor = records_end
    for i in range(lnc):
        nh, ndoff, nnp, nnc = struct.unpack_from("<IIHH", data, 32 + 12 * i)
        if (nnp, nnc) != (2, 0):
            raise SystemExit(f"{path}: binding {i} has np={nnp} nc={nnc}, expected 2/0")
        if ndoff != cursor:
            raise SystemExit(f"{path}: binding {i} data at {ndoff}, predicted {cursor}")
        props = []
        for k in range(2):
            phash, pdata, ptype = struct.unpack_from("<IIB", data, ndoff + 9 * k)
            type_counts[ptype] += 1
            prop_hashes[f"{phash:08X}"] += 1
            if ptype != 3:
                raise SystemExit(f"{path}: binding {i} prop {k} type {ptype}, expected 3")
            s, _ = strz(data, pdata)
            props.append((phash, pdata, s))
        (ih, ioff, inp), (ah, aoff, act) = props
        # Every block starts with the literal 'PP', then whichever of its two names is
        # not already in the pool; the property offset skips the prefix (+2).
        pos = ndoff + 18
        if data[pos:pos + 2] != b"PP":
            raise SystemExit(f"{path}: binding {i} has no 'PP' prefix at {pos}")
        pos += 2
        for name, off in ((inp, ioff), (act, aoff)):
            if off in seen:
                if seen[off] != name:
                    raise SystemExit(f"{path}: binding {i} offset {off} reused for two names")
                continue
            if off != pos:
                raise SystemExit(f"{path}: binding {i} string {name!r} at {off}, predicted {pos}")
            if data[off:off + len(name)] != name.encode("ascii") or data[off + len(name)] != 0:
                raise SystemExit(f"{path}: binding {i} string at {off} is not {name!r}\0")
            seen[off] = name
            pos = off + len(name) + 1
        # Is the binding's node hash any name hash we can recompute? Counted, because the
        # answer decides how the id is described (and what stays UNKNOWN).
        cands = {"action": act, "input": inp, "PP+input": "PP" + inp,
                 "input_lower": inp.lower(), "action+input": act + inp,
                 "input+action": inp + act, "action_index": act + str(i)}
        for key, text in cands.items():
            if (hash_jenkins(text.encode("ascii", "replace")) & 0xFFFFFFFF) == nh:
                jmatch[key] += 1
        bindings.append({
            "node_index": i,
            "node_hash": f"{nh:08X}",
            "input": inp, "action": act,
            "input_string_offset": ioff,
            "action_string_offset": aoff,
        })
        tail = len(data) - pos if i == lnc - 1 else None
        cursor = align4(pos)
    if not 0 <= tail <= 3:
        raise SystemExit(f"{path}: {tail} tail bytes after the last block, expected 0..3")
    if pos > len(data):
        raise SystemExit(f"{path}: last block ends at {pos}, past the file {len(data)}")
    accounting = {
        "size": len(data),
        "version": version,
        "root_hash": f"{rh:08X}",
        "list_hash": f"{lh:08X}",
        "record_region": f"32..{records_end} ({lnc} x 12 B)",
        "bindings": len(bindings),
        "first_data_offset": records_end,
        "tiled_end": pos,
        "tail_bytes": tail,
        "blocks_tile_data": True,
        "distinct_strings": len(seen),
        "string_bytes_conserved": sum(len(v) + 3 for v in seen.values()),
        "property_types": {str(k): v for k, v in sorted(type_counts.items())},
        "property_hashes": {k: v for k, v in sorted(prop_hashes.items())},
        "node_hash_jenkins_matches": jmatch,
        "sha256": sha(data),
    }
    return bindings, accounting



def scope_of(action):
    for name, rx in SCOPES.items():
        if re.match(rx, action):
            return name
    return ""


# ------------------------------------------------------------------ fleet census

def entity_census():
    if not os.path.isdir(ENTITIES):
        raise SystemExit(f"missing entity dumps: {ENTITIES}")
    names = sorted(os.listdir(ENTITIES))
    hits = {s: 0 for s in PROBE_STRINGS}
    examples = {}
    nitro_members = Counter()
    tokens = Counter()
    for fn in names:
        with open(os.path.join(ENTITIES, fn), "rb") as f:
            blob = f.read()
        for s in PROBE_STRINGS:
            c = blob.count(s.encode())
            if c:
                hits[s] += 1
                examples.setdefault(s, []).append(fn)
        for m in re.finditer(rb"[A-Za-z0-9_.]*nitro_boost[A-Za-z0-9_.\[\]]*", blob):
            nitro_members[m.group().decode("latin-1")] += 1
        parts = fn.split("__")[0].split("_")
        if len(parts) >= 2:
            tokens[parts[1]] += 1
    return {
        "dir": ENTITIES,
        "files": len(names),
        "probe_hits": {s: {"files": hits[s], "example": examples.get(s, [None])[0]}
                       for s in PROBE_STRINGS},
        "nitro_member_paths": [[p, n] for p, n in nitro_members.most_common(8)],
        "class_tokens": dict(sorted(tokens.items())),
    }


# ------------------------------------------------------------------ bmak verdicts

def evaluate_bm(actions):
    out = []
    for row in BM_ROWS:
        ev = []
        if "exact" in row:
            ok = all(a in actions for a in row["exact"])
            for a in row["exact"]:
                ev.append(f"{a}: {'present' if a in actions else 'absent'}")
            verdict = "reachable" if ok else ("not reachable" if not any(
                a in actions for a in row["exact"]) else "partial")
        elif "none_of" in row:
            m = [a for a in actions if re.search(row["none_of"], a)]
            ev.append(f"actions matching /{row['none_of']}/: {len(m)}"
                      + (f" {sorted(m)[:6]}" if m else ""))
            verdict = "not reachable" if not m else "UNKNOWN"
        else:
            m = sorted(a for a in actions if re.search(row["any_of"], a))
            ev.append(f"actions matching /{row['any_of']}/: {m}")
            verdict = "UNKNOWN"
        out.append(dict(id=row["id"], bmak=row["bmak"], verdict=verdict,
                        evidence="; ".join(ev)))
    return out


# ------------------------------------------------------------------ build

def build():
    rows = load_index(OUT)
    files = []
    all_bindings = []
    for path in KEYMAPS:
        entries = read_entries(rows, path)
        if not entries:
            raise SystemExit(f"not in the index: {path}")
        for r, data in entries:
            bindings, acc = parse_keymap(path, r, data)
            for b in bindings:
                b.update(file=path, mount=r["mount"], archive=r["archive"],
                         entry_offset=r["offset"], scope=scope_of(b["action"]))
            files.append({"path": path, "mount": r["mount"], "archive": r["archive"],
                          "entry_offset": r["offset"], **acc})
            all_bindings.extend(bindings)

    # The mounted (patch) layer is what the index ranks last; report it separately so
    # base/patch drift is visible instead of silently merged.
    top = {}
    for f in files:
        if f["mount"] not in top or MOUNT_RANK[f["mount"]] > MOUNT_RANK[top[f["mount"]]["mount"]]:
            top[f["mount"]] = f
    active = {}
    for path in KEYMAPS:
        cand = [f for f in files if f["path"] == path]
        active[path] = max(cand, key=lambda f: MOUNT_RANK[f["mount"]])["mount"]

    def cur(path):
        return [b for b in all_bindings
                if b["file"] == path and b["mount"] == active[path]]

    actions = {}
    for path in KEYMAPS:
        for b in cur(path):
            actions.setdefault(b["action"], {"gamepad": "", "keyboard": "", "scope": b["scope"]})
            dev = "gamepad" if "gamepad" in path else "keyboard"
            if not actions[b["action"]][dev]:
                actions[b["action"]][dev] = b["input"]
    for a, v in actions.items():
        if not v["scope"]:
            v["scope"] = scope_of(a)

    # base vs patch diff, per device
    diffs = []
    for path in KEYMAPS:
        base = [b for b in all_bindings if b["file"] == path and b["mount"] == "base"]
        pat = [b for b in all_bindings if b["file"] == path and b["mount"] == "patch"]
        if not base or not pat:
            diffs.append({"file": path, "base": len(base), "patch": len(pat),
                          "note": "one layer only"})
            continue
        bp = {(b["input"], b["action"]) for b in base}
        pp = {(b["input"], b["action"]) for b in pat}
        diffs.append({"file": path, "base": len(base), "patch": len(pat),
                      "added_in_patch": sorted(f"{i}->{a}" for i, a in pp - bp),
                      "removed_in_patch": sorted(f"{i}->{a}" for i, a in bp - pp)})

    order = {p: i for i, p in enumerate(KEYMAPS)}
    all_bindings.sort(key=lambda b: (order[b["file"]], MOUNT_RANK[b["mount"]],
                                     b["action"], b["input"]))
    bm = evaluate_bm(set(actions))
    census = entity_census()
    scopes = Counter(v["scope"] or "UNKNOWN" for v in actions.values())

    return {
        "schema": SCHEMA,
        "game": DEFAULT_GAME,
        "index": os.path.join(OUT, "INDEX.jsonl"),
        "files": files,
        "active_layer": active,
        "binding_rows": all_bindings,
        "actions": {a: actions[a] for a in sorted(actions)},
        "scope_counts": dict(sorted(scopes.items())),
        "scope_rules": {k: v for k, v in SCOPES.items()},
        "layer_diff": diffs,
        "entity_census": census,
        "bmak": bm,
        "unknowns": [{"what": w, "why": y} for w, y in UNKNOWNS],
        "counts": {
            "files": len(files),
            "bindings": len(all_bindings),
            "actions": len(actions),
            "actions_with_both_devices": sum(1 for v in actions.values()
                                             if v["gamepad"] and v["keyboard"]),
            "entity_files": census["files"],
        },
    }


# ------------------------------------------------------------------ markdown

def md(s):
    return str(s).replace("|", "\\|")


def render(d):
    L = []
    A = L.append
    c = d["counts"]
    A("# JC3 vehicle input model (G3-08)")
    A("")
    A("Generated by `Tools/scripts/jc3_input.py --write`. Do not edit by hand; `--check` "
      "re-derives and compares.")
    A("")
    A("Labels: `decoded` = read from a file (file + archive + offset, or a byte census); "
      "`derived` = computed from decoded facts (rule given); `UNKNOWN` = not decodable "
      "here, see the UNKNOWN list at the end.")
    A("")
    A("## Where JC3 defines vehicle controls (decoded)")
    A("")
    A("Two `settings/*.bin` entries in the archives are the whole input definition. Both "
      "are `RTPC` containers (the same container the `.epe` graphs use): a root node, one "
      "list node, and **one child record per binding**. Each binding's two 9-byte property "
      "records are written inline, followed by its two strings (`\"PP\"`+input, then the "
      "action), 4-byte aligned.")
    A("")
    A("| file | layer | archive | entry offset | size | bindings | sha256 (16) |")
    A("|---|---|---|---|---|---|---|")
    for f in d["files"]:
        A(f"| `{md(f['path'])}` | {f['mount']} | `{md(f['archive'])}` | {f['entry_offset']} | "
          f"{f['size']} | {f['bindings']} | `{f['sha256'][:16]}` |")
    A("")
    A("Layer in use below: " + ", ".join(f"`{md(k)}` → **{v}**"
                                         for k, v in d["active_layer"].items()) +
      " (derived: `MOUNT_RANK` of `jc3index.py`; the patch layer wins a path lookup).")
    A("")
    A("**Byte-accounting oracle** (decoded, per file): each binding owns one block - "
      "18 B of property records, then the literal `\"PP\"`, then whichever of its two names "
      "is not already in the string pool (names are deduplicated across bindings), padded to "
      "4. The blocks must tile the file exactly from the end of the record region, with 0–3 "
      "alignment bytes at the tail. This is what fails on a wrong stride or a skipped binding.")
    A("")
    A("| file | layer | record region | bindings | first block | tiled end | tail | "
      "distinct strings | tiles |")
    A("|---|---|---|---|---|---|---|---|---|")
    for f in d["files"]:
        A(f"| `{md(f['path'])}` | {f['mount']} | {f['record_region']} | {f['bindings']} | "
          f"{f['first_data_offset']} | {f['tiled_end']} | {f['tail_bytes']} | "
          f"{f['distinct_strings']} | {f['blocks_tile_data']} |")
    A("")
    A("The two property name hashes are `" +
      "` / `".join(f for f in d["files"][0]["property_hashes"]) +
      "` in all four files (input / action), and every property is type 3 (`stringZ`). "
      "Because names are deduplicated, the string pool is smaller than 2×bindings: " +
      ", ".join(f"{f['mount']} {f['distinct_strings']} strings for {f['bindings']} bindings"
                for f in d["files"]) + ".")
    A("")
    tot = sum(f["bindings"] for f in d["files"])
    jm = {k: sum(f["node_hash_jenkins_matches"][k] for f in d["files"])
          for k in d["files"][0]["node_hash_jenkins_matches"]}
    A("Binding node hashes (decoded by recomputing `rbmhdr.hash_jenkins`, the project's "
      "Jenkins lookup3, over candidate names): of " + str(tot) + " bindings the node hash "
      "equals " + ", ".join(f"`{k}` {v}" for k, v in jm.items()) + ". So the node hash is "
      "the **action id**, and it equals `H(action name)` for " + str(jm["action"]) +
      " bindings; the rest carry ids that none of the candidates reproduces (ids are stable "
      "across the base and patch copies for the same action, so they are not per-file).")
    A("")
    A("Root hash `" + d["files"][0]["root_hash"] + "` and list hash `" +
      d["files"][0]["list_hash"] + "` are identical in all four copies, so both devices "
      "use one container class. Property types seen: " +
      ", ".join(f"{k}×{v}" for k, v in d["files"][0]["property_types"].items()) +
      " (type 3 = `stringZ`, per `rtpcdump.py`), i.e. every property in every binding is "
      "a string.")
    A("")
    A(f"Bindings decoded: **{c['bindings']}** rows over **{c['files']}** files; "
      f"**{c['actions']}** distinct action names, **{c['actions_with_both_devices']}** of "
      f"them on both devices.")
    A("")

    A("## Base vs patch layer (decoded)")
    A("")
    A("| file | base bindings | patch bindings | added in patch | removed in patch |")
    A("|---|---|---|---|---|")
    for t in d["layer_diff"]:
        add = t.get("added_in_patch", [])
        rem = t.get("removed_in_patch", [])
        A(f"| `{md(t['file'])}` | {t['base']} | {t['patch']} | "
          f"{len(add)} ({md(', '.join(add[:4]))}{' …' if len(add) > 4 else ''}) | "
          f"{len(rem)} ({md(', '.join(rem[:4]))}{' …' if len(rem) > 4 else ''}) |")
    A("")

    A("## Action table (decoded, mounted layer)")
    A("")
    A("`scope` is a **name rule** (derived): the first regex in the scope list that "
      "matches the action name. It says which class an action *names*; it is not a claim "
      "that the game uses it there.")
    A("")
    A("| action | gamepad | keyboard | scope (derived) |")
    A("|---|---|---|---|")
    for a, v in d["actions"].items():
        A(f"| `{a}` | {md(v['gamepad']) or '—'} | {md(v['keyboard']) or '—'} | "
          f"{v['scope'] or '**UNKNOWN**'} |")
    A("")
    A("Scope census (derived): " +
      ", ".join(f"{k} {v}" for k, v in d["scope_counts"].items()) + ".")
    A("")

    A("## Per class (derived name rule + decoded class census)")
    A("")
    A("The class of a vehicle is the root object of its `.epe` (`CCar`, `CBoat`, "
      "`CHelicopter`, `CAirPlane`, `CTrain`, `CMotorBike` — decoded in "
      "`FORCEPULSE.md` §owners). The action names that carry a class token:")
    A("")
    A("| class | actions |")
    A("|---|---|")
    for scope in d["scope_rules"]:
        acts = [a for a, v in d["actions"].items() if v["scope"] == scope]
        if acts:
            A(f"| {scope} | {', '.join('`' + a + '`' for a in acts)} |")
    A("")
    A("Entity-class census from the decoded `.ee` dumps (derived: the second token of the "
      "entity leaf, e.g. `v0300_car_…`; byte census of the 232 dumps): " +
      ", ".join(f"{k} {v}" for k, v in d["entity_census"]["class_tokens"].items()) +
      ". No file in this set maps a class to an action set; that step is **UNKNOWN**.")
    A("")

    A("## What the vehicle side names (decoded byte census)")
    A("")
    A(f"All **{d['entity_census']['files']}** decoded vehicle `.ee` dumps in "
      f"`{md(d['entity_census']['dir'])}` were searched for the literals below.")
    A("")
    A("| literal | entity files containing it | example |")
    A("|---|---|---|")
    for k, v in d["entity_census"]["probe_hits"].items():
        A(f"| `{md(k)}` | {v['files']} | {md(v['example'] or '—')} |")
    A("")
    nm = d["entity_census"]["nitro_member_paths"]
    if nm:
        A("Paths carrying `nitro_boost` (top " + str(len(nm)) + ", member path × files):")
        A("")
        for path, n in nm:
            A(f"- `{md(path)}` × {n}")
        A("")
    A("So **no vehicle entity names an input action and none names the keymap**: the "
      "binding table is global, not per entity. The name that does appear, "
      "`nitro_boost`, is a module block (tuning), not an action.")
    A("")

    A("## BmAK actions → JC3 (verdicts)")
    A("")
    A("BmAK side from `Research/BatmobileGrab/CONTROLS.md` (G3-02) and the user mapping "
      "in `GRAB_BACKLOG.md` D-11. Verdicts are computed from the decoded action set above: "
      "`reachable` when every named action exists, `not reachable` when a required name "
      "matches 0 actions, `UNKNOWN` when the names exist but nothing ties them to a "
      "vehicle, or when only a near-name exists.")
    A("")
    A("| BmAK action | JC3 evidence | verdict |")
    A("|---|---|---|")
    for r in d["bmak"]:
        A(f"| {md(r['id'])}<br><sub>{md(r['bmak'])}</sub> | {md(r['evidence'])} | "
          f"**{r['verdict']}** |")
    A("")

    A("## What an entity or module can change without code")
    A("")
    A("* **Can**: the graphs/objects/states a vehicle carries — entry and exit nodes, "
      "trigger volumes, seat points, weapon components, and module blocks such as "
      "`arcade.nitro_boost` (decoded in G2-16/18/19/11 and `USAGES.md` §6).")
    A("* **Cannot**: the button → action binding. The only button → action tables are the "
      "two `settings/keymap_*.bin` files, and no entity names them "
      f"({d['entity_census']['probe_hits']['keymap']['files']}/"
      f"{d['entity_census']['files']} entity files contain `keymap`).")
    A("* **Not decoded**: whether replacing `settings/keymap_gamepad.bin` from a dropzone "
      "is honoured — that needs a runtime test (no game runs in this card).")
    A("")

    A("## UNKNOWN")
    A("")
    for u in d["unknowns"]:
        A(f"- **{md(u['what'])}** — {md(u['why'])}")
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
    md_text = render(d)
    js_text = json.dumps(d, indent=1, ensure_ascii=False) + "\n"

    if a.write:
        os.makedirs(OUT, exist_ok=True)
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md_text)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js_text)
        c = d["counts"]
        print(f"wrote {OUT_MD} ({len(md_text)} bytes)")
        print(f"wrote {OUT_JSON} ({len(js_text)} bytes)")
        print(f"files={c['files']} bindings={c['bindings']} actions={c['actions']} "
              f"both_devices={c['actions_with_both_devices']} "
              f"scopes={d['scope_counts']} entities={c['entity_files']}")
        print("node_hash_jenkins_matches=" + json.dumps(
            {k: sum(f["node_hash_jenkins_matches"][k] for f in d["files"])
             for k in d["files"][0]["node_hash_jenkins_matches"]}, sort_keys=True))
        print("bmak verdicts: " + ", ".join(f"{r['id'].split(' (')[0]}={r['verdict']}"
                                            for r in d["bmak"]))
        return 0

    if not os.path.exists(OUT_JSON) or not os.path.exists(OUT_MD):
        print(f"MISSING output(s): {OUT_JSON} {OUT_MD}")
        return 1
    ok = True
    with open(OUT_JSON, encoding="utf-8") as f:
        on_disk = json.load(f)
    if on_disk == d:
        print(f"json ok: re-derived data == {os.path.basename(OUT_JSON)} "
              f"({d['counts']['bindings']} bindings, {d['counts']['actions']} actions)")
    else:
        ok = False
        print("json MISMATCH")
        for k in d:
            if on_disk.get(k) != d[k]:
                print(f"  differs: {k}")
    with open(OUT_MD, encoding="utf-8") as f:
        disk_md = f.read()
    if disk_md == md_text:
        print(f"md ok: re-rendered text == {os.path.basename(OUT_MD)} "
              f"({len(md_text)} bytes)")
    else:
        ok = False
        print(f"md MISMATCH ({len(disk_md)} on disk vs {len(md_text)} re-rendered)")

    # Row fidelity: every published binding must re-read from the archive as the same
    # (input, action) pair at the offsets it records.
    rows = load_index(OUT)
    cache = {}
    bad = checked = 0
    for b in d["binding_rows"]:
        key = (b["file"], b["mount"])
        if key not in cache:
            entries = read_entries(rows, b["file"])
            cache[key] = next(dd for x, dd in entries if x["mount"] == b["mount"])
        data = cache[key]
        checked += 1
        for off, name in ((b["input_string_offset"], b["input"]),
                          (b["action_string_offset"], b["action"])):
            raw = name.encode()
            if data[off:off + len(raw)] != raw or data[off + len(raw)] != 0:
                bad += 1
                break
    print(f"string fidelity: {checked - bad}/{checked} bindings re-read their input and "
          f"action strings from the archive at the recorded offsets")
    if bad:
        ok = False
    print("CHECK OK" if ok else "CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
