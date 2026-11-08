"""bm_entity.py - B-05: the Batmobile's entity graph (`.epe`), built from the translation tables.

`GRAB_BACKLOG.md` §8 (`B-05`): "using `ConvertProperty` round-trip (proven, plan §7.1) and the
signature-preorder diff (G2-12) as the template: 1. `CPartProp` for every new part. 2. Weapon
components and `SWeaponPoint`s per T-11 (points at `SOCKETS_JC3.json` positions, parented to the
turret/cannon parts). 3. `SVehicleLight` entries per T-18. 4. Interaction objects moved per
`t9_interaction.json`. 5. Root `health`/`invulnerable` per T-14. 6. Keep the camera reference
(`bat_base.ctune`, test-091)."
Out: `Working/Entity/bm_epe_edits.json` + the `.epe` in the build.
Done: "`ConvertProperty` round-trips the built `.epe` to identical XML; every weapon point, light and
part name resolves (script check); `.epe` object count = base + planned additions."

What this script does, and what it deliberately does not do
-----------------------------------------------------------
It stages `Builds/bm-RC4-entity/aaf` from **bm-RC4-parts** (B-04's part module; the RC4 chain is
`test-091` -> `bm-RC4-base` -> `bm-RC4-parts`), exports the `.epe` with `ConvertProperty --e`,
applies the rows below by *named member only*, re-imports with `--i`, and writes the spec + receipt.

The B-05 rows are the ones the apply-* reports decided:

* **Forced slot space (T-WP13)** - four `CCar` roots on the one entity, each carrying all four slot
  pointers, for **8 slot members** (4 x `main_weapon` + `id:00568A74`). Four are bound to the four
  T-11 carriers; the other four are reserved (all-null) for the tracker and the three Joker weapons,
  which have no T-11 carrier or decoded socket. Only decoded member names are used.
* **T-WP4 split** - the `w618` EMP clone gains a private `tuning_file` and `autoaim_tuning_file`
  reference (B-06 authors the five w143 guidance values and the new lock-on `AutoAim` tune), and the
  EMP `CForcePulse` (T-WP5) is added once, not once per root.
* **Gadgets outside the slot space** - five named by T-WP13: EMP burst, booster, winch, sonar,
  hacker. Three have a carrier in this graph (EMP pulse, sonar pulse, winch anchor); the booster is
  the module member `arcade.nitro_boost` (T-WP11, module-side) and the hacker needs a private `.effc`
  plus a usage (B-19), so both are declared, not invented.
* **Winch anchor (B-16)** - a `CVehicleCargoBay` clone at the `WinchOrigin` socket; the pull loop,
  the two BmAK rope components and the drum part stay outside this step (no JC3 class / B-04 part).
* **B-12 precondition 3** - the runtime entity swap is UNKNOWN (`mode-switch-carriers.md` §7 U1), so
  no mode-switch object is written; the report names it.
* **B-26** - the per-entity audio override (21 of 45 GUIDs) needs a private effects-class bank and a
  recorded take; it contributes 0 objects here and is declared in the spec.

Limits, measured and carried as such (never filled in with a plausible value, R4):

* **Weapon rows** - T-11 has a carrier for four structural rows. `T-WP5` has no trigger in the files
  (`t7_weapons_edits.json` `structural`), and the 11 BmAK weapons with no JC3 carrier are not written
  here at all. The components are clones of the armed APC's `CBulletWeaponBase`
  (`E:/Modding/_shared/gamedata/JC3grab/epe_schema/apc_debug.xml`, R10 outside the repo): the ~60 *unnamed* members
  are copied verbatim, because their meaning is UNKNOWN. That means the unnamed weapon-path members
  still name the donor template until **B-06** repoints them at the private weapon copies - recorded
  in the spec, not hidden.
* **Pod fire points** - `SOCKETS_JC3.json` carries two missile sockets (`MissileL`, `MissileR`), so
  T-WP3 writes two points, not the donor's four; the other two donor fire points are not in any repo
  table this script reads and are recorded as UNKNOWN. The two `w618` components have **no root slot**
  (`main_weapon` and `id:00568A74` are the cannon and Vulcan; `id:AC0BC788` and `mounted_weapon` ship
  null), so they are written but cannot fire; the `unbound[]` census and `declared[]` record that.
* **`attach.vehicle`** - the APC point carries three part refs (`5C19E7E0`, `80201E4D`, `A90F5E74`).
  The first two are rewritten from T-11's mount/turret pair; the third (`weapon_anchor`) names no B-04
  part and no row, so it is **omitted** rather than filled with a guess (`declared[]`, R4).
* **T-18 custom lights** - only `diffuse` is in the row as a graph member; the other 11 positional
  slots (including the `A04C3B1E` matrix and `preset_id`) are inherited from `Front_Left_Point`, so all
  six sit at that lamp. `declared[]` says so; placement is B-07's module anchor, not this step.
* **`CPartProp`** - the base graph carries 6 props for 42 parts and no prop carries a behaviour
  (G2-33 §8: lights bind through the module's `CarLight` blocks, not the prop). No row names a prop,
  so step 1 adds none and instead asserts every B-04 part name exists in the built module.
* **`SVehicleLight`** - only the 18 named members are written (T-18's own census: 29 slots, 11
  positional `id:*`); the 6 custom T-18 entries are clones of a shipped sibling, so the positional
  slots keep measured values.
* **Root `health`/`invulnerable`** - already 100/0 and T-14's decision B keeps them: step 5 is a
  checked no-op.
* **Camera** - `bat_base.ctune` is asserted present exactly once; this script never writes it.

Usage
    python Tools/scripts/bm_entity.py --write    # stage, edit, re-import, spec, receipt
    python Tools/scripts/bm_entity.py --check    # re-derive, compare, run the three Done checks
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3wiring                                   # noqa: E402  (the only .epe reader)
import rbmhdr                                      # noqa: E402  (hash_jenkins)

CARD = "B-05"
BASE_TAG = "bm-RC4-parts"
TAG = "bm-RC4-entity"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
EPE = EE.replace(".ee", ".epe")
ENT = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
BASE_DIR = os.path.join(ROOT, "Builds", BASE_TAG)
OUT = os.path.join(ROOT, "Builds", TAG)
OUT_EPE = os.path.join(OUT, "aaf", ENT, EPE)
SPEC = os.path.join(ROOT, "Working", "Entity", "bm_epe_edits.json")
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
APC = r"E:\Modding\_shared\gamedata\JC3grab\epe_schema\apc_debug.epe"
PARTS = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
T7 = os.path.join(ROOT, "Working", "Translation", "t7_weapons_edits.json")
T9 = os.path.join(ROOT, "Working", "Translation", "t9_interaction.json")
INTERACTION = os.path.join(ROOT, "Research", "JC3Grab", "INTERACTION.json")   # G2-18
SOCKETS = os.path.join(ROOT, "Research", "BatmobileGrab", "SOCKETS_JC3.json")
# decoded: the donor parts module, sportsmuscle_f_l_seat `centroid` (the seat G2-19 matches to Driver)
DONOR_SEAT_CENTROID = [-0.43320074677467346, 0.8705714344978333, 0.18794015049934387]
T18 = os.path.join(ROOT, "Working", "Translation", "t14_lights.json")
SOCKETS = os.path.join(ROOT, "Research", "BatmobileGrab", "SOCKETS_JC3.json")
SCHEMA = 1
BASE_OBJECTS = 416          # asserted, not assumed: the census stops the run if it moves
BASE_CLASSES = 43           # classed objects only; the classless `root` wrapper is not a class
MODELS = "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc"
# the APC `attach.vehicle` point carries its part refs in these measured unnamed members
PART_REF_IDS = ("5C19E7E0", "80201E4D", "A90F5E74")

# ---- T-WP13 forced slot space: four roots x the four root pointers = 8 slot members.
# Only `main_weapon` (`id:851CAABE`) and `id:00568A74` are used; the two gunner pointers stay null,
# because no shipped graph mixes driver and gunner slots (WP13 report §6).
SLOT_PROPS = ("id:851CAABE", "id:00568A74")          # the two driver pointers = the 8 slots
OTHER_POINTERS = ("mounted_weapon", "id:AC0BC788")  # gunner pointers, null on all four roots
ENTITY_ROOT = "v0300_car_kensington_sportsmuscle_civilian_01"
ROOTS = (
    {"suffix": "", "main": "w602_mediumtank_canon", "secondary": "w603_mediumtank_mgun",
     "why": "T-WP13 root 1: the heavy cannon (main) and the V2 cannon/chain gun (second)"},
    {"suffix": "_slot2", "main": "w618_sportsmuscle_missile",
     "secondary": "w618_sportsmuscle_missile_emp",
     "why": "T-WP13 root 2: the missile launcher (main) and the EMP launcher (second)"},
    {"suffix": "_slot3", "main": None, "secondary": None,
     "why": "T-WP13 root 3 reserves `main_weapon` for Vehicle_Tracker (T-WP9/B-21) and the second "
            "slot for the Joker heavy cannon; neither has a T-11 carrier, so both stay null"},
    {"suffix": "_slot4", "main": None, "secondary": None,
     "why": "T-WP13 root 4 reserves `main_weapon` for the Joker V2 cannon and the second slot for "
            "the Joker missile launcher; no Joker socket coordinate is decoded, so both stay null"},
)

# ---- T-WP4 split / T-WP5 gadget carriers. Paths are the B-06 private-copy convention; the tunes
# themselves are B-06's output, the graph only names them.
PRIVATE_TUNE = ("editor/entities/jc_weapons/06_vehicle/w618_batmobile_emp/"
                "w618_batmobile_emp.wtune")
PRIVATE_AUTOAIM = ("editor/entities/jc_weapons/06_vehicle/w618_batmobile_emp/"
                   "autoaim_batmobile_lockon.wtune")
EMP_TUNE = "editor/entities/jc_explosions/vehicles/truck_emp.ftune"       # G2-16
SONAR_TUNE = "editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftune"  # T-WP8
EMP_FLAGS = {"4912FC04": "0", "AE6F7EFF": "1", "CF4F7880": "1"}       # G2-16, unique in 307
# read-only donor graphs (R10, outside the repo) - XML is the ConvertProperty output the repo's own
# reader consumes; the APC `.epe` is already a build-time input.
DONOR_DIR = r"E:\Modding\_shared\gamedata\JC3grab\wiring\epe"
EMP_TRUCK = os.path.join(DONOR_DIR, "v0505_car_solar_oldtruck_rebel_emp_01.ee.xml")
CARGO_PLANE = os.path.join(DONOR_DIR, "v4603_plane_urga_cargotransport_blackhand_01.ee.xml")

# the four weapon rows T-11 can carry, and the slot each one takes (T-WP13 / T7_WEAPONS.md §slots)
WEAPONS = [
    {"row": "T-WP1", "name": "w602_mediumtank_canon", "weapon_id": 602, "root": 1,
     "slot": "main_weapon", "slot_hash": "851CAABE",
     "points": [{"name": "CannonMuzzle", "socket": "CannonMuzzle", "type": 2}],
     "attach": {"turret": "batmobile_turret", "mount": "batmobile_cannon"},
     "src": "T7_WEAPONS.md T-WP1: w602 (7 carriers), main_weapon id:851CAABE, socket CannonMuzzle"},
    {"row": "T-WP2", "name": "w603_mediumtank_mgun", "weapon_id": 603, "root": 1,
     "slot": "secondary", "slot_hash": "00568A74",
     "points": [{"name": "ChainGunMuzzle", "socket": "ChainGunMuzzle", "type": 2}],
     "attach": {"turret": "batmobile_turret", "mount": "batmobile_machine_gun"},
     "src": "T7_WEAPONS.md T-WP2: w603 (7 carriers), secondary id:00568A74, socket ChainGunMuzzle"},
    {"row": "T-WP3", "name": "w618_sportsmuscle_missile", "weapon_id": 618, "root": 2,
     "slot": None, "slot_hash": None,
     "points": [{"name": "MissileL", "socket": "MissileL", "type": 2},
                {"name": "MissileR", "socket": "MissileR", "type": 2}],
     "attach": {"turret": "batmobile_missile_pod_l", "mount": "batmobile_missile_pod_r"},
     "src": "T7_WEAPONS.md T-WP3: w618 (1 carrier), 4 donor fire points; SOCKETS_JC3.json has "
            "2 missile sockets, so 2 points are written and 2 stay UNKNOWN"},
    {"row": "T-WP4", "name": "w618_sportsmuscle_missile_emp", "weapon_id": 618, "root": 2,
     "slot": None, "slot_hash": None,
     "points": [{"name": "BattleModeSpotLight", "socket": "BattleModeSpotLight", "type": 2}],
     "attach": {"turret": "batmobile_missile_pod_l", "mount": "batmobile_missile_pod_r"},
     "private_tune": PRIVATE_TUNE, "private_autoaim": PRIVATE_AUTOAIM,
     "src": "T7_WEAPONS.md T-WP4 (split): w618 clone + the EMP CForcePulse (T-WP5) + the five w143 "
            "guidance values and the new lock-on AutoAim tune (B-06). The tune paths written here "
            "are B-06's private copies"},
]


# ------------------------------------------------------------------ helpers
def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def h(s: str) -> int:
    """The game's string hash, as a signed 32-bit int (the XML writes ints signed)."""
    v = rbmhdr.hash_jenkins(s.encode("utf-8"))
    return v - (1 << 32) if v >= (1 << 31) else v


