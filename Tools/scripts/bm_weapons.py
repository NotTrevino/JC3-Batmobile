"""bm_weapons.py - B-06: private weapon tunes for the full BmAK weapon set (RC4).

`GRAB_BACKLOG.md` §8 (`B-06`): "for each cloned JC3 weapon: copy its `.ee`/tunes to a new private
path (`editor/entities/jc_weapons/06_vehicle/w6xx_batmobile_<name>/…`), rename internal hashes,
apply `t7_weapons_edits.json`, point the `.epe` weapon components at the new paths. Never edit the
shipped `w6xx` files in place (R7)."

`Builds/bm-RC4-weapons` is staged from `Builds/bm-RC4-entity` (B-05's graph, 4 `CBulletWeaponBase`
components, 8 forced slot pointers). This card writes, as private copies:

  T-WP1  w602 cannon      fire_rate 2.0, velocity 400 m/s, tracer TTL 1.25 s   (3 writes)
  T-WP2  w603 Vulcan      fire_rate 0.138 s                                    (1 write)
  T-WP3  w618 missile     copy only, no numeric row                            (0 writes)
  T-WP4  w618 EMP clone   5 Fire-Leech guidance values + a lock-on AutoAim     (5 + 18 writes)
  B-15   riot cannon      damage 0, impulse, factors, fire_rate 0.75 + AutoAim  (4 + 18 writes)

Every value is patched **at its decoded `offset-in-file`**, so each file keeps its shipped size
(a ConvertAdf re-encode is not byte-identical: 14,224 -> 14,208 B). Each write is located by its
full ADF leaf path in the ConvertAdf XML (`bullet_weapon[0].tuning.base_tuning.fire_rate`), never
by "the first member with this name": `tuning` and `ai_tuning` share every name.

Values and their BmAK source numbers are listed per write in the manifest (`edits[].bmak`) and in
`tmp/freebuff/reports/build-d06-weapons-tunes.md`.

Usage
    python Tools/scripts/bm_weapons.py --write   # stage Builds/bm-RC4-weapons, copy+patch, manifest
    python Tools/scripts/bm_weapons.py --check   # re-derive, compare, values read back at offsets
    python Tools/scripts/jc3weapons.py --check --root Builds/bm-RC4-weapons   # Done 2 (build mode)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_entity as E                                # noqa: E402  (the one mat/hash/ConvertProperty set)
import jc3weapons as W                               # noqa: E402  (the ADF reader and tune sources)
import jc3wiring                                      # noqa: E402  (the only .epe reader)

CARD = "B-06"
BASE_TAG = "bm-RC4-entity"
TAG = "bm-RC4-weapons"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
EPE = EE.replace(".ee", ".epe")
ENT = "editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle"
BASE_DIR = os.path.join(ROOT, "Builds", BASE_TAG)
BASE_EPE = os.path.join(BASE_DIR, "aaf", ENT, EPE)
OUT = os.path.join(ROOT, "Builds", TAG)
OUT_EPE = os.path.join(OUT, "aaf", ENT, EPE)
SPEC = os.path.join(ROOT, "Working", "Weapons", "manifest.json")
T7 = os.path.join(ROOT, "Working", "Translation", "t7_weapons_edits.json")
WJSONL = os.path.join(ROOT, "Research", "JC3Grab", "WEAPONS.jsonl")
WSHARED = os.path.join(ROOT, "Research", "JC3Grab", "WEAPONS_SHARED.json")
INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
SIGDIFF = os.path.join(ROOT, "Research", "JC3Grab", "SIGNATURE_DIFF.json")
APC = r"E:\Modding\_gamedata\JC3grab\epe_schema\apc_debug.xml"
ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
SCHEMA = 2
WEP_DIR = "editor/entities/jc_weapons/06_vehicle/"
TUNE_ID = "AA7096C9"        # `tuning_file` (`SIGNATURE_DIFF.md` §"weapon component")
AIMA_ID = "6D4C8277"        # `autoaim_tuning_file` (WEAPON_WIRING.md:16)
GAME = os.environ.get("JC3_GAME", W.DEFAULT_GAME)
SHARED_DIR = "editor/entities/jc_weapons/00_shared/autoaim_tuning/"

# The BmAK source number behind each T-11 write. `WEAPONS.md` line numbers are the BmAK grab's.
T11_SRC = {
    ("T-WP1", "fire_rate"): "BmAK cannon FiringInterval 2.0 s (WEAPONS.md:553, `RVehicleWeapon."
                            "FiringInterval`); T-11 `decoded`",
    ("T-WP1", "velocity"): "BmAK `Projectile.Speed` 40000.0 UU/s = 400 m/s (WEAPONS.md:333, "
                           "export 15 tag @668); 1 UU = 1 cm",
    ("T-WP2", "fire_rate"): "BmAK Vulcan FiringInterval 0.138 s = 7.25 rounds/s (T-11 `decoded`; "
                            "field `RVehicleWeapon.FiringInterval`, WEAPONS.md:553)",
}

# The eight shipped tracer members (FX-16 §3). Only one has an exact BmAK source number; the rest
# are recorded as unchanged/UNKNOWN rather than set "for character".
TRACER_BLOCK = "bullet_base_tuning"

TUNES = [
    {"key": "cannon", "row": "T-WP1", "component": "w602_mediumtank_canon",
     "purpose": "the car's 60 mm heavy cannon (T-WP1), forced slot root 1",
     "src": ("weapon", "w602_mediumtank_canon"),
     "private": WEP_DIR + "w602_batmobile_cannon/w602_batmobile_cannon.wtunec",
     "edits": [{"from": "t7", "row": "T-WP1", "member": "fire_rate", "block": None},
               {"from": "t7", "row": "T-WP1", "member": "velocity", "block": None},
               {"row": "FX-16", "member": "tracer_time_to_live",
                "block": ".tuning." + TRACER_BLOCK + ".",
                "old": 0.0, "new": 1.25, "type": "float", "conf": "decoded",
                "bmak": "`Particles.Rocket.Batmobile_CanonTrail` ribbon `ParticleModuleLifetime."
                        "Lifetime` 1.25 s (export 2241 @96; FX-16 §7); 1:1 seconds"}],
     "autoaim": None},
    {"key": "vulcan", "row": "T-WP2", "component": "w603_mediumtank_mgun",
     "purpose": "the Vulcan (T-WP2), forced slot root 2",
     "src": ("weapon", "w603_mediumtank_mgun"),
     "private": WEP_DIR + "w603_batmobile_vulcan/w603_batmobile_vulcan.wtunec",
     "edits": [{"from": "t7", "row": "T-WP2", "member": "fire_rate", "block": None}],
     "autoaim": None},
    {"key": "missile", "row": "T-WP3", "component": "w618_sportsmuscle_missile",
     "purpose": "the missile launcher (T-WP3), forced slot root 3; copy only, no numeric row",
     "src": ("weapon", "w618_sportsmuscle_missile"),
     "private": WEP_DIR + "w618_batmobile_missile/w618_batmobile_missile.wtunec",
     "edits": [], "autoaim": None},
    {"key": "emp", "row": "T-WP4", "component": "w618_sportsmuscle_missile_emp",
     "purpose": "the EMP launcher (T-WP4), forced slot root 4: Fire-Leech guidance + lock-on aim",
     "src": ("weapon", "w618_sportsmuscle_missile"),
     "private": WEP_DIR + "w618_batmobile_emp_missile/w618_batmobile_emp_missile.wtunec",
     "edits": [
         {"row": "T-WP4", "member": "missile_turning_speed", "block": ".tuning.",
          "old": 0.0, "new": 300.0, "type": "float", "conf": "decoded",
          "bmak": "w143 Fire Leech guidance value transplanted by value (apply-weapon-slot-rows "
                  "§2); BmAK homing rate has no decoded member (`RBatmobileMissile.AccelRate` "
                  "absent, WEAPONS.md:193)"},
         {"row": "T-WP4", "member": "missile_turning_speed_random", "block": ".tuning.",
          "old": 0.0, "new": 60.0, "type": "float", "conf": "decoded",
          "bmak": "w143 Fire Leech guidance value (apply-weapon-slot-rows §2)"},
         {"row": "T-WP4", "member": "missile_acceleration[0]", "block": ".tuning.",
          "old": 200.0, "new": 65.0, "type": "float", "conf": "derived",
          "bmak": "BmAK missile acceleration target 65 (0.2 s -> 10 s bracket); w618's own 200 "
                  "is the shipped cannon-missile value (apply-weapon-slot-rows §2)"},
         {"row": "T-WP4", "member": "missile_acceleration_time[0]", "block": ".tuning.",
          "old": 5.0, "new": 10.0, "type": "float", "conf": "derived",
          "bmak": "BmAK missile acceleration bracket ends at 10 s (apply-weapon-slot-rows §2)"},
         {"row": "T-WP4", "member": "missile_acceleration_random[0]", "block": ".tuning.",
          "old": 0.0, "new": 5.0, "type": "float", "conf": "decoded",
          "bmak": "w143 Fire Leech acceleration random (apply-weapon-slot-rows §2)"}],
     "autoaim": {
         "private": WEP_DIR + "w618_batmobile_emp_missile/"
                    "autoaim_batmobile_emp_lockon.wtunec",
         "src": SHARED_DIR + "autoaim_vehicle_no_lockon_missile.wtunec",
         "purpose": "the EMP launcher's new lock-on AutoAim (T-WP4), typed like BmAK's "
                    "`RVehicle` lock; replaces `autoaim_vehicle_no_lockon_missile`",
         "edits": [
             {"member": "AngleThresholdNewTarget", "new": 0.12, "type": "float",
              "bmak": "fleet lock-on preset 0.12 turns (`autoaim_vehicle_lockon_missile`, "
                      "WEAPONS_SHARED.json); BmAK lock cone 40 deg has no confirmed member "
                      "(apply-weapon-slot-rows §10 U2)"},
             {"member": "AngleThresholdCurrentTarget", "new": 0.15, "type": "float",
              "bmak": "fleet lock-on preset 0.15 (`autoaim_vehicle_lockon_missile`)"},
             {"member": "MaxAimDistance", "new": 120.0, "type": "float",
              "bmak": "BmAK `RBatmobileMissileLauncher.LockOnRange` 12000 UU = 120 m "
                      "(WEAPONS.md:556; apply-weapon-slot-rows §2)"},
             {"member": "CanTargetVehicles", "new": 1, "type": "uint32",
              "bmak": "BmAK lock target type `RVehicle` (apply-weapon-slot-rows §2)"},
             {"member": "CanTargetRigidObjects", "new": 1, "type": "uint32",
              "bmak": "BmAK lock target type `RVehicle`; rigid objects kept (apply-weapon-slot-rows §2)"},
             {"member": "CanTargetCharacters", "new": 0, "type": "uint32",
              "bmak": "BmAK `RVehicle` lock must not target pedestrians (apply-weapon-slot-rows §2)"}]}},
    {"key": "riot", "row": "B-15", "component": None,
     "purpose": "the riot suppressor (B-15): a zero-damage, high-impulse round in a private copy "
                "of B-06's built cannon tune; no entity object exists yet, so it is unbound",
     "src": ("chain", "cannon"),
     "private": WEP_DIR + "riot_batmobile_suppressor/riot_batmobile_suppressor.wtunec",
     "edits": [
         {"row": "T-WP10", "member": "base_tuning.damage", "block": ".tuning.",
          "old": 1.0, "new": 0.0, "type": "float", "conf": "derived",
          "bmak": "riot mode has no damage value of its own; the cannon's `ChainGunDamage` 40 is "
                  "lethal-only (apply-riot-mode-rows §4)"},
         {"row": "T-WP10", "member": "base_tuning.impulse", "block": ".tuning.",
          "old": 0.0, "new": 100.0, "type": "float", "conf": "derived",
          "bmak": "`RBatmobileCannon.ImpactMomentum` 60000 (WEAPONS.md:680) and "
                  "`RBatmobileCannon.RiotSuppressorVillainImpulse` 6000 (WEAPONS.md:692); "
                  "clamped to the tune maximum 100 player / 40 AI"},
         {"row": "T-WP10", "member": "base_tuning.vehicle_impulse_factor", "block": ".tuning.",
          "old": 0.5, "new": 1.0, "type": "float", "conf": "derived",
          "bmak": "same impulse pair (WEAPONS.md:680, :692); no per-target attenuation is decoded"},
         {"row": "T-WP10", "member": "fire_rate", "block": None,
          "old": 2.0, "new": 0.75, "type": "float", "conf": "decoded",
          "bmak": "`RBatmobileCannon.RiotSuppressorFiringInterval` 0.75 s (WEAPONS.md:691)"}],
     "autoaim": {
         "private": WEP_DIR + "riot_batmobile_suppressor/riot_batmobile_suppressor_autoaim.wtunec",
         "src": SHARED_DIR + "autoaim_vehicle_mgun.wtunec",
         "purpose": "the riot suppressor's 7.5 deg cone (B-15), a private copy of the cannon's "
                    "current mgun AutoAim",
         "edits": [
             {"member": "AngleThresholdNewTarget", "new": 7.5, "type": "float",
              "bmak": "`RBatmobileCannon.RiotSuppressorLockOnAngle` 7.5 (WEAPONS.md:690)"},
             {"member": "AngleThresholdCurrentTarget", "new": 7.5, "type": "float",
              "bmak": "`RBatmobileCannon.RiotSuppressorLockOnAngle` 7.5 (WEAPONS.md:690)"},
             {"member": "StickyAimStartAngle", "new": 7.5, "type": "float",
              "bmak": "`RBatmobileCannon.RiotSuppressorLockOnAngle` 7.5 (WEAPONS.md:690); which "
                      "of the three is the cone is UNKNOWN (apply-riot-mode-rows §6.3)"}]}},
]

# Tracer members left exactly as shipped, with the reason (FX-16 §8/§9). Listed so the report can
# say what was *not* written as well as what was.
TRACER_UNCHANGED = [
    {"member": "tracer_fire_width", "w602": 0.5,
     "why": "already exact: the BmAK ribbon StartSize is 50 uu = 0.50 m (FX-16 §7/§8)"},
    {"member": "tracer_fire_length", "w602": 30.0,
     "why": "the ribbon's 250-uu field is labelled 'beam length' but its UE property is UNKNOWN "
            "(distance or segment count), so no value is written (FX-16 §7/§12.4)"},
    {"member": "tracer_fire_velocity", "w602": 900.0,
     "why": "the ribbon's VelocityOverLifetime values are not decoded; 900 is the streak's stretch "
            "rate, not the trail particle speed (FX-16 §12.5)"},
    {"member": "tracer_expand_width", "w602": 0.0,
     "why": "size-over-life curve not decoded and the member's unit is UNKNOWN (FX-16 §12.2)"},
    {"member": "smoke_trail_tile_size", "w602": 5.0,
     "why": "the BmAK sprite has no tile-size value in the grab (FX-16 §8)"},
    {"member": "tracer_per_smoke_trail", "w602": 1,
     "why": "the ribbon's 8/s spawn rate is a particle rate, not a per-tracer interval "
            "(FX-16 §8/§12.3)"},
    {"member": "bullets_per_tracer", "w602": 1,
     "why": "BmAK has no per-N-bullets tracer value (FX-16 §8)"},
    {"member": "tracer_texture_type", "w602": 1,
     "why": "enum already 1 on every vehicle bullet weapon; the enum->asset mapping is UNKNOWN "
            "(FX-16 §5/§12.1)"},
]


# ------------------------------------------------------------------ helpers
def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def read_json(p: str):
    return json.load(open(p, encoding="utf-8"))


def weapon_rows() -> dict[str, dict]:
    out = {}
    for line in open(WJSONL, encoding="utf-8"):
        rec = json.loads(line)
        out[rec["id"]] = rec
    return out


def t7_rows() -> dict[tuple[str, str], dict]:
    return {(e["row"], e["member"]): e for e in read_json(T7)["edits"]}


def conv(args: list[str]) -> None:
    r = subprocess.run([ADF, *args], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ConvertAdf {args[0]} failed:\n{(r.stdout + r.stderr)[:1200]}")


def export_xml(blob: bytes, name: str) -> str:
    tmp = os.path.join(ROOT, "tmp", "b06")
    os.makedirs(tmp, exist_ok=True)
    raw = os.path.join(tmp, name + ".wtunec")
    xml = os.path.join(tmp, name + ".xml")
    open(raw, "wb").write(blob)
    conv(["-e", raw, xml])
    return xml


def leaf_paths(xml: str) -> list[dict]:
    """Every ADF leaf with a byte offset: (`path`, offset, type, text) from ConvertAdf's XML.

    Paths are built from the ancestors' `name` attributes, with `[i]` on array elements, e.g.
    `bullet_weapon[0].tuning.base_tuning.fire_rate`. This is the only safe key: `tuning` and
    `ai_tuning` carry the same member names and offsets differ per block.
    """
    out: list[dict] = []

    def rec(el, prefix: str) -> None:
        kids = [c for c in el if c.tag == "member"]
        idx: dict[str, list] = {}
        leaf_i = 0
        for c in kids:
            n = c.get("name")
            off = c.get("offset-in-file")
            if off:                        # a value: named (structure member) or unnamed (array elt)
                path = (prefix + n) if n is not None else (prefix.rstrip(".") + f"[{leaf_i}]")
                if n is None:
                    leaf_i += 1
                out.append({"path": path, "offset": int(off, 16),
                            "type": c.get("type") or "float", "text": (c.text or "").strip()})
                continue
            if n is None:               # an array element structure: the parent name owns the index
                rec(c, prefix)
                continue
            if n not in idx:
                many = sum(1 for k in kids if k.get("name") == n) > 1
                arr = many or (c.get("gbltype") or "") in ("InlineArray", "Array")
                idx[n] = [0, arr]
            i = idx[n][0]
            idx[n][0] += 1
            # an InlineArray's *leaves* carry the index (the name is the array); a reference
            # Array's *elements* are unnamed structures, so the name carries the index
            inline = (c.get("gbltype") or "") == "InlineArray"
            rec(c, prefix + (f"{n}[{i}]." if (idx[n][1] and not inline) else f"{n}."))

    for inst in ET.parse(xml).getroot().findall("instances/instance"):
        rec(inst, "")
    return out


def locate(leaves: list[dict], member: str, block: str | None, require: int | None = 1) -> list[dict]:
    hits = [l for l in leaves
            if (l["path"] == member or l["path"].endswith("." + member))
            and (block is None or block in l["path"])]
    if require is not None and len(hits) != require:
        raise SystemExit(f"{member} (block {block}): {len(hits)} leaf/leaves, expected {require}: "
                         f"{[h['path'] for h in hits][:8]}")
    if not hits:
        raise SystemExit(f"{member} (block {block}): no leaf")
    return hits


def pack_at(blob: bytearray, off: int, typ: str, val) -> None:
    if typ == "float":
        struct.pack_into("<f", blob, off, float(val))
    elif typ == "uint32":
        struct.pack_into("<I", blob, off, int(val))
    elif typ == "uint8":
        struct.pack_into("<B", blob, off, int(val))
    else:
        raise SystemExit(f"unsupported member type {typ}")


def unpack_at(blob: bytes, off: int, typ: str):
    if typ == "float":
        return struct.unpack_from("<f", blob, off)[0]
    if typ == "uint32":
        return struct.unpack_from("<I", blob, off)[0]
    if typ == "uint8":
        return struct.unpack_from("<B", blob, off)[0]
    raise SystemExit(f"unsupported member type {typ}")


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def same(a, b) -> bool:
    return abs(float(a) - float(b)) <= 1e-6 * max(1.0, abs(float(b)))


# ------------------------------------------------------------------ sources
def tune_source(weapon: str) -> dict:
    """The shipped `.wtunec` copy, pinned by sha1 against WEAPONS.jsonl."""
    rec = weapon_rows()[weapon]
    path = os.path.join(W.WROOT, weapon, weapon + ".wtunec")
    if not os.path.exists(path):
        raise SystemExit(f"no decoded tune for {weapon} under {path} "
                         f"(E:/Modding/_gamedata/JC3grab/weapons/, R10)")
    blob = open(path, "rb").read()
    h = sha1(blob)
    matches = [s for s in rec["sources"] if s["sha1"] == h]
    if not matches:
        raise SystemExit(f"{weapon}: extracted tune ({h}) is not a copy WEAPONS.jsonl recorded")
    src = matches[0]
    dsize = [d["size"] for d in rec["dir_files"] if d["path"] == src["path"]]
    return {"kind": "weapon", "id": weapon, "game_path": src["path"], "mount": src["mount"],
            "sha1": h, "bytes": len(blob), "blob": blob,
            "dir_file_bytes": dsize[0] if dsize else None}


def shared_source(path: str) -> dict:
    """A shared AutoAim `.wtunec` read straight from the archive, pinned by WEAPONS_SHARED.json."""
    best = W.best_by_path(W.load_rows())
    if path not in best:
        raise SystemExit(f"shared tune {path} is not in the index")
    blob = W.read_row(best[path], GAME)
    rec = next((s for s in read_json(WSHARED) if s.get("path") == path), None)
    if rec is None:
        raise SystemExit(f"{path} is not in WEAPONS_SHARED.json")
    h = sha1(blob)
    hit = [s for s in rec["sources"] if s["sha1"] == h]
    if not hit:
        raise SystemExit(f"{path}: archive bytes ({h}) are not the recorded shared tune")
    return {"kind": "shared", "id": rec["name"], "game_path": path, "mount": hit[0]["mount"],
            "sha1": h, "bytes": len(blob), "blob": blob, "dir_file_bytes": None}


def resolve_source(spec) -> dict:
    if spec[0] == "weapon":
        return tune_source(spec[1])
    if spec[0] == "shared":
        return shared_source(spec[1])
    raise SystemExit(f"unknown source {spec}")


# ------------------------------------------------------------------ the plan
def resolve_edits(spec: dict, src: dict, xml: str, t7: dict, report: list[dict]) -> list[dict]:
    """Turn each edit spec into `{row, member, path, offset, old, new, type, bmak, ...}`."""
    leaves = leaf_paths(xml)
    rows = []
    for e in spec["edits"]:
        if e.get("from") == "t7":
            t = t7.get((e["row"], e["member"]))
            if t is None:
                raise SystemExit(f"{e['row']} {e['member']} missing from {os.path.basename(T7)}")
            e = {**e, "old": float(t["old"]), "new": float(t["new"]), "type": "float",
                 "conf": t["conf"], "behaviour": t["behaviour"], "take": t["take"],
                 "bmak": T11_SRC.get((e["row"], e["member"]), "T-11 ledger")}
        if "member" not in e:
            raise SystemExit(f"edit without member: {e}")
        hits = locate(leaves, e["member"], e.get("block"))
        h = hits[0]
        old, new = e.get("old"), e["new"]
        cur = num(h["text"])
        if old is not None and cur is not None and not same(cur, old):
            raise SystemExit(f"{spec['key']}: {h['path']} reads {h['text']}, expected old {old}")
        typ = e.get("type") or ("float" if h["type"] == "float" else h["type"])
        rows.append({"row": e["row"], "member": e["member"].split(".")[-1],
                     "path": h["path"], "offset": h["offset"],
                     "offset_hex": f"0x{h['offset']:X}", "type": typ,
                     "old": cur if cur is not None else old, "new": new,
                     "conf": e.get("conf", "decoded"), "bmak": e.get("bmak", ""),
                     **({"behaviour": e["behaviour"], "take": e["take"]}
                        if "behaviour" in e else {})})
    return rows


def resolve_autoaim(aa: dict, report: list[dict]) -> dict:
    src = shared_source(aa["src"])
    xml = export_xml(src["blob"], "aa_" + aa["private"].split("/")[-1].replace(".wtunec", ""))
    leaves = leaf_paths(xml)
    rows, already = [], []
    for e in aa["edits"]:
        hits = locate(leaves, e["member"], None, require=None)
        for h in hits:
            cur = num(h["text"]) if h["type"] != "uint32" else int(h["text"])
            want = e["new"]
            row = {"row": "T-WP4" if "emp" in aa["private"] else "B-15",
                   "member": e["member"], "path": h["path"], "offset": h["offset"],
                   "offset_hex": f"0x{h['offset']:X}", "type": e["type"],
                   "old": cur, "new": want, "conf": e.get("conf", "derived"),
                   "bmak": e["bmak"], "state": h["path"].split(".")[0]}
            (already if (isinstance(cur, (int, float)) and same(cur, want)) else rows).append(row)
    return {"source": {k: src[k] for k in ("kind", "id", "game_path", "mount", "sha1", "bytes")},
            "source_blob": src["blob"], "private": aa["private"], "purpose": aa["purpose"],
            "edits": rows, "already": already}


def patch(blob: bytes, rows: list[dict], label: str) -> bytes:
    b = bytearray(blob)
    for r in rows:
        pack_at(b, r["offset"], r["type"], r["new"])
    if len(b) != len(blob):
        raise SystemExit(f"{label}: patch changed the size")
    return bytes(b)


def plan() -> dict:
    t7 = t7_rows()
    files = {}
    order = ["cannon", "vulcan", "missile", "emp", "riot"]
    by_key = {t["key"]: t for t in TUNES}
    for key in order:
        spec = by_key[key]
        if spec["src"][0] == "chain":
            base = files[spec["src"][1]]["patched"]
            src = {"kind": "build", "id": spec["src"][1] + " (this build)",
                   "game_path": by_key[spec["src"][1]]["private"], "mount": "private",
                   "sha1": sha1(base), "bytes": len(base), "blob": base, "dir_file_bytes": None}
        else:
            src = resolve_source(spec["src"])
        xml = export_xml(src["blob"], spec["key"])
        rows = resolve_edits(spec, src, xml, t7, [])
        patched = patch(src["blob"], rows, spec["private"])
        entry = {"key": key, "row": spec["row"], "component": spec["component"],
                 "purpose": spec["purpose"], "private": spec["private"],
                 "tune": spec["private"].replace(".wtunec", ".wtune"),
                 "source": {k: src[k] for k in ("kind", "id", "game_path", "mount", "sha1",
                                                "bytes", "dir_file_bytes")},
                 "edits": rows, "patched": patched, "readback": readback(patched, rows),
                 "autoaim": resolve_autoaim(spec["autoaim"], []) if spec["autoaim"] else None}
        if entry["autoaim"]:
            aa = entry["autoaim"]
            aa["patched"] = patch(aa["source_blob"], aa["edits"], aa["private"])
            aa["readback"] = readback(aa["patched"], aa["edits"])
            aa["bytes"] = len(aa["patched"])
            aa["sha256"] = sha256(aa["patched"])
        entry["bytes"] = len(patched)
        entry["sha256"] = sha256(patched)
        files[key] = entry
    return {"schema": SCHEMA, "card": CARD, "generator": E.rel(__file__),
            "base": {"build": E.rel(BASE_DIR), "epe": E.rel(BASE_EPE),
                     "epe_sha256": sha256(open(BASE_EPE, "rb").read()),
                     "bytes": os.path.getsize(BASE_EPE)},
            "inputs": {
                "t7": E.rel(T7) + " (T-11: 3 numeric edits)",
                "weapons": E.rel(WJSONL) + " (G2-10 shipped tunes, sha1 + sizes)",
                "shared": E.rel(WSHARED) + " (G2-10 shared AutoAim tunes)",
                "tracer": "tmp/freebuff/reports/fx12-16-tracer-and-trail.md (FX-16: offsets, "
                          "values, BmAK CanonTrail numbers)",
                "riot": "tmp/freebuff/reports/apply-riot-mode-rows.md §4 (B-15 members)",
                "t4": "tmp/freebuff/reports/apply-weapon-slot-rows.md §2 (T-WP4 guidance values)",
                "base_graph": E.rel(BASE_EPE) + " (B-05's four components)",
            },
            "weapons": [files[k] for k in order],
            "tracer_unchanged": TRACER_UNCHANGED,
            "limits": [
                {"id": "L-1", "kind": "declared (R5)",
                 "what": "the w618 pair names a missile tune on a `CBulletWeaponBase` component",
                 "why": "B-05 clones the APC's bullet weapon for all four; a missile tune on a "
                        "bullet-weapon carrier is a name-level match, behaviour UNKNOWN."},
                {"id": "L-2", "kind": "UNKNOWN",
                 "what": "each private copy keeps its shipped ADF instance name",
                 "why": "renaming needs a ConvertAdf re-encode that is not byte-identical."},
                {"id": "L-3", "kind": "UNKNOWN",
                 "what": "the loose `.epe` install path",
                 "why": "B-05 limit: whether JC3 honours a dropzone-loose `.epe` is UNKNOWN."},
                {"id": "L-4", "kind": "unbound",
                 "what": "the riot tune and its AutoAim are authored but not bound",
                 "why": "B-15 needs a second weapon entity; B-05 wrote none, and the third slot "
                        "index is blocked (mode-switch-carriers.md §7 U1)."},
                {"id": "L-5", "kind": "UNKNOWN",
                 "what": "the AutoAim angle unit",
                 "why": "0.15 is 54 deg as turns, 8.6 deg as radians; BmAK's 40 deg cone cannot "
                        "be written until the unit is settled (apply-weapon-slot-rows §10 U2)."},
            ],
            }


def readback(blob: bytes, rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        cur = unpack_at(blob, r["offset"], r["type"])
        out.append({"path": r["path"], "offset_hex": r["offset_hex"], "read": cur,
                    "expected": r["new"], "ok": same(cur, r["new"])})
    return out


# ------------------------------------------------------------------ the entity
def epe_plan(root, doc) -> list[dict]:
    """Point each of B-05's four components at its private tune/autoaim; return the rows."""
    comps = {}
    for o in E.objects(root):
        if E.vcls(o) == "CBulletWeaponBase":
            comps.setdefault(E.vname(o), []).append(o)
    rows = []
    for w in doc["weapons"]:
        if not w["component"]:
            continue
        hits = comps.get(w["component"], [])
        if len(hits) != 1:
            raise SystemExit(f"{w['component']}: {len(hits)} component object(s)")
        o = hits[0]
        pairs = [(TUNE_ID, w["tune"], "tuning_file")]
        if w["autoaim"]:
            pairs.append((AIMA_ID, w["autoaim"]["private"].replace(".wtunec", ".wtune"),
                          "autoaim_tuning_file"))
        for mid, new, name in pairs:
            old = E.get_value(o, "id:" + mid)
            E.set_value(o, "id:" + mid, new)
            rows.append({"component": w["component"], "row": w["row"], "member": "id:" + mid,
                         "name": name, "old": old, "new": new,
                         "evidence": w["purpose"]})
    return rows


def register(aaf: str, vfs_names: list[str]) -> int:
    p = os.path.join(aaf, "@files.xml")
    data = open(p, "rb").read()
    eol = b"\r\n" if data.count(b"\r\n") * 2 > data.count(b"\n") else b"\n"
    added = 0
    for vfs in vfs_names:
        if b'name="' + vfs.encode() + b'"' in data:
            continue
        line = (f'  <file name="{vfs}">{vfs.replace("/", "\\")}</file>'.encode() + eol)
        data = data.replace(b"</files>", line + b"</files>")
        added += 1
    open(p, "wb").write(data)
    return added


def index_paths() -> set[str]:
    return {json.loads(l)["path"] for l in open(INDEX, encoding="utf-8")}


def shipped_paths() -> set[str]:
    """Paths the shipped game names: the index, the APC graph, the signature diff."""
    out = {p for p in index_paths()
           if p.startswith(("editor/entities/jc_weapons/", "models/jc_weapons/",
                            "editor/entities/jc_environments/"))}
    for f in (APC, SIGDIFF):
        if os.path.exists(f):
            out |= set(re.findall(r"(?:editor/entities|models)/[^\"<>\s,]+",
                                  open(f, encoding="utf-8", errors="replace").read()))
    return out


def done_paths(root) -> dict:
    prefixes = ("editor/entities/jc_weapons/", "models/jc_weapons/",
                "editor/entities/jc_environments/")
    named: set[str] = set()
    for o in E.objects(root):
        for v in o.iter("value"):
            if v.get("type") == "string" and (v.text or "").startswith(prefixes):
                named.add(v.text)
    index = index_paths()
    shipped_set = shipped_paths()
    private, shipped, dangling = [], [], []
    aaf = os.path.join(OUT, "aaf")
    for p in sorted(named):
        wtunec = p[:-len(".wtune")] + ".wtunec" if p.endswith(".wtune") else p
        if os.path.exists(os.path.join(aaf, p)):
            private.append(p)
        elif wtunec != p and os.path.exists(os.path.join(aaf, wtunec)):
            private.append(p)
        elif p in index or wtunec in index or p in shipped_set or wtunec in shipped_set:
            shipped.append(p)
        else:
            dangling.append(p)
    return {"named": len(named), "private": private, "shipped": shipped, "dangling": dangling}