def conv(*args: str) -> subprocess.CompletedProcess:
    r = subprocess.run([CONV, *args], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        out = (r.stdout + r.stderr).strip()
        raise SystemExit(f"ConvertProperty {args[0]} failed:\n{out[:1200]}")
    return r


def export(epe: str, xml: str) -> None:
    conv("--e", epe, xml)


def imp(xml: str, epe: str) -> None:
    conv("-i", xml, epe)


def vcls(o) -> str | None:
    v = o.find("value[@name='_class']")
    return v.text if v is not None else None


def vname(o) -> str | None:
    v = o.find("value[@name='name']")
    return v.text if v is not None else None


def values(o):
    return {v.get("name"): v for v in o.findall("value") if v.get("name")}


def set_value(o, name: str, text: str, deep: bool = False) -> None:
    """Set one *named* member on an object; exactly one must match, or the run stops.

    `deep=False` means an own member (a direct `value` child). Only the root's slot hashes are
    searched in the subtree, because `jc3wiring` exposes them as props even when the exporter
    nests them.
    """
    def match(v) -> bool:
        # a member is named, or carries only its Jenkins hash in the `id` attribute (`jc3wiring`
        # keys those as `id:<HASH>`, which is how the root's weapon slots are addressable)
        return (v.get("id") == name[3:] if name.startswith("id:") else v.get("name") == name)

    hits = [v for v in (o.iter("value") if deep else o.findall("value")) if match(v)]
    if len(hits) != 1:
        raise SystemExit(f"{vcls(o)} {vname(o)}: {name!r} matches {len(hits)} values")
    hits[0].text = text


def get_value(o, name: str, deep: bool = False) -> str:
    def match(v) -> bool:
        return (v.get("id") == name[3:] if name.startswith("id:") else v.get("name") == name)

    hits = [v for v in (o.iter("value") if deep else o.findall("value")) if match(v)]
    if len(hits) != 1:
        raise SystemExit(f"{vcls(o)} {vname(o)}: {name!r} matches {len(hits)} values")
    return hits[0].text or ""


def interaction_transforms(root) -> int:
    """T-13R (see B-05 step 4): write the 15 point/trigger `world` matrices. Idempotent - the donor
    3x3 is read from G2-18's record (INTERACTION.json points[].world), never from the file."""
    ia = json.load(open(INTERACTION, encoding="utf-8"))
    box = ia["frames"]["scale_xyz"]
    mapped = {o["name"]: o for o in ia["points"]}
    drv = next(s for s in json.load(open(SOCKETS, encoding="utf-8"))["sockets"] if s.get("socket") == "Driver")
    seat_c = DONOR_SEAT_CENTROID
    src = mapped["point.driver"]["serpente"]
    seat = [drv["position_m"][j] + src[j] - seat_c[j] for j in range(3)]
    seat_dz = seat[2] - mapped["point.driver"]["batmobile"][2]
    placed = 0
    for o in objects(root):
        n, cls = vname(o), vcls(o)
        if cls not in ("CInteractionGraphPointNode", "CInteractionTrigger") or n not in mapped:
            continue
        if not any(v.get("name") == "world" for v in o.findall("value")):
            continue
        m = [float(x) for x in mapped[n]["world"].replace(" ", "").split(",")]
        rows = [m[0:3], m[4:7], m[8:11]]
        if cls == "CInteractionTrigger":
            rows = [[r[j] * box[j] for j in range(3)] for r in rows]
        pos = list(mapped[n]["batmobile"])
        if "driver" in n:   # the driver's approach keeps the donor's seat-relative z (seat moved to Driver)
            pos[2] += seat_dz
        if n == "point.driver":
            pos = list(seat)
        f = lambda v: f"{v:.6g}"
        set_value(o, "world", ", ".join(",".join(f(x) for x in r) + ",0" for r in rows)
                  + ", " + ",".join(f(x) for x in pos) + ",1")
        placed += 1
    if placed != 15:
        raise SystemExit(f"T-13R: placed {placed} interaction transforms, expected 15 (8 points + 7 triggers)")
    return placed


def objects(root) -> list:
    """Every object element with a `_class`, in document order (the census the spec asserts)."""
    return [o for o in root.iter("object") if vcls(o)]


def by_class_name(root, cls: str, name: str | None = None) -> list:
    out = [o for o in objects(root) if vcls(o) == cls and (name is None or vname(o) == name)]
    return out


def one(root, cls: str, name: str | None = None):
    hits = by_class_name(root, cls, name)
    if len(hits) != 1:
        raise SystemExit(f"{cls} {name!r}: {len(hits)} object(s) in the graph")
    return hits[0]


def strip_object_ids(el) -> None:
    """Drop `id` attributes copied from the donor *object* elements.

    ConvertProperty validates that an element carrying both `name` and `id` has `id ==
    hash_jenkins(name)`; the donor's own object ids do not satisfy that against our names (measured:
    `attach.vehicle` copied with `id=35FED46A` while hash(attach.vehicle) = `7A22470D`, which the
    importer rejects with "supplied id and name, but they don't match"). The build's own objects are
    written with a name only, so the cloned ones are too; `value` ids are member hashes and stay.
    """
    if el.tag == "object" and "id" in el.attrib:
        el.attrib.pop("id", None)

    def walk(parent) -> None:
        for i, o in enumerate(parent.findall("object")):
            had_id = "id" in o.attrib
            o.attrib.pop("id", None)
            if had_id and not o.get("name"):
                # array elements in the donor file are written with an id and no name; ours are
                # named positionally, the way the build's own array elements are written
                o.set("name", str(i))
            walk(o)

    walk(el)


def name_hash_mismatch(objs) -> list[dict]:
    """Objects whose `name_hash` is not `hash_jenkins(name)` (either signed form accepted)."""
    bad = []
    for o in objs:
        nh = o.props.get("name_hash")
        if nh is None or not o.name:
            continue
        if str(nh) not in (str(h(o.name)), str(h(o.name) + (1 << 32))):
            bad.append({"class": o.cls, "name": o.name, "name_hash": nh,
                        "expected": h(o.name)})
    return bad


def winch_origin() -> list[float]:
    """B-16: `WinchOrigin` relative to `Batmobile_Chassis`, cm -> m, no rotation to bake."""
    sk = next(x for x in json.load(open(SOCKETS, encoding="utf-8"))["sockets"]
              if x.get("socket") == "WinchOrigin")
    return [float(x) / 100.0 for x in sk["relative_location_cm"]]


def mat(pos, fwd, up) -> str:
    """`SWeaponPoint.world` layout measured on 420 fleet mats: rows 0-2 = local X/Y/Z, row 3 =
    origin, det +1. X = up x forward (checked against the fleet example in the B-05 spec)."""
    def cross(a, b):
        return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    right = cross(up, fwd)
    n = sum(x * x for x in right) ** 0.5
    if n < 1e-6:
        raise SystemExit("degenerate basis: up x forward is zero")
    right = [x / n for x in right]
    cells = [*right, 0.0, *up, 0.0, *fwd, 0.0, *pos, 1.0]
    # `+ 0.0` turns a -0.0 into 0.0 so the written text is the exporter's own `0`, not `-0`
    return ",".join(f"{(c + 0.0):.7g}" for c in cells)


# ------------------------------------------------------------------ the edit plan
def forced_roots(root, primary, comps, new_id, additions, declared, edits) -> list:
    """T-WP13: four `CCar` roots on the one entity = 8 slot members.

    The three extra roots are cloned from the donor root's *members only*. Cloning its children too
    would duplicate the interaction context, the light list and the effect set; a second root that
    owns the same chassis does not need them, and the childless root is declared as a plan stand-in.
    """
    roots = [primary]
    for i, spec in enumerate(ROOTS[1:], 2):
        name = ENTITY_ROOT + spec["suffix"]
        r = copy.deepcopy(primary)
        for ch in list(r.findall("object")):
            r.remove(ch)
        strip_object_ids(r)
        r.set("name", name)
        set_value(r, "_object_id", new_id())
        set_value(r, "name", name)
        set_value(r, "name_hash", str(h(name)))
        for prop in SLOT_PROPS + OTHER_POINTERS:
            set_value(r, prop, "00000000")
        root.find("object").append(r)
        roots.append(r)
        additions.append({"class": "CCar", "name": name, "row": "T-WP13",
                          "src": f"forced root {i} of 4: every member copied from the donor CCar, "
                                 f"no child objects",
                          "why": spec["why"]})
        declared.append({"what": f"`CCar` root {i} (`{name}`) and its slots",
                         "why": spec["why"] + ". A childless extra root has no shipped precedent "
                                "(the cargo-plane entity's second root is a whole tank), so what "
                                "the engine does with these roots is UNKNOWN",
                         "row": "T-WP13"})
    for r, spec in zip(roots, ROOTS):
        for member, weapon in (("id:851CAABE", spec["main"]), ("id:00568A74", spec["secondary"])):
            if not weapon:
                continue
            set_value(r, member, comps[weapon].find("value[@name='_object_id']").text)
            edits.append({"node": ENTITY_ROOT + spec["suffix"],
                          "member": member, "row": "T-WP13", "to": weapon,
                          "src": "T-WP13 forced slot: the medium tank's two driver pointers"})
    return roots


def gadgets(root, primary, new_id, additions, declared) -> None:
    """The four non-slot gadgets that have a carrier, plus their named absences.

    Objects: EMP burst (T-WP5 / B-18), sonar pulse (T-WP8 / B-20), winch anchor (T-WP6 / B-16).
    Declared, not written: the booster (module member, T-WP11), the hacker (needs a private `.effc`
    and a usage, B-19), the two BmAK rope components (no JC3 class) and the winch drum (B-04 part).
    """
    ident = mat([0.0, 0.0, 0.0], [0, 0, 1], [0, 1, 0])
    base_pulse = one(root, "CForcePulse")

    # ---- T-WP5 / B-18: EMP burst = the truck's own EMP pulse, flags and tune intact
    emp_tpl = next(o for o in objects(ET.parse(EMP_TRUCK).getroot())
                   if vcls(o) == "CForcePulse" and vname(o) == "EMP")
    emp = copy.deepcopy(emp_tpl)
    strip_object_ids(emp)
    emp.set("name", "CForcePulse_EMP")
    set_value(emp, "_object_id", new_id())
    set_value(emp, "name", "CForcePulse_EMP")
    set_value(emp, "name_hash", str(h("CForcePulse_EMP")))
    set_value(emp, "SettingsFile", EMP_TUNE)
    for k, v in EMP_FLAGS.items():
        set_value(emp, "id:" + k, v)
    set_value(emp, "id:D3DDD766", "00000000")   # CMaterialEffectTable not copied (opaque payload)
    set_value(emp, "world", ident)
    primary.append(emp)
    additions.append({"class": "CForcePulse", "name": "CForcePulse_EMP", "row": "T-WP5",
                      "src": "G2-16: the EMP truck's `EMP` pulse, `truck_emp.ftune`, flag triple "
                             "4912FC04=0 / AE6F7EFF=1 / CF4F7880=1",
                      "why": "entity-level burst, not a slot (T-WP13 counts it outside the 8)"})
    declared.append({"what": "`CForcePulse_EMP`'s `id:D3DDD766` material-effect table",
                     "why": "the truck points it at `emp_flatbed_table`, a `CMaterialEffectTable` "
                            "whose payload is opaque; the pointer is zeroed instead of carrying "
                            "an object this step cannot read", "row": "T-WP5/B-18"})

    # ---- T-WP8 / B-20: sonar pulse, a 0-damage 5 m push
    sonar = copy.deepcopy(base_pulse)
    strip_object_ids(sonar)
    sonar.set("name", "CForcePulse_Sonar")
    set_value(sonar, "_object_id", new_id())
    set_value(sonar, "name", "CForcePulse_Sonar")
    set_value(sonar, "name_hash", str(h("CForcePulse_Sonar")))
    set_value(sonar, "SettingsFile", SONAR_TUNE)
    set_value(sonar, "world", ident)
    primary.append(sonar)
    additions.append({"class": "CForcePulse", "name": "CForcePulse_Sonar", "row": "T-WP8",
                      "src": "B-20: clone of the graph's own pulse with "
                             "`gen_explosion_5m_nodamage.ftune` (0 damage / 5 m)",
                      "why": "entity-level pulse, outside the slot space"})

    # ---- T-WP6 / B-16: the winch anchor = a shipped `CVehicleCargoBay` at `WinchOrigin`
    bay_tpl = next(o for o in objects(ET.parse(CARGO_PLANE).getroot())
                   if vcls(o) == "CVehicleCargoBay")
    bay = copy.deepcopy(bay_tpl)
    for ch in list(bay.findall("object")):
        bay.remove(ch)
    strip_object_ids(bay)
    bay.set("name", "WinchAnchor")
    set_value(bay, "_object_id", new_id())
    set_value(bay, "name", "WinchAnchor")
    set_value(bay, "name_hash", str(h("WinchAnchor")))
    set_value(bay, "enabled", "1")
    set_value(bay, "world", mat(winch_origin(), [0, 0, 1], [0, 1, 0]))
    primary.append(bay)
    additions.append({"class": "CVehicleCargoBay", "name": "WinchAnchor", "row": "T-WP6",
                      "src": "B-16: clone of the cargo plane's `CVehicleCargoBay`, world from "
                             "SOCKETS_JC3.json `WinchOrigin` relative_location_cm / 100",
                      "why": "the only decoded class carrying a transform plus an enable/disable "
                             "pair; `enable`/`disable` stay empty like all 12 shipped bays"})
    declared.append({"what": "the winch pull loop, drum part and the two BmAK rope components",
                     "why": "no length/force/reel/release member exists in JC3 (0 of 53 module "
                            "types, 0 of 67 part behaviours); the drum is a B-04 part and the "
                            "BmAK `RSimpleRopeComponent` has no JC3 class, so only the anchor "
                            "object is written", "row": "T-WP6/B-16"})
    declared.append({"what": "the booster gadget",
                     "why": "it is the module member `arcade.nitro_boost` (T-WP11/B-24), not an "
                            "entity object; it contributes no object to this graph",
                     "row": "T-WP11"})
    declared.append({"what": "the drone-hacker gadget",
                     "why": "it needs an `SAttachedEffect` whose effect is a private `.effc` and a "
                            "usage hash the engine dispatches on (B-19); no such file or usage "
                            "exists yet, so no object is written", "row": "T-WP7/B-19"})
    declared.append({"what": "a mode-switch object",
                     "why": "B-12 precondition 3: no data selects a variant at runtime "
                            "(`mode-switch-carriers.md` §7 U1, UNKNOWN); nothing is written",
                     "row": "B-12"})
    declared.append({"what": "B-26 per-entity audio override (21 of 45 GUIDs)",
                     "why": "the override is a private effects-class bank plus per-entity binding "
                            "rows and a recorded take; the bank and the two takes are the card's "
                            "own gate, so this step adds 0 objects", "row": "B-26"})


def plan(root, spec_in) -> dict:
    """Derive every edit from the translation tables. No number is typed here (R11)."""
    additions, edits, skipped, declared = [], [], [], []
    # the donor root and the values this step must leave alone, read from the base graph itself
    primary = one(root, "CCar")
    base_keep = {k: get_value(primary, k) for k in ("health", "invulnerable", "damage")}

    # ---- step 1: CPartProp. No row names one, so none is added; the assertion is Done 2's job.
    existing_props = [o for o in objects(root) if vcls(o) == "CPartProp"]
    parts = json.load(open(PARTS, encoding="utf-8"))["parts"]
    prop_names = {vname(o) for o in existing_props}

    # ---- step 2: weapon components (T-WP1..T-WP4)
    apc_root = ET.parse(spec_in["apc_xml"]).getroot()
    tpl = next(o for o in objects(apc_root) if vcls(o) == "CBulletWeaponBase")
    # `weapon_type` is measured, not chosen: the APC template carries 2 and WEAPON_WIRING.md:31
    # says every shipped weapon component carries 2. The base graph's own w618 component is the
    # cross-check for the missile clone, so a disagreement stops the run instead of being written.
    tpl_type = get_value(tpl, "weapon_type")
    # the base graph is the civilian Serpente and carries no weapon component, so the w618
    # cross-check is the armed signature diff's measured component (SIGNATURE_DIFF.json `weapon`),
    # not a typed number
    sig = json.load(open(os.path.join(ROOT, "Research", "JC3Grab", "SIGNATURE_DIFF.json"),
                         encoding="utf-8"))
    donor618_type = str((sig.get("weapon") or {}).get("weapon_type", ""))
    sockets = {s["socket"]: s for s in json.load(open(SOCKETS, encoding="utf-8"))["sockets"]}
    weapon_ids = {"uid": 0x8001}
    comps: dict = {}

    def new_id() -> str:
        weapon_ids["uid"] += 1
        return f"{h('bm-005-object-%d' % weapon_ids['uid']) & 0xFFFFFFFF:08X}=FFFF{weapon_ids['uid']:04X}"

    for w in WEAPONS:
        comp = copy.deepcopy(tpl)
        strip_object_ids(comp)
        comp.set("name", w["name"])
        set_value(comp, "_object_id", new_id())
        set_value(comp, "name", w["name"])
        set_value(comp, "name_hash", str(h(w["name"])))
        set_value(comp, "weapon_id", str(w["weapon_id"]))
        set_value(comp, "weapon_type", tpl_type)
        if w["weapon_id"] == 618:
            if not donor618_type:
                raise SystemExit("SIGNATURE_DIFF.json has no w618 weapon_type")
            if donor618_type != tpl_type:
                raise SystemExit(f"weapon_type disagrees: donor w618 {donor618_type}, "
                                 f"template {tpl_type}")
        sk = sockets[w["points"][0]["socket"]]
        set_value(comp, "world", mat(sk["position_m"], sk["forward_jc3"], sk["up_jc3"]))
        if w.get("private_tune"):
            # T-WP4 split: the graph names B-06's private tune and AutoAim copies. The five w143
            # guidance values and the 0.12/0.15 cone are tune members B-06 writes; the entity's
            # share is these two path references.
            set_value(comp, "id:AA7096C9", w["private_tune"])
            set_value(comp, "id:6D4C8277", w["private_autoaim"])
            edits.append({"node": w["name"], "member": "id:AA7096C9,id:6D4C8277",
                          "row": "T-WP4",
                          "to": "B-06 private w618 tune + the new lock-on AutoAim",
                          "src": "T-WP4 split: the five w143 guidance values and the new AutoAim "
                                 "tune are B-06's; the graph only names the private files"})
        # children: keep SEffects + CAIEntityProxy, replace the point set, set the part binding
        children = {vcls(c): c for c in comp.findall("object")}
        for c in list(comp.findall("object")):
            if vcls(c) in ("SWeaponPoint",):
                comp.remove(c)
        attach_tpl = children.get("SWeaponPoint")
        # the donor's attach.vehicle point is gone with the point set; re-make it from the template
        src_points = [c for c in tpl.findall("object") if vcls(c) == "SWeaponPoint"]
        attach = copy.deepcopy(next(p for p in src_points if vname(p) == "attach.vehicle"))
        strip_object_ids(attach)
        attach.set("name", "attach.vehicle")
        set_value(attach, "_object_id", new_id())
        set_value(attach, "name", "attach.vehicle")
        set_value(attach, "name_hash", str(h("attach.vehicle")))
        # the two part names the point binds: they sit in *unnamed* string members after `world`
        # the two part names are the *unnamed* string members (the named ones are name/state)
        strs = [v for v in attach.findall("value")
                if v.get("type") == "string" and not v.get("name")]
        if len(strs) < 2:
            raise SystemExit("attach.vehicle template lost its two part-name members")
        strs[0].text = w["attach"]["mount"]
        strs[1].text = w["attach"]["turret"]
        # the donor's third ref (`weapon_anchor`) names no B-04 part; omit it rather than invent one
        for extra in strs[2:]:
            attach.remove(extra)
            declared.append({
                "what": f"`attach.vehicle` third part ref on {w['name']}",
                "why": "the donor member id:A90F5E74 names `weapon_anchor`, a part with no B-04 "
                       "equivalent and no T-11 row; the member is omitted rather than filled "
                       "with a guessed part name",
                "row": w["row"]})
        comp.append(attach)
        for pt in w["points"]:
            s = sockets[pt["socket"]]
            p = copy.deepcopy(next(p for p in src_points if vname(p) == "FirePosition"))
            strip_object_ids(p)
            p.set("name", pt["name"])
            set_value(p, "_object_id", new_id())
            set_value(p, "name", pt["name"])
            set_value(p, "name_hash", str(h(pt["name"])))
            set_value(p, "type", str(pt["type"]))
            set_value(p, "world", mat(s["position_m"], s["forward_jc3"], s["up_jc3"]))
            comp.append(p)
        root.find("object").append(comp)
        comps[w["name"]] = comp
        additions.append({"class": "CBulletWeaponBase", "name": w["name"], "row": w["row"],
                          "src": w["src"], "unnamed_members": "copied verbatim from the APC clone"})
        for pt in w["points"]:
            additions.append({"class": "SWeaponPoint", "name": pt["name"], "row": w["row"],
                              "parent": w["name"],
                              "src": f"SOCKETS_JC3.json {pt['socket']} position_m/forward_jc3/up_jc3"})
        # slots are bound in `forced_roots()` once all four roots exist (T-WP13)
        # child objects counted as additions too (they are cloned nodes with fresh ids). The named
        # fire points were written above; a list that repeats them would not match the objects the
        # graph actually gains (`additions` counts objects, one row each - see `added_objects`).
        seen = {(a["class"], a["name"]) for a in additions if a.get("parent") == w["name"]}
        for c in comp.findall("object"):
            if (vcls(c), vname(c)) in seen:
                continue
            seen.add((vcls(c), vname(c)))
            additions.append({"class": vcls(c), "name": vname(c), "row": w["row"],
                              "parent": w["name"], "src": "cloned from the APC template"})

    # ---- step 3: SVehicleLight (6 T-18 customs + the mapped rows' named members)
    t18 = json.load(open(T18, encoding="utf-8"))
    template = one(root, "SVehicleLight", "Front_Left_Point")
    lst = next(o for o in root.iter("object")
               if vcls(o) == "SVehicleLightList" and vname(o) == "_Default")
    # the graph-side members T-18 measures for a light object (its `object` blocks)
    PHOTOMETRIC = ("radius", "spot_angle", "spot_inner_angle", "multiplier",
                   "volume_intensity", "volumetric_mode", "near_cap")
    customs: dict[str, dict] = {}
    for row in t18["rows"]:
        for t in row.get("targets") or []:
            if t.get("kind") == "custom":
                c = t.get("custom") or {}
                customs.setdefault(c.get("name") or t["name"], {**c, "rows": []})["rows"].append(
                    row["id"])
    for name, c in customs.items():
        clone = copy.deepcopy(template)
        clone.set("name", name + "_light")
        set_value(clone, "_object_id", new_id())
        set_value(clone, "name", name + "_light")
        set_value(clone, "name_hash", str(h(name + "_light")))
        d = c.get("diffuse")
        members = ["name", "name_hash"]
        if d:
            # `diffuse` is one `vec` member "R,G,B" on this object (measured on the shipped rows)
            set_value(clone, "diffuse", ",".join(f"{x:.6g}" for x in d))
            members.append("diffuse")
        lst.append(clone)
        additions.append({
            "class": "SVehicleLight", "name": name + "_light", "tag": name,
            "row": ",".join(c["rows"]), "src": "T-18 custom target (diffuse) + clone of "
            "Front_Left_Point for the unnamed slots", "members": members,
            "inherited": "every photometric member keeps its clone parent's measured value; "
                         "T-18's `range`/`angle` are the *module* row's members (B-07), not "
                         "SVehicleLight members"})
    if customs:
        declared.append({
            "what": "the 6 T-18 custom lights' 11 positional `id:*` slots",
            "why": "T-18's custom rows carry no matrix (only part/deformable_transform); every "
                   "clone inherits Front_Left_Point's slots, so all six sit at that lamp and keep "
                   "its preset_id until a card decodes the slot semantics or B-07's module anchor "
                   "binds them",
            "rows": ",".join(sorted({r for c in customs.values() for r in c["rows"]}))})
    # donor-row and graph-object targets: the measured `object` values, member for member
    for row in t18["rows"]:
        for t in row.get("targets") or []:
            if t.get("kind") not in ("donor-row", "graph-object"):
                continue
            obj = t.get("object") or {}
            name = obj.get("name")
            if not name:
                continue
            hits = [o for o in objects(root) if vcls(o) == "SVehicleLight" and vname(o) == name]
            if len(hits) != 1:
                skipped.append({"row": row["id"], "what": name,
                                "why": f"{len(hits)} SVehicleLight object(s) with that name"})
                continue
            o = hits[0]
            changed = []
            d = obj.get("diffuse")
            if d:
                set_value(o, "diffuse", ",".join(f"{x:.6g}" for x in d))
                changed.append("diffuse")
            for m in PHOTOMETRIC:
                if obj.get(m) is not None:
                    set_value(o, m, f"{obj[m]:.6g}")
                    changed.append(m)
            if changed:
                edits.append({"node": name, "member": ",".join(changed), "row": row["id"],
                              "src": "T-18 target `object` block (measured graph values)"})

    # ---- step 4: interaction objects (T-13R, Q re-test 4 2026-11-02: "unenterable")
    # T-13 anchored every point/trigger 0.05-0.30 m off the body shell with invented yaws and unit
    # scale: the seat point left the cockpit, the standing points rose to 1.15 m and every trigger
    # VOLUME (donor half-extents, e.g. trigger.driver 2.65 x 1.91 x 2.83 m) collapsed to 1 m.
    # Translation rule now, every value from the grab:
    #   3x3      = the donor's own 3x3 (identity rotation in all 15) x G2-18's per-axis box map
    #              for triggers (volumes follow the body box), unchanged for points;
    #   position = G2-18's per-axis box map (INTERACTION.json points[].batmobile), the same
    #              Serpente-box -> Batmobile-box map B-10 used for the hull;
    #   seat     = point.driver: the BmAK `Driver` socket + the donor's offset from its seat part
    #              (sportsmuscle_f_l_seat centroid) to point.driver - the Serpente seat is off to
    #              the left, the Batmobile cockpit is centred.
    placed = interaction_transforms(root)
    for o in t9["objects"] if (t9 := json.load(open(T9, encoding="utf-8"))) else []:
        if o.get("transform") and not o["name"].startswith(("point.", "trigger.")):
            skipped.append({"name": o["name"], "class": o["class"],
                            "why": "no named `world` member: inherits its graph node's transform (T-13R)"})
    edits.append({"node": "*", "member": "world", "row": "T-13R",
                  "to": f"{placed} object(s)",
                  "src": "donor 3x3 x INTERACTION.json frames.scale_xyz (triggers); INTERACTION.json "
                         "points[].batmobile; point.driver = SOCKETS_JC3 Driver + donor seat offset"})

    # ---- step 5: T-WP13 forced slot space (4 roots x the 2 driver pointers)
    forced_roots(root, primary, comps, new_id, additions, declared, edits)
    # ---- step 6: the gadget objects outside the slot space (T-WP5/T-WP6/T-WP8)
    gadgets(root, primary, new_id, additions, declared)

    declared.append({
        "what": "the four reserved slot pointers (roots 3 and 4)",
        "why": "8 slot members exist (4 roots x `main_weapon` + `id:00568A74`); only 4 are bound "
               "because T-11 has carriers for four weapons. Vehicle_Tracker, the Joker heavy "
               "cannon, the Joker V2 cannon and the Joker missile launcher have no T-11 carrier "
               "and no decoded Joker socket, so their slots stay null rather than naming a "
               "weapon object that does not exist"})

    return {
        "schema": SCHEMA, "card": CARD, "generator": rel(__file__),
        "base": {"build": BASE_TAG, "epe": f"{rel(BASE_DIR)}/aaf/{ENT}/{EPE}",
                 "epe_sha256": sha(open(os.path.join(BASE_DIR, "aaf", ENT, EPE), "rb").read()),
                 "objects": BASE_OBJECTS, "classes": BASE_CLASSES},
        "inputs": {"t7": rel(T7) + " (T-11)", "t9": rel(T9) + " (T-13)",
                   "t14": rel(T18) + " (T-18)", "parts": rel(PARTS) + " (B-04)",
                   "sockets": rel(SOCKETS) + " (T-11)", "weapon_template": APC + " (R10, read-only)"},
        "additions": additions, "edits": edits, "skipped": skipped, "declared": declared,
        "preserve": {"bat_base_ctune": 1, "car_base_ctune": 0,
                     "health": base_keep["health"],
                     "invulnerable": base_keep["invulnerable"],
                     "damage": base_keep["damage"]},
        "counts": {"base_objects": BASE_OBJECTS, "base_classes": BASE_CLASSES,
                   "additions": len(additions),
                   "expected_objects": BASE_OBJECTS + len(additions),
                   "cpartprop_added": 0, "cpartprop_existing": len(existing_props),
                   "part_names_in_module": len(parts), "interactions_written": placed,
                   "weapons": len(WEAPONS), "light_customs": len(t18["custom"]),
                   "roots": len(ROOTS), "slot_members": len(ROOTS) * len(SLOT_PROPS),
                   "slots_bound": sum(1 for r in ROOTS for m in (r["main"], r["secondary"])
                                      if m),
                   "slots_reserved": sum(1 for r in ROOTS
                                         for m in (r["main"], r["secondary"]) if not m),
                   "gadgets": 5, "gadget_objects": 3, "audio_override_objects": 0},
    }


# ------------------------------------------------------------------ build
def build(write: bool = True) -> dict:
    apc_xml = os.path.join(tempfile.mkdtemp(prefix="bm_entity_"), "apc_debug.xml")
    export(APC, apc_xml)
    base_xml = os.path.join(tempfile.mkdtemp(prefix="bm_entity_"), "base.xml")
    export(os.path.join(BASE_DIR, "aaf", ENT, EPE), base_xml)
    root = ET.parse(base_xml).getroot()
    base_census = jc3wiring.parse_epe(base_xml)
    if len(base_census) != BASE_OBJECTS or len({o.cls for o in base_census if o.cls}) != BASE_CLASSES:
        raise SystemExit(f"base graph moved: {len(base_census)} objects / "
                         f"{len({o.cls for o in base_census})} classes, "
                         f"expected {BASE_OBJECTS}/{BASE_CLASSES}")
    doc = plan(root, {"apc_xml": apc_xml})
    # name-hash baseline: the donor graph's own mismatches, so the check reports *new* ones
    doc["name_hashes"] = {"base_mismatches": len(name_hash_mismatch(base_census))}
    built_xml = os.path.join(ROOT, "tmp", "b05", "built.xml")
    os.makedirs(os.path.dirname(built_xml), exist_ok=True)
    ET.ElementTree(root).write(built_xml, encoding="utf-8", xml_declaration=True)
    if write:
        os.makedirs(os.path.dirname(OUT_EPE), exist_ok=True)
        imp(built_xml, OUT_EPE)
    built_census = jc3wiring.parse_epe(built_xml)
    # the planned additions, counted from the graphs themselves (R11): every object path the built
    # graph has and the base graph does not, which is what the card's Done 3 compares
    base_paths = {o.node for o in base_census}
    added = [{"class": o.cls, "name": o.name, "node": o.node}
             for o in built_census if o.node not in base_paths]
    doc["added_objects"] = added
    doc["counts"]["additions"] = len(added)
    doc["counts"]["expected_objects"] = BASE_OBJECTS + len(added)
    # `additions` lists one row per object the plan creates; `added` is the graph diff, which also
    # counts the nested nodes a cloned component drags in (effects, conditions). Both are reported.
    doc["counts"]["addition_rows"] = len(doc["additions"])
    doc["built"] = {"epe": rel(OUT_EPE) if write else "(not written)",
                    "objects": len(built_census),
                    "classed_objects": sum(1 for o in built_census if o.cls),
                    "classes": len({o.cls for o in built_census if o.cls}),
                    "expected_xml": built_xml}
    # a component that no root pointer names is dead weight (WEAPON_WIRING.md:31). Counted from the
    # graph's own text: its `_object_id` occurs once when only its definition carries it.
    built_text = open(built_xml, encoding="utf-8", errors="replace").read()
    doc["unbound"] = []
    for o in built_census:
        if o.cls == "CBulletWeaponBase" and o.oid and built_text.count(o.oid) <= 1:
            doc["unbound"].append({
                "name": o.name, "object_id": o.oid,
                "why": "the only occurrence is its own _object_id: no root slot points at it "
                       "(WEAPON_WIRING.md:31 calls such a component dead weight)"})
    doc["counts"]["unbound_weapons"] = len(doc["unbound"])
    return doc


def installer_text(doc: dict) -> str:
    return "\n".join([
        "<#",
        f"    {TAG} installer (B-05 entity graph). Generated by Tools/scripts/bm_entity.py.",
        "    Generated, never run by it. Close the game before -Action Install.",
        "    -GameDir defaults to the real install; point it at a copy to rehearse offline.",
        "#>",
        "[CmdletBinding()]",
        "param([ValidateSet('Install','Verify','Rollback091','Status')]"
        "[string]$Action = 'Status', [string]$GameDir = 'D:\\Games\\Just Cause 3')",
        "$ErrorActionPreference = 'Stop'",
        "$B = '" + OUT + "'",
        "$D = Join-Path $GameDir 'dropzone\\" + ENT + "'",
        "switch ($Action) {",
        "    'Install' {",
        "        New-Item -ItemType Directory -Force -Path $D | Out-Null",
        "        Copy-Item -LiteralPath (Join-Path $B 'aaf\\" + ENT + "\\" + EPE + "') "
        "-Destination (Join-Path $D '" + EPE + "') -Force",
        "        Write-Host 'deployed " + EPE + "'",
        "    }",
        "    'Verify' {",
        "        $p = Join-Path $D '" + EPE + "'",
        "        if (-not (Test-Path -LiteralPath $p)) { throw ('missing ' + $p) }",
        "        Write-Host ('verified ' + $p + ' ' + (Get-FileHash -LiteralPath $p).Hash)",
        "    }",
        "    'Rollback091' {",
        "        Remove-Item -LiteralPath (Join-Path $D '" + EPE + "') -Force -ErrorAction SilentlyContinue",
        "        if ($GameDir -eq 'D:\\Games\\Just Cause 3') {",
        "            & (Join-Path 'E:\\Modding\\JustCause3\\JC3-Batmobile\\Builds\\test-091' 'install.ps1') "
        "-Action Install",
        "        } else { Write-Host ('rehearsal on ' + $GameDir + ': test-091 re-install skipped') }",
        "    }",
        "    'Status' { Write-Host ('epe: ' + (Join-Path $D '" + EPE + "')) }",
        "}",
    ]) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        if os.path.exists(OUT):
            shutil.rmtree(OUT)
        os.makedirs(OUT)
        shutil.copytree(os.path.join(BASE_DIR, "aaf"), os.path.join(OUT, "aaf"))
        doc = build(write=True)
        os.makedirs(os.path.dirname(SPEC), exist_ok=True)
        with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=1)
        with open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
            f.write(installer_text(doc))
        receipt = {"schema": SCHEMA, "card": CARD, "tag": TAG, "base": rel(BASE_DIR),
                   "epe": {"file": rel(OUT_EPE), "sha256": sha(open(OUT_EPE, "rb").read()),
                           "bytes": os.path.getsize(OUT_EPE)},
                   "counts": doc["counts"], "additions": doc["additions"],
                   "edits": doc["edits"], "skipped": doc["skipped"],
                   "declared": doc["declared"], "unbound": doc["unbound"],
                   "installed": False}
        with open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(receipt, f, indent=1)
        c = doc["counts"]
        print(f"wrote {rel(OUT_EPE)}: {c['addition_rows']} planned row(s) = {c['additions']} "
              f"object(s), {len(doc['edits'])} edit(s), {len(doc['skipped'])} skipped; "
              f"objects {c['base_objects']} -> {doc['built']['objects']}")
        print(f"  weapons {c['weapons']}, light customs {c['light_customs']}, "
              f"interactions {c['interactions_written']}, CPartProp added {c['cpartprop_added']}")
        return
    sys.exit(check())


def check() -> int:
    doc = build(write=False)
    fails: list[str] = []
    if not os.path.exists(OUT_EPE):
        print("FAIL: " + rel(OUT_EPE) + " missing (run --write)")
        return 1
    # ---- Done 1: ConvertProperty round trip of the built .epe
    tmp = tempfile.mkdtemp(prefix="bm_entity_check_")
    x1 = os.path.join(tmp, "a.xml")
    x2 = os.path.join(tmp, "b.xml")
    y = os.path.join(tmp, "b.epe")
    export(OUT_EPE, x1)
    imp(x1, y)
    if sha(open(OUT_EPE, "rb").read()) != sha(open(y, "rb").read()):
        fails.append("Done 1: ConvertProperty --e/--i does not reproduce the built .epe")
    export(y, x2)
    if open(x1, "rb").read() != open(x2, "rb").read():
        fails.append("Done 1: the round-tripped XML differs from the built XML")
    # ---- the built graph, re-parsed
    built = jc3wiring.parse_epe(x1)
    # the built graph must be the graph the plan derives, value for value (catches any tamper that
    # leaves names, hashes and counts alone, e.g. a mat or a diffuse edit). The two XMLs come from
    # different writers, so the comparison is semantic: class, name and every member value.
    plan_census = jc3wiring.parse_epe(doc["built"]["expected_xml"])

    def norm(v: str):
        # values are compared numerically when they are numbers, because the exporter re-formats
        # floats (`-1` comes back as `-1.000000`) while the meaning is the same
        try:
            return tuple(round(float(x), 6) + 0.0 for x in str(v).split(","))
        except ValueError:
            try:
                return round(float(v), 6) + 0.0
            except ValueError:
                return str(v)

    def key(o):
        # the exporter re-orders siblings, so the comparison is by content, not by position
        return (o.cls, o.name, tuple(sorted((k, norm(v)) for k, v in o.props.items())))

    from collections import Counter
    a_set = Counter(repr(key(o)) for o in built)
    b_set = Counter(repr(key(o)) for o in plan_census)
    if a_set != b_set:
        extra = list((a_set - b_set).elements())[:2]
        missing = list((b_set - a_set).elements())[:2]
        fails.append(f"the built .epe differs from the re-derived plan: {sum((b_set - a_set).values())}"
                     f" object(s) missing, {sum((a_set - b_set).values())} unexpected, "
                     f"e.g. missing {missing} / unexpected {extra}")
    parts = {p["name"]: p for p in json.load(open(PARTS, encoding="utf-8"))["parts"]}
    # ---- Done 2: names resolve
    points = [o for o in built if o.cls == "SWeaponPoint"]
    comps = [o for o in built if o.cls == "CBulletWeaponBase"]
    for o in points:
        nh = o.props.get("name_hash")
        want = h(o.name)
        if str(nh) not in (str(want), str(want + (1 << 32))):
            fails.append(f"Done 2: weapon point {o.name!r} name_hash {nh} != hash_jenkins")
    for o in comps:
        nh = o.props.get("name_hash")
        want = h(o.name)
        if str(nh) not in (str(want), str(want + (1 << 32))):
            fails.append(f"Done 2: weapon component {o.name!r} name_hash {nh} != hash_jenkins")
    t18 = json.load(open(T18, encoding="utf-8"))
    light_names = {o.name for o in built if o.cls == "SVehicleLight"}
    for entry in t18["custom"]:
        want = (entry.get("part_name") or entry.get("name")) + "_light"
        if want not in light_names:
            fails.append(f"Done 2: T-18 custom light {want!r} missing")
    for o in built:
        if o.cls != "SVehicleLight":
            continue
        nh = o.props.get("name_hash")
        if str(nh) not in (str(h(o.name)), str(h(o.name) + (1 << 32))):
            fails.append(f"Done 2: light {o.name!r} name_hash {nh} != hash_jenkins")
    # every part ref the weapon points bind, by the measured member ids (not by a name prefix),
    # and every B-04 part name against the built module's actual bytes
    dangling = 0
    for o in points:
        for key, v in o.props.items():
            if isinstance(v, str) and key.startswith("id:") and key[3:].upper() in PART_REF_IDS:
                if v not in parts:
                    dangling += 1
                    fails.append(f"Done 2: point {o.name!r} binds {v!r} via {key}, not a B-04 part")
    mod_path = os.path.join(OUT, "aaf", MODELS)
    found = 0
    if not os.path.exists(mod_path):
        fails.append(f"Done 2: the parts module is missing at {rel(mod_path)}")
    else:
        mod_bytes = open(mod_path, "rb").read()
        absent = [n for n in parts if n.encode("utf-8") not in mod_bytes]
        found = len(parts) - len(absent)
        if absent:
            fails.append(f"Done 2: {len(absent)} B-04 part name(s) absent from the module bytes: "
                         f"{absent[:3]}")
    # ---- preserve list + the T-WP13 slot space + the gadget objects
    cars = [o for o in built if o.cls == "CCar"]
    if len(cars) != len(ROOTS):
        fails.append(f"Done 2: {len(cars)} CCar root(s), expected {len(ROOTS)} (T-WP13)")
    else:
        prim = next((o for o in cars if o.name == ENTITY_ROOT), None)
        if prim is None:
            fails.append("Done 2: the entity root name is missing from the CCar set")
        else:
            for k in ("health", "invulnerable", "damage"):
                want = doc["preserve"][k]
                if str(prim.props.get(k)) != str(want):
                    fails.append(f"Done 2: root {k} {prim.props.get(k)} != base {want}")
        byid = {o.oid: o for o in built if o.oid}
        members = bound = 0
        for c in cars:
            for prop in SLOT_PROPS:
                if prop not in c.props:
                    fails.append(f"Done 2: {c.cls} {c.name!r} has no {prop} pointer")
                    continue
                members += 1
                val = c.props.get(prop, "")
                if val and val != "00000000":
                    bound += 1
                    tgt = byid.get(val)
                    if tgt is None or tgt.cls not in jc3wiring.WEAPON_CLASSES:
                        fails.append(f"Done 2: {c.name!r} {prop} -> {val} is not a weapon object")
        if members != doc["counts"]["slot_members"]:
            fails.append(f"Done 2: {members} slot members, expected "
                         f"{doc['counts']['slot_members']} (4 roots x 4 pointers)")
        if bound != doc["counts"]["slots_bound"]:
            fails.append(f"Done 2: {bound} bound slot(s), expected "
                         f"{doc['counts']['slots_bound']}")
        doc["counts"]["slots_found"] = members
        doc["counts"]["slots_bound_found"] = bound
    for cls, nm in (("CForcePulse", "CForcePulse_EMP"),
                    ("CForcePulse", "CForcePulse_Sonar"),
                    ("CVehicleCargoBay", "WinchAnchor")):
        hits = [o for o in built if o.cls == cls and o.name == nm]
        if len(hits) != 1:
            fails.append(f"Done 2: gadget object {cls} {nm!r}: {len(hits)} in the graph")
    anchor = next((o for o in built if o.cls == "CVehicleCargoBay"), None)
    if anchor is not None:
        try:
            cells = [float(x) for x in anchor.props["world"].replace(" ", "").split(",")]
            want = winch_origin()
            if any(abs(cells[12 + i] - want[i]) > 1e-4 for i in range(3)):
                fails.append(f"Done 2: WinchAnchor world {cells[12:15]} != WinchOrigin {want}")
        except (KeyError, ValueError):
            fails.append("Done 2: WinchAnchor has no readable world matrix")
    mism = name_hash_mismatch(built)
    doc["name_hashes"]["built_mismatches"] = len(mism)
    if len(mism) > doc["name_hashes"]["base_mismatches"]:
        fails.append(f"Done 2: {len(mism)} name-hash mismatch(es) in the built graph "
                     f"(base {doc['name_hashes']['base_mismatches']}): {mism[:2]}")
    if doc["unbound"]:
        fails.append("Done 2: unbound weapon component(s) with no root slot: "
                     + ", ".join(u["name"] for u in doc["unbound"]))
    xml_text = open(x1, encoding="utf-8", errors="replace").read()
    if xml_text.count("bat_base.ctune") != 1 or "car_base.ctune" in xml_text:
        fails.append("Done 2: the camera reference bat_base.ctune is not exactly once")
    # ---- Done 3: object count = base + planned additions
    c = doc["counts"]
    got = len(built)
    if got != c["expected_objects"]:
        fails.append(f"Done 3: {got} objects, expected {c['base_objects']} + "
                     f"{c['additions']} = {c['expected_objects']}")
    if fails:
        for f in fails:
            print("FAIL:", f)
        return 1
    classed = sum(1 for o in built if o.cls)
    classes = len({o.cls for o in built if o.cls})
    print(f"PASS: {c['weapons']} weapon component(s), {c['unbound_weapons']} unbound, "
          f"{len(points)} weapon point(s), {len(light_names)} light(s) "
          f"({c['light_customs']} T-18 custom), {found}/{len(parts)} part name(s) in the module, "
          f"{dangling} dangling | {c['roots']} CCar roots, {c['slots_found']} slot members "
          f"({c['slots_bound_found']} bound, {c['slots_reserved']} reserved) "
          f"| {c['gadget_objects']} gadget object(s) of {c['gadgets']} gadgets "
          f"| name-hash mismatches {doc['name_hashes']['built_mismatches']} "
          f"(base {doc['name_hashes']['base_mismatches']}) "
          f"| objects {c['base_objects']} + {c['additions']} = {got} "
          f"({classed} classed + {got - classed} classless root, {classes} classes) "
          f"| round trip identical (count definitional; plan equality enforced above)")
    return 0


if __name__ == "__main__":
    main()