def build() -> dict:
    doc = plan()
    tmp = tempfile.mkdtemp(prefix="bm_wpn_")
    base_xml = os.path.join(tmp, "base.xml")
    E.export(BASE_EPE, base_xml)
    root = ET.parse(base_xml).getroot()
    census = jc3wiring.parse_epe(base_xml)
    doc["base"]["objects"] = len(census)
    doc["base"]["classes"] = len({o.cls for o in census if o.cls})
    doc["base"]["classless_root"] = sum(1 for o in census if not o.cls)
    doc["repointed"] = epe_plan(root, doc)
    built_xml = os.path.join(ROOT, "tmp", "b06", "built.xml")
    os.makedirs(os.path.dirname(built_xml), exist_ok=True)
    ET.ElementTree(root).write(built_xml, encoding="utf-8", xml_declaration=True)
    built = jc3wiring.parse_epe(built_xml)
    doc["built"] = {"epe": E.rel(OUT_EPE), "objects": len(built),
                    "classes": len({o.cls for o in built if o.cls}),
                    "classless_root": sum(1 for o in built if not o.cls),
                    "expected_xml": built_xml}
    carriers = {o.name: o.cls for o in built
                if o.cls in ("CBulletWeaponBase", "CMissileWeaponBase")}
    for w in doc["weapons"]:
        w["carrier_class"] = carriers.get(w["component"]) if w["component"] else None
    files = [w for w in doc["weapons"]]
    doc["counts"] = {
        "components": sum(1 for w in files if w["component"]),
        "private_tunes": sum(1 for w in files if w["private"]),
        "autoaim_tunes": sum(1 for w in files if w["autoaim"]),
        "private_files": sum(1 for w in files if w["private"])
                         + sum(1 for w in files if w["autoaim"]),
        "tune_edits": sum(len(w["edits"]) for w in files),
        "autoaim_edits": sum(len(w["autoaim"]["edits"]) for w in files if w["autoaim"]),
        "autoaim_already": sum(len(w["autoaim"]["already"]) for w in files if w["autoaim"]),
        "edits": sum(len(w["edits"]) for w in files)
                 + sum(len(w["autoaim"]["edits"]) for w in files if w["autoaim"]),
        "repointed_members": len(doc["repointed"]),
        "bound_weapons": sum(1 for w in files if w["component"]),
        "unbound": sum(1 for w in files if not w["component"]),
        "carrier_class_mismatch": sum(1 for w in files
                                      if w["component"] and w["carrier_class"]
                                      != "CMissileWeaponBase" and "missile" in w["tune"]),
    }
    doc["done1"] = done_paths(root)
    doc["_patched"] = {w["key"]: w.pop("patched") for w in doc["weapons"]}
    doc["_auto"] = {w["key"]: w["autoaim"].pop("patched")
                    for w in doc["weapons"] if w["autoaim"]}
    for w in doc["weapons"]:
        w.pop("source_blob", None)
        if w["autoaim"]:
            w["autoaim"].pop("source_blob", None)
    return doc


def installer_text(doc: dict) -> str:
    files = [ENT + "/" + EPE]
    for w in doc["weapons"]:
        files.append(w["private"])
        if w["autoaim"]:
            files.append(w["autoaim"]["private"])
    lines = [
        "<#",
        "    bm-RC4-weapons installer (B-06 private weapon tunes). Generated by",
        "    Tools/scripts/bm_weapons.py; never run by it. Close the game before -Action Install.",
        "    -GameDir defaults to the real install; point it at a copy to rehearse offline.",
        "#>",
        "[CmdletBinding()]",
        "param([ValidateSet('Install','Verify','Rollback091','Status')]"
        "[string]$Action = 'Status', [string]$GameDir = 'D:\\Games\\Just Cause 3')",
        "$ErrorActionPreference = 'Stop'",
        "$B = '" + OUT + "'",
        "$D = Join-Path $GameDir 'dropzone'",
        "$files = @(",
    ]
    for i, f in enumerate(files):
        lines.append(("    " if i == 0 else "    ,") + "'" + f + "'")
    lines += [
        ")",
        "switch ($Action) {",
        "    'Install' {",
        "        foreach ($f in $files) {",
        "            $t = Join-Path $D $f",
        "            New-Item -ItemType Directory -Force -Path (Split-Path $t) | Out-Null",
        "            Copy-Item -LiteralPath (Join-Path $B ('aaf\\' + $f.Replace('/', '\\'))) "
        "-Destination $t -Force",
        "            Write-Host ('deployed ' + $f)",
        "        }",
        "    }",
        "    'Verify' {",
        "        foreach ($f in $files) {",
        "            $t = Join-Path $D $f",
        "            if (-not (Test-Path -LiteralPath $t)) { throw ('missing ' + $t) }",
        "            Write-Host ('verified ' + $t + ' ' + (Get-FileHash -LiteralPath $t).Hash)",
        "        }",
        "    }",
        "    'Rollback091' {",
        "        foreach ($f in $files) {",
        "            Remove-Item -LiteralPath (Join-Path $D $f) -Force -ErrorAction SilentlyContinue",
        "        }",
        "        if ($GameDir -eq 'D:\\Games\\Just Cause 3') {",
        "            & (Join-Path 'E:\\Modding\\JC3-Batmobile\\Builds\\test-091' 'install.ps1') "
        "-Action Install",
        "        } else { Write-Host ('rehearsal on ' + $GameDir + ': test-091 re-install skipped') }",
        "    }",
        "    'Status' { foreach ($f in $files) { Write-Host ('file ' + (Join-Path $D $f)) } }",
        "}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not a.write:
        sys.exit(check())
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(BASE_DIR, "aaf"), os.path.join(OUT, "aaf"))
    doc = build()
    for w in doc["weapons"]:
        p = os.path.join(OUT, "aaf", w["private"].replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(doc["_patched"].pop(w["key"]))
        if w["autoaim"]:
            aa = w["autoaim"]
            ap_ = os.path.join(OUT, "aaf", aa["private"].replace("/", os.sep))
            os.makedirs(os.path.dirname(ap_), exist_ok=True)
            open(ap_, "wb").write(doc["_auto"].pop(w["key"]))
    os.makedirs(os.path.dirname(OUT_EPE), exist_ok=True)
    E.imp(doc["built"]["expected_xml"], OUT_EPE)
    doc["done1"] = done_paths(ET.parse(doc["built"]["expected_xml"]).getroot())
    doc.pop("_patched", None)
    doc.pop("_auto", None)
    paths = [w["private"] for w in doc["weapons"]]
    paths += [w["autoaim"]["private"] for w in doc["weapons"] if w["autoaim"]]
    added = register(os.path.join(OUT, "aaf"), paths)
    listed = open(os.path.join(OUT, "aaf", "@files.xml"), encoding="utf-8-sig").read()
    doc["counts"]["registered"] = sum(1 for p in paths if f'name="{p}"' in listed)
    doc["counts"]["registered_this_run"] = added
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
    with open(os.path.join(OUT, "install.ps1"), "w", encoding="utf-8", newline="\n") as f:
        f.write(installer_text(doc))
    receipt = {"schema": SCHEMA, "card": CARD, "tag": TAG, "base": E.rel(BASE_DIR),
               "base_sha256": doc["base"]["epe_sha256"], "base_bytes": doc["base"]["bytes"],
               "epe": {"file": E.rel(OUT_EPE), "sha256": sha256(open(OUT_EPE, "rb").read()),
                       "bytes": os.path.getsize(OUT_EPE)},
               "counts": doc["counts"], "weapons": doc["weapons"],
               "repointed": doc["repointed"], "tracer_unchanged": doc["tracer_unchanged"],
               "limits": doc["limits"], "done1": doc["done1"], "installed": False}
    with open(os.path.join(OUT, "receipt.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    c = doc["counts"]
    print(f"wrote {E.rel(OUT_EPE)}: {c['components']} component(s), {c['private_files']} private "
          f"file(s), {c['edits']} value writes")
    for w in doc["weapons"]:
        rb = ", ".join(f"{r['path'].split('.')[-1]}={r['read']:g}" for r in w["readback"])
        print(f"  {w['private']}  ({w['bytes']} B)  {rb or 'copy only'}")
        if w["autoaim"]:
            aa = w["autoaim"]
            print(f"    {aa['private']}  ({aa['bytes']} B)  {len(aa['edits'])} write(s), "
                  f"{len(aa['already'])} already at target")
    d = doc["done1"]
    print(f"  Done 1: {d['named']} weapon path(s) named - {len(d['private'])} private in the build, "
          f"{len(d['shipped'])} shipped, {len(d['dangling'])} dangling")
    print(f"  classes: base {doc['base']['classes']}, built {doc['built']['classes']}")


def check() -> int:
    fails: list[str] = []
    doc = build()
    if not os.path.exists(OUT_EPE):
        print("FAIL: " + E.rel(OUT_EPE) + " missing (run --write)")
        return 1
    tmp = tempfile.mkdtemp(prefix="bm_wpn_check_")
    x1 = os.path.join(tmp, "a.xml")
    E.export(OUT_EPE, x1)
    y = os.path.join(tmp, "b.epe")
    E.imp(x1, y)
    if sha256(open(OUT_EPE, "rb").read()) != sha256(open(y, "rb").read()):
        fails.append("ConvertProperty --e/--i does not reproduce the built .epe")
    on_disk = read_json(SPEC) if os.path.exists(SPEC) else None
    if on_disk is None:
        fails.append("Working/Weapons/manifest.json missing")
    else:
        rec_base = on_disk.get("base", {}).get("epe_sha256")
        if rec_base and rec_base != doc["base"]["epe_sha256"]:
            fails.append("the base build changed since this card was built - rebuild with --write")
        if on_disk.get("weapons") != doc["weapons"] or \
                on_disk.get("repointed") != doc["repointed"] or \
                on_disk.get("limits") != doc["limits"]:
            fails.append("Working/Weapons/manifest.json does not match the re-derived plan")
    if os.path.exists(os.path.join(OUT, "receipt.json")):
        rec = read_json(os.path.join(OUT, "receipt.json"))
        if rec.get("epe", {}).get("sha256") != sha256(open(OUT_EPE, "rb").read()):
            fails.append("the receipt's .epe sha256 does not match the built file")
        if rec.get("base_sha256") and rec["base_sha256"] != doc["base"]["epe_sha256"]:
            fails.append("the receipt's base sha256 does not match the base on disk")
    for w in doc["weapons"]:
        path = os.path.join(OUT, "aaf", w["private"].replace("/", os.sep))
        if not os.path.exists(path):
            fails.append(f"the private tune {w['private']} is missing from the build")
            continue
        blob = open(path, "rb").read()
        if len(blob) != w["source"]["bytes"]:
            fails.append(f"{w['private']}: {len(blob)} B, the source is {w['source']['bytes']} B "
                         f"(a patch must not resize the file)")
        if sha256(blob) != w["sha256"]:
            fails.append(f"{w['private']}: the built copy does not have the manifest's sha256")
        for r in readback(blob, w["edits"]):
            if not r["ok"]:
                fails.append(f"{w['private']}: {r['path']} reads {r['read']}, expects {r['expected']}")
        if w["autoaim"]:
            aa = w["autoaim"]
            ap_ = os.path.join(OUT, "aaf", aa["private"].replace("/", os.sep))
            if not os.path.exists(ap_):
                fails.append(f"the private autoaim {aa['private']} is missing from the build")
                continue
            ab = open(ap_, "rb").read()
            if len(ab) != aa["source"]["bytes"]:
                fails.append(f"{aa['private']}: size {len(ab)} != {aa['source']['bytes']}")
            if sha256(ab) != aa["sha256"]:
                fails.append(f"{aa['private']}: sha256 does not match the manifest")
            for r in readback(ab, aa["edits"]):
                if not r["ok"]:
                    fails.append(f"{aa['private']}: {r['path']} reads {r['read']}, "
                                 f"expects {r['expected']}")
    listed = open(os.path.join(OUT, "aaf", "@files.xml"), encoding="utf-8-sig").read()
    privates = [w["private"] for w in doc["weapons"]] + \
               [w["autoaim"]["private"] for w in doc["weapons"] if w["autoaim"]]
    registered = sum(1 for p in privates if f'name="{p}"' in listed)
    if registered != len(privates):
        fails.append(f"only {registered} of {len(privates)} private file(s) are registered in "
                     f"aaf/@files.xml")
    d = done_paths(ET.parse(x1).getroot())
    if d["dangling"]:
        fails.append(f"Done 1: {len(d['dangling'])} dangling weapon path(s): {d['dangling'][:3]}")
    for w in doc["weapons"]:
        if w["component"] and w["tune"] not in d["private"]:
            fails.append(f"Done 1: the private tune {w['tune']} is not among the .epe's paths")
    if fails:
        for f in fails:
            print("FAIL: " + f)
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    c = doc["counts"]
    print(f"PASS: {E.rel(OUT_EPE)} {doc['base']['objects']} -> {doc['built']['objects']} objects, "
          f"{c['repointed_members']} member(s) repointed")
    print(f"  files: {c['private_tunes']} private tune(s) + {c['autoaim_tunes']} AutoAim; "
          f"{c['edits']} value writes ({c['tune_edits']} tune + {c['autoaim_edits']} aim, "
          f"{c['autoaim_already']} aim leaves already at target)")
    print(f"  Done 1: {d['named']} weapon path(s) named - {len(d['private'])} private, "
          f"{len(d['shipped'])} shipped, {len(d['dangling'])} dangling")
    return 0


if __name__ == "__main__":
    main()
