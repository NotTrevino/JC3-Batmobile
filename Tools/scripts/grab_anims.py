"""grab_anims.py - the Batmobile animation record: names, sets, bones, notifies, poses.

`MECHANICS.md` prints the export table name for an animation, and in this cook every
`AnimSequence` export is literally named `AnimSequence`.  The human name is the
`SequenceName` NameProperty in the tag stream (offset 84), which `objects.jsonl` does not
promote to its `name` field.  This tool performs that join, then records:

  * every sequence's owning AnimSet, name, SequenceLength, NumFrames and RateScale;
  * the AnimSet's `TrackBoneNames` and the umodel `RemoveTracks` config, so the active
    bone list is the tracks that actually exist in the PSA (a removed component is null,
    not a zero that looks like data);
  * every `Notifies` item: time, notify class, `AnimNotify_Sound` -> AkEvent and
    `RAnimNotify_Script` -> script name, plus the payload of the other notify classes;
  * a mechanism class per sequence, assigned from the bones that move, with the evidence
    recorded.  A sequence that moves three or more weapon/body mechanisms, or a
    transformation bone/shell, is `transformation`; wheel-only motion is `wheels/strafe`,
    and camera/batwing/chair/door/winch motion is `other` with its bones listed.

The key-frame tables are written outside the repository, as the card requires:

  E:\\Modding\\_shared\\gamedata\\BmAKgrab\\anims\\keys\\<package>__<AnimSet>.json

Each track stores position (metres, PSK/UE3 frame) and rotation (quaternion and Euler XYZ
in radians), or null where the PSA config says that component was not exported.  No value
is hand-typed: positions and rotations come from the umodel PSA, and every other field is
read from the `.upk` or the PSA header.

Outputs:
  Research/BatmobileGrab/ANIMATIONS.json   the machine source
  Research/BatmobileGrab/ANIMATIONS.md     the readable record
  E:\\Modding\\_shared\\gamedata\\BmAKgrab\\anims\\keys\\*.json  per-bone keyframes (outside the repo)

Usage:
  python Tools/scripts/grab_anims.py --write
  python Tools/scripts/grab_anims.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import struct
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upk_read import Package, best_walk  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OBJECTS = GRAB / "objects.jsonl"
OUT_JSON = GRAB / "ANIMATIONS.json"
OUT_MD = GRAB / "ANIMATIONS.md"

GAME = Path(os.environ.get("BMAK_GAME_DIR",
                           r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"))
ANIM_ROOT = Path(os.environ.get("BMAK_ANIM_DIR", r"E:\Modding\_shared\gamedata\BmAKgrab\anims"))
KEY_DIR = ANIM_ROOT / "keys"

PACKAGES = (
    ("Playable_Batmobile_SF", "Batmobile"),
    ("Playable_BatmobileMK2_SF", "MK2"),
    ("Playable_BatmobileFunhouse_SF", "Funhouse"),
    ("Playable_BatmobileJoker_SF", "Joker"),
)
LABEL = dict(PACKAGES)
PACKAGE_ORDER = {p: i for i, (p, _) in enumerate(PACKAGES)}

MECHANISMS = (
    "canopy", "turret", "cannon", "Vulcan", "missile bays", "transformation",
    "wheels/strafe", "suspension", "fins/air-brakes", "driver/Batman", "other",
)
MECH_ORDER = {m: i for i, m in enumerate(MECHANISMS)}
TRANSFORM_BONES = ("Weapons_Trans", "Shell", "Weapons_Root", "Weapons_Sides",
                   "Weapons_Top_Sides")
# A transformation claim is stronger than a weapon's own translation bone: `Weapons_Trans`
# and `Weapons_Top_Sides_Root` also move during Cannon_Fire.  Only a shell is unambiguous;
# everything else reaches `transformation` through three or more strong mechanisms.
TRANSFORM_SIGNATURE = ("Shell",)

# The key-frame tables are useful only if they are smaller than the PSAs; 6 decimals is
# below the precision of the cooked floats (the PSA stores IEEE singles).
ROUND = 6
MOVE_CM = 0.5          # a track with less motion than this is not cited as evidence
MOVE_DEG = 0.5


# ---------------------------------------------------------------------------------------------
# small helpers


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fnum(v, places=6):
    if v is None:
        return None
    return round(float(v), places)


def esc(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        out.append("| " + " | ".join(esc(c) for c in row) + " |")
    return out


def name_from_tags(pkg, index: int) -> tuple[str | None, int | None, list[dict]]:
    """Return (SequenceName, FName number, tags) for an AnimSequence export."""
    data = pkg.data(index)
    tags, _end, _why = best_walk(pkg, data)
    name_tag = next((t for t in tags
                     if t.get("type") == "NameProperty" and t.get("offset") == 84), None)
    if name_tag is None:
        name_tag = next((t for t in tags if t.get("type") == "NameProperty"), None)
    if name_tag is None:
        return None, None, tags
    return name_tag.get("value"), name_tag.get("number"), tags


def scalar(tags: list[dict], offset: int, type_name: str):
    tag = next((t for t in tags if t.get("offset") == offset
                and t.get("type") == type_name), None)
    return None if tag is None else tag.get("value")


def bone_category(bone: str) -> str:
    """Mechanism groups over the actual track names.  Deliberately name-independent."""
    if any(s in bone for s in ("Bip01", "Gundummy", "FcFX_", "flower_root",
                               "ExposeTransform")):
        return "driver/Batman"
    if "Aero_Flap" in bone or "Jet_Fins" in bone:
        return "fins/air-brakes"
    if "Missiles_" in bone:
        return "missile bays"
    if "Machine_Gun" in bone:
        return "Vulcan"
    if "Heavy_Cannon" in bone or "Heavy_Shells" in bone or "Riot_Sup" in bone:
        return "cannon"
    if "Turret_" in bone:
        return "turret"
    if "CockPit" in bone or "Cockpit" in bone or "Nose_Mesh" in bone:
        return "canopy"
    if "SUSP" in bone or "Damper" in bone or "Wheel_Parent" in bone or \
            "WHEEL_ARCH_Arm" in bone:
        return "suspension"
    if bone.startswith("Wheel_") or "Wheel_" in bone:
        return "wheels/strafe"
    if any(s in bone for s in TRANSFORM_BONES):
        return "transformation"
    return "other"


def is_transform_signature(bone: str) -> bool:
    return any(s in bone for s in TRANSFORM_SIGNATURE)


# ---------------------------------------------------------------------------------------------
# PSA reader


def parse_psa(path: Path) -> dict | None:
    """Read a UEViewer .psa (PSA_VERSION 20100422).  None when the file is absent."""
    if not path.exists():
        return None
    data = path.read_bytes()
    bones: list[str] = []
    infos: list[dict] = []
    keys = b""
    o = 0
    while o < len(data):
        if o + 32 > len(data):
            raise ValueError("%s: truncated chunk header at %#x" % (path, o))
        cid = data[o:o + 20].split(b"\0")[0].decode("latin-1")
        typ, size, count = struct.unpack_from("<Iii", data, o + 20)
        o += 32
        if cid == "ANIMHEAD":
            continue
        if cid == "BONENAMES":
            if size < 64 or o + size * count > len(data):
                raise ValueError("%s: bad BONENAMES" % path)
            for i in range(count):
                bones.append(data[o + i * size:o + i * size + 64].split(b"\0")[0]
                             .decode("latin-1"))
            o += size * count
        elif cid == "ANIMINFO":
            if size < 168 or o + size * count > len(data):
                raise ValueError("%s: bad ANIMINFO" % path)
            for i in range(count):
                d = data[o + i * size:o + (i + 1) * size]
                name = d[:64].split(b"\0")[0].decode("latin-1")
                total, _root, _style, _quot = struct.unpack_from("<iiii", d, 128)
                _red, track, rate = struct.unpack_from("<fff", d, 144)
                _start, first, raw = struct.unpack_from("<iii", d, 156)
                infos.append({
                    "name": name, "total_bones": total,
                    "track_time": fnum(track), "rate": fnum(rate),
                    "first_raw_frame": first, "num_raw_frames": raw,
                })
            o += size * count
        elif cid == "ANIMKEYS":
            if size != 32 or o + size * count > len(data):
                raise ValueError("%s: bad ANIMKEYS" % path)
            keys = data[o:o + size * count]
            o += size * count
        elif cid == "SCALEKEYS":
            o += size * count
        else:
            raise ValueError("%s: unknown chunk %r at %#x" % (path, cid, o - 32))
    return {
        "path": path,
        "sha256": sha256_file(path),
        "bones": bones,
        "infos": infos,
        "keys": keys,
        "key_count": len(keys) // 32,
    }


def psa_match(sequences: list[dict], psa: dict | None) -> list[dict]:
    """Map package sequences to PSA ANIMINFO rows.

    Umodel sorts PSA ANIMINFO by name, truncates `Name[64]` to 63 characters and
    disambiguates two same-named sequences (`Disarm_Switch_Player_180`).  Match on
    exact name + frame count first, then prefix + frame count, then the remaining
    fallbacks.  Every match is recorded, never assumed.
    """
    if not psa:
        return []
    infos = psa["infos"]
    unused = set(range(len(infos)))
    matched = []
    for seq in sequences:
        name, frames = seq["name"], seq.get("num_frames")
        choose = None
        for kind, pred in (
            ("exact+frames", lambda i: infos[i]["name"] == name and
             infos[i]["num_raw_frames"] == frames),
            ("prefix+frames", lambda i: (infos[i]["name"].startswith(name) or
                                         name.startswith(infos[i]["name"])) and
             infos[i]["num_raw_frames"] == frames),
            ("frames", lambda i: infos[i]["num_raw_frames"] == frames),
            ("exact", lambda i: infos[i]["name"] == name),
            ("prefix", lambda i: infos[i]["name"].startswith(name) or
             name.startswith(infos[i]["name"])),
            ("length", lambda i: seq.get("sequence_length") is not None and
             infos[i]["track_time"] is not None and infos[i]["rate"] and
             abs(infos[i]["track_time"] / infos[i]["rate"] - seq["sequence_length"]) < 1e-4),
        ):
            cand = [i for i in sorted(unused) if pred(i)]
            if cand:
                choose = cand[0]
                break
        if choose is None and unused:
            choose = min(unused)
            kind = "remaining"
        elif choose is None:
            kind = "unmatched"
        if choose is not None:
            unused.remove(choose)
            info = infos[choose]
            seq["psa_index"] = choose
            seq["psa_name"] = info["name"]
            seq["psa_match"] = kind
            seq["psa_length"] = (fnum(info["track_time"] / info["rate"])
                                 if info["rate"] else None)
            seq["psa_track_frames"] = info["track_time"]
            seq["psa_rate"] = info["rate"]
            seq["psa_frames"] = info["num_raw_frames"]
            matched.append(seq)
        else:
            seq["psa_index"] = None
            seq["psa_name"] = None
            seq["psa_match"] = "unmatched"
            seq["psa_length"] = None
            seq["psa_track_frames"] = None
            seq["psa_rate"] = None
            seq["psa_frames"] = None
    # Umodel sorts ANIMINFO by name, but two names can truncate to the same 63 characters.
    # When the frame counts also agree, the only deterministic mapping left is the name
    # order; assign the sorted sequence names to the sorted PSA rows.
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for seq in matched:
        groups[(seq.get("psa_name"), seq.get("psa_frames"))].append(seq)
    for group in groups.values():
        if len(group) < 2:
            continue
        indices = sorted({s["psa_index"] for s in group})
        ordered = sorted(group, key=lambda s: s["name"])
        for seq, index in zip(ordered, indices):
            seq["psa_index"] = index
            seq["psa_name"] = infos[index]["name"]
            seq["psa_length"] = (fnum(infos[index]["track_time"] / infos[index]["rate"])
                                 if infos[index]["rate"] else None)
            seq["psa_track_frames"] = infos[index]["track_time"]
            seq["psa_rate"] = infos[index]["rate"]
            seq["psa_frames"] = infos[index]["num_raw_frames"]
    return matched


def psa_track(psa: dict, seq: dict, bone_index: int) -> dict:
    """Return the raw keys for one bone, plus which components the config kept."""
    info = psa["infos"][seq["psa_index"]]
    n = info["num_raw_frames"]
    nb = len(psa["bones"])
    base = info["first_raw_frame"] * nb
    mode = seq["_removed"].get(bone_index)
    has_trans = mode != "trans"
    has_rot = mode != "rot"
    positions, quats = [], []
    for fi in range(n):
        off = (base + fi * nb + bone_index) * 32
        if off + 32 > len(psa["keys"]):
            raise ValueError("%s: key overrun in %s" % (psa["path"], seq["name"]))
        x, y, z = struct.unpack_from("<3f", psa["keys"], off)
        qx, qy, qz, qw = struct.unpack_from("<4f", psa["keys"], off + 12)
        if has_trans:
            positions.append((x, y, z))
        if has_rot:
            quats.append((qx, qy, qz, qw))
    return {"positions": positions, "quats": quats,
            "has_trans": has_trans, "has_rot": has_rot, "frames": n}


def quat_angle_deg(a: tuple, b: tuple) -> float:
    dot = abs(sum(x * y for x, y in zip(a, b)))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    dot = min(1.0, max(-1.0, dot / (na * nb)))
    return math.degrees(2.0 * math.acos(dot))


def quat_euler_xyz(q: tuple) -> tuple[float, float, float]:
    """Euler XYZ in radians, R = Rz(yaw) * Ry(pitch) * Rx(roll)."""
    x, y, z, w = q
    sinr = 2.0 * (w * x + y * z)
    cosr = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr, cosr)
    sinp = 2.0 * (w * y - z * x)
    pitch = math.asin(min(1.0, max(-1.0, sinp)))
    siny = 2.0 * (w * z + x * y)
    cosy = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny, cosy)
    return roll, pitch, yaw


def motion_for(psa: dict, seq: dict) -> tuple[list[str], list[dict]]:
    """Active bone names and per-bone displacement/rotation, from the PSA keys."""
    active: list[str] = []
    moved: list[dict] = []
    for bi, bone in enumerate(psa["bones"]):
        mode = seq["_removed"].get(bi)
        if mode == "all":
            continue
        active.append(bone)
        raw = psa_track(psa, seq, bi)
        dpos = 0.0
        if raw["positions"]:
            p0 = raw["positions"][0]
            for p in raw["positions"][1:]:
                dpos = max(dpos, math.dist(p0, p))
        drot = 0.0
        if raw["quats"]:
            q0 = raw["quats"][0]
            for q in raw["quats"][1:]:
                drot = max(drot, quat_angle_deg(q0, q))
        if dpos >= MOVE_CM or drot >= MOVE_DEG:
            moved.append({"bone": bone, "category": bone_category(bone),
                          "dpos_cm": fnum(dpos, 4), "drot_deg": fnum(drot, 3)})
    moved.sort(key=lambda m: (-max(m["dpos_cm"], m["drot_deg"]), m["bone"]))
    return active, moved


# ---------------------------------------------------------------------------------------------
# notifies


def simple_tag(tag: dict) -> dict:
    out = {"type": tag.get("type"), "offset": tag.get("offset")}
    if tag.get("name") is not None:
        out["name"] = tag["name"]
    if "ref" in tag:
        out["ref"] = tag["ref"]
        if tag.get("ref_class"):
            out["ref_class"] = tag["ref_class"]
        out["index"] = tag.get("value")
    elif "props" in tag:
        out["props"] = [simple_tag(p) for p in tag["props"]]
    elif "items" in tag:
        out["count"] = tag.get("count")
        out["items"] = [[simple_tag(p) for p in item]
                        for item in tag["items"]]
    elif "value" in tag:
        out["value"] = tag["value"]
    if "bits" in tag:
        out["bits"] = tag["bits"]
    return out


def notify_record(pkg, package: str, item: list[dict], by_index: dict,
                  seq_length: float | None) -> dict:
    time_tag = next((t for t in item if t.get("type") == "FloatProperty"), None)
    ref_tag = next((t for t in item if t.get("ref")), None)
    time_s = fnum(time_tag["value"], 6) if time_tag else None
    rec = {
        "time_s": time_s,
        "time_fraction": fnum(time_s / seq_length, 6) if time_s is not None and seq_length else None,
        "class": ref_tag.get("ref_class") if ref_tag else None,
        "object_index": ref_tag.get("value") if ref_tag else None,
        "object": None,
        "sound": None,
        "script": None,
        "bone": None,
        "payload": [],
    }
    if not ref_tag:
        return rec
    idx = ref_tag["value"]
    obj = by_index.get((package, idx))
    if obj is None:
        return rec
    rec["object"] = pkg.object_path(idx)
    tags, _e, _w = best_walk(pkg, pkg.data(idx))
    rec["payload"] = [simple_tag(t) for t in tags]
    cls = obj.get("class")
    if cls == "AnimNotify_Sound":
        ak = next((t for t in tags if t.get("ref_class") == "AkEvent"), None)
        if ak:
            target = by_index.get((package, ak["value"]))
            rec["sound"] = {
                "event": ak.get("ref"),
                "index": ak.get("value"),
                "class": ak.get("ref_class"),
                "local": target is not None,
                "object": (target.get("class") if target else None),
            }
        rec["bone"] = next((t.get("value") for t in tags
                            if t.get("type") == "NameProperty"), None)
    elif cls == "RAnimNotify_Script":
        rec["script"] = next((t.get("value") for t in tags
                              if t.get("type") == "NameProperty"), None)
    else:
        rec["bone"] = next((t.get("value") for t in tags
                            if t.get("type") == "NameProperty"), None)
    return rec


# ---------------------------------------------------------------------------------------------
# collection


def load_objects() -> tuple[list[dict], dict]:
    rows = [json.loads(line) for line in OBJECTS.read_text(encoding="utf-8").splitlines()
            if line.strip()]
    return rows, {(r["package"], r["index"]): r for r in rows}


def read_set_bones(pkg, obj: dict) -> list[str]:
    data = pkg.data(obj["index"])
    tags, _end, _why = best_walk(pkg, data)
    tag = next((t for t in tags if t.get("name") == "TrackBoneNames"), None)
    if tag is None:
        return []
    out = []
    for i in range(tag.get("count") or 0):
        at = tag["at"] + 4 + i * 8
        idx = struct.unpack_from("<i", data, at)[0]
        out.append(pkg.names[idx] if 0 <= idx < len(pkg.names) else None)
    return out


def read_removed(path: Path) -> dict[str, dict[int, str]]:
    out: dict[str, dict[int, str]] = defaultdict(dict)
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^(.+?)\.(\d+)=(all|trans|rot)\s*$", line)
        if m:
            out[m.group(1)][int(m.group(2))] = m.group(3)
    return out


def active_from_config(bones: list[str], removed: dict[int, str]) -> list[str]:
    return [b for i, b in enumerate(bones) if removed.get(i) != "all"]


def classify(active: list[str], moved: list[dict]) -> tuple[str, list[dict]]:
    """Assign one primary mechanism from moved bones, with a static fallback."""
    active_cats = Counter(bone_category(b) for b in active)
    moved_cats: dict[str, list[dict]] = defaultdict(list)
    for m in moved:
        moved_cats[m["category"]].append(m)

    def strong(cat: str) -> list[dict]:
        items = [m for m in moved_cats.get(cat, [])
                 if m["dpos_cm"] >= 5.0 or m["drot_deg"] >= 5.0]
        if cat == "transformation":
            items = [m for m in items
                     if is_transform_signature(m["bone"])]
        return items

    strong_cats = {c for c in MECHANISMS if strong(c)}
    multi = {c for c in strong_cats
             if c in ("turret", "cannon", "Vulcan", "missile bays", "fins/air-brakes",
                      "transformation", "canopy", "driver/Batman")}
    if "driver/Batman" in strong_cats:
        primary = "driver/Batman"
    elif "transformation" in strong_cats or len(multi) >= 3:
        primary = "transformation"
    elif strong_cats:
        # Pick the strongest mechanism, not a fixed priority: a drift can move the cockpit
        # mesh as well as the wheels, and the wheel rotation is the larger motion.
        def score(m: str) -> tuple[float, int]:
            items = strong(m)
            val = max((max(x["dpos_cm"], x["drot_deg"]) for x in items), default=0.0)
            return (val, -MECH_ORDER[m])
        candidates = [m for m in strong_cats if m != "other"] or ["other"]
        primary = max(candidates, key=score)
    elif not moved:
        # A held pose with no movement: only claim a mechanism when the active tracks
        # point at one, and never call a multi-weapon static pose a transformation.
        if "CockPit_Mesh" in active:
            primary = "canopy"
        elif active_cats.get("driver/Batman"):
            primary = "driver/Batman"
        elif len([c for c in active_cats if c != "other"]) == 1:
            primary = next(c for c in active_cats if c != "other")
        else:
            primary = "other"
    else:
        primary = "other"
    return primary, []


def mechanism_rows(active: list[str], moved: list[dict], primary: str) -> list[dict]:
    active_cats = Counter(bone_category(b) for b in active)
    moved_cats: dict[str, list[dict]] = defaultdict(list)
    for m in moved:
        moved_cats[m["category"]].append(m)
    rows = []
    for mech in MECHANISMS:
        items = moved_cats.get(mech, [])
        if not active_cats.get(mech) and not items:
            continue
        rows.append({
            "mechanism": mech,
            "active_bones": active_cats.get(mech, 0),
            "moved_bones": len(items),
            "max_dpos_cm": max((m["dpos_cm"] for m in items), default=0.0),
            "max_drot_deg": max((m["drot_deg"] for m in items), default=0.0),
            "primary": mech == primary,
        })
    return rows


def evidence_for(active: list[str], moved: list[dict], primary: str) -> list[dict]:
    if moved:
        return moved[:5]
    return [{"bone": b, "category": bone_category(b), "dpos_cm": 0.0, "drot_deg": 0.0}
            for b in active if bone_category(b) == primary][:5]


def collect() -> dict:
    rows, by_index = load_objects()
    doc = {
        "schema": 1,
        "generator": "grab_anims.py",
        "verdict": "",
        "inputs": {
            "objects": "Research/BatmobileGrab/objects.jsonl",
            "objects_sha256": sha256_file(OBJECTS),
            "anim_root": ANIM_ROOT.as_posix(),
            "keyframes_dir": KEY_DIR.as_posix(),
            "packages": [{"package": p, "label": l} for p, l in PACKAGES],
            "selection": "every AnimSequence, AnimSet and AnimTree in the four vehicle packages",
            "name_rule": ("SequenceName NameProperty at tag offset 84; the export table name is "
                          "the class AnimSequence for all 253 sequences"),
        },
        "counts": {},
        "mechanism_counts": {},
        "notify_class_counts": {},
        "sets": [],
        "trees": [],
        "sequences": [],
        "duplicate_names": [],
        "psa_name_differences": [],
        "psa_missing": [],
    }

    for package, label in PACKAGES:
        path = GAME / (package + ".upk")
        pkg = Package(str(path))
        set_objs = {r["index"]: r for r in rows
                    if r["package"] == package and r["class"] == "AnimSet"}
        tree_objs = [r for r in rows
                     if r["package"] == package and r["class"] == "AnimTree"]
        seq_objs = {r["index"]: r for r in rows
                    if r["package"] == package and r["class"] == "AnimSequence"}

        # ---- sets and trees
        for idx, obj in set_objs.items():
            set_name = pkg.object_name(idx)
            bones = read_set_bones(pkg, obj)
            config = ANIM_ROOT / package / "AnimSet" / (set_name + ".config")
            psa_path = ANIM_ROOT / package / "AnimSet" / (set_name + ".psa")
            removed = read_removed(config)
            psa = parse_psa(psa_path)
            seqs = []
            for s in seq_objs.values():
                if pkg.object_name(pkg.exports[s["index"] - 1]["outer_index"]) != set_name:
                    continue
                seqs.append(s)
            seqs.sort(key=lambda r: r["index"])
            seq_records = []
            for s in seqs:
                seq = build_sequence(pkg, package, label, set_name, s, removed, by_index,
                                     bones)
                seq_records.append(seq)
            if psa:
                psa_match(seq_records, psa)
                for seq in seq_records:
                    if seq.get("psa_index") is not None:
                        active, moved = motion_for(psa, seq)
                    else:
                        active = active_from_config(bones, seq["_removed"])
                        moved = []
                    seq["active_bones"] = active
                    seq["active_bone_count"] = len(active)
                    seq["moved_bones"] = moved[:12]
                    seq["moved_bone_count"] = len(moved)
                    seq["max_translation_cm"] = max((m["dpos_cm"] for m in moved), default=0.0)
                    seq["max_rotation_deg"] = max((m["drot_deg"] for m in moved), default=0.0)
                    seq["mechanism"], _ = classify(active, moved)
                    seq["mechanisms"] = mechanism_rows(active, moved, seq["mechanism"])
                    seq["evidence"] = evidence_for(active, moved, seq["mechanism"])
            else:
                for seq in seq_records:
                    active = active_from_config(bones, seq["_removed"])
                    seq["psa_index"] = None
                    seq["psa_name"] = None
                    seq["psa_match"] = "missing"
                    seq["psa_length"] = None
                    seq["psa_track_frames"] = None
                    seq["psa_rate"] = None
                    seq["psa_frames"] = None
                    seq["active_bones"] = active
                    seq["active_bone_count"] = len(active)
                    seq["moved_bones"] = []
                    seq["moved_bone_count"] = 0
                    seq["max_translation_cm"] = 0.0
                    seq["max_rotation_deg"] = 0.0
                    seq["mechanism"], _ = classify(active, [])
                    seq["mechanisms"] = mechanism_rows(active, [], seq["mechanism"])
                    seq["evidence"] = evidence_for(active, [], seq["mechanism"])
            key_name = "%s__%s.json" % (package, set_name)
            set_row = {
                "package": package,
                "package_label": label,
                "name": set_name,
                "export_index": idx,
                "outer": pkg.object_path(pkg.exports[idx - 1]["outer_index"]),
                "track_bones": bones,
                "track_bone_count": len(bones),
                "sequence_count": len(seq_records),
                "psa": psa_path.as_posix() if psa else None,
                "psa_sha256": psa["sha256"] if psa else None,
                "config": config.as_posix() if config.exists() else None,
                "config_sha256": sha256_file(config) if config.exists() else None,
                "psa_keys": psa["key_count"] if psa else 0,
                "keyframes": key_name if psa else None,
            }
            if not psa:
                doc["psa_missing"].append({"package": package, "set": set_name,
                                           "path": psa_path.as_posix()})
            doc["sets"].append(set_row)
            doc["sequences"].extend(seq_records)

        # ---- AnimTrees
        for obj in sorted(tree_objs, key=lambda r: r["index"]):
            tree_name = pkg.object_name(obj["index"])
            tags, _end, _why = best_walk(pkg, pkg.data(obj["index"]))
            children = []
            child_tag = next((t for t in tags if t.get("name") == "Children"), None)
            for item in (child_tag.get("items") if child_tag else []) or []:
                name_tag = next((t for t in item if t.get("type") == "NameProperty"), None)
                ref_tag = next((t for t in item if t.get("ref")), None)
                child = {"name": name_tag.get("value") if name_tag else None,
                         "node_index": ref_tag.get("value") if ref_tag else None,
                         "node_class": ref_tag.get("ref_class") if ref_tag else None,
                         "sequence": None}
                if ref_tag and by_index.get((package, ref_tag["value"])):
                    node = by_index[(package, ref_tag["value"])]
                    ntags, _e, _w = best_walk(pkg, pkg.data(node["index"]))
                    child["sequence"] = next((t.get("value") for t in ntags
                                              if t.get("type") == "NameProperty"
                                              and t.get("offset") == 280), None)
                children.append(child)
            controls = []
            ctl_tag = next((t for t in tags if t.get("name") == "SkelControlLists"), None)
            for item in (ctl_tag.get("items") if ctl_tag else []) or []:
                name_tag = next((t for t in item if t.get("type") == "NameProperty"), None)
                ref_tag = next((t for t in item if t.get("ref")), None)
                controls.append({"bone": name_tag.get("value") if name_tag else None,
                                 "control": ref_tag.get("ref_class") if ref_tag else None,
                                 "index": ref_tag.get("value") if ref_tag else None})
            doc["trees"].append({
                "package": package,
                "package_label": label,
                "name": tree_name,
                "export_index": obj["index"],
                "outer": pkg.object_path(pkg.exports[obj["index"] - 1]["outer_index"]),
                "children": children,
                "skel_controls": controls,
            })

    # ---- stable ordering and flat cross-package views
    doc["sets"].sort(key=lambda r: (PACKAGE_ORDER[r["package"]], r["export_index"]))
    doc["sequences"].sort(key=lambda r: (PACKAGE_ORDER[r["package"]], r["export_index"]))
    doc["trees"].sort(key=lambda r: (PACKAGE_ORDER[r["package"]], r["export_index"]))
    name_count = Counter(r["name"] for r in doc["sequences"])
    doc["duplicate_names"] = [
        {"name": name,
         "instances": [{"package": s["package"], "set": s["set"],
                        "export_index": s["export_index"]}
                       for s in doc["sequences"] if s["name"] == name]}
        for name, count in sorted(name_count.items()) if count > 1
    ]
    doc["psa_name_differences"] = [
        {"package": s["package"], "set": s["set"], "name": s["name"],
         "psa_name": s["psa_name"], "match": s["psa_match"]}
        for s in doc["sequences"] if s["psa_name"] and s["psa_name"] != s["name"]
    ]

    mechanism_counts = Counter(s["mechanism"] for s in doc["sequences"])
    notify_counts = Counter()
    for s in doc["sequences"]:
        notify_counts.update(n["class"] for n in s["notifies"])
    doc["mechanism_counts"] = {m: mechanism_counts.get(m, 0) for m in MECHANISMS
                               if mechanism_counts.get(m, 0)}
    doc["notify_class_counts"] = dict(sorted(notify_counts.items(),
                                             key=lambda kv: (-kv[1], kv[0])))
    named = sum(1 for s in doc["sequences"] if s["name"])
    with_bones = sum(1 for s in doc["sequences"] if s["active_bones"])
    with_mech = sum(1 for s in doc["sequences"] if s["mechanism"])
    psa_sets = sum(1 for s in doc["sets"] if s["psa"])
    psa_sequences = sum(1 for s in doc["sequences"] if s["psa_index"] is not None)
    psa_keys = sum(s.get("psa_keys", 0) for s in doc["sets"])
    length_mismatch = sum(1 for s in doc["sequences"]
                          if s["psa_length"] is not None and s["sequence_length"] is not None
                          and abs(s["psa_length"] - s["sequence_length"]) > 1e-4)
    frame_mismatch = sum(1 for s in doc["sequences"]
                         if s["psa_frames"] is not None and s["psa_frames"] != s["num_frames"])
    doc["counts"] = {
        "packages": len(PACKAGES),
        "sets": len(doc["sets"]),
        "trees": len(doc["trees"]),
        "sequences": len(doc["sequences"]),
        "named": named,
        "with_bone_lists": with_bones,
        "with_mechanism": with_mech,
        "psa_sets": psa_sets,
        "psa_sequences": psa_sequences,
        "psa_keys": psa_keys,
        "psa_missing": len(doc["psa_missing"]),
        "active_bone_tracks": sum(s["active_bone_count"] for s in doc["sequences"]),
        "moved_bones": sum(s["moved_bone_count"] for s in doc["sequences"]),
        "sequences_with_notifies": sum(1 for s in doc["sequences"] if s["notifies"]),
        "notify_instances": sum(len(s["notifies"]) for s in doc["sequences"]),
        "notify_classes": len(doc["notify_class_counts"]),
        "sound_notifies": doc["notify_class_counts"].get("AnimNotify_Sound", 0),
        "script_notifies": doc["notify_class_counts"].get("RAnimNotify_Script", 0),
        "duplicate_names": len(doc["duplicate_names"]),
        "psa_name_differences": len(doc["psa_name_differences"]),
        "length_mismatches": length_mismatch,
        "frame_mismatches": frame_mismatch,
        "export_name_is_class": sum(1 for s in doc["sequences"] if s["export_name"] == "AnimSequence"),
    }
    c = doc["counts"]
    doc["verdict"] = (
        "%d/%d sequences named from SequenceName; %d sets + %d AnimTrees; %d PSA exports "
        "(%d sequences, %d keys); %d with notifies (%d items); %d/%d have bone lists and "
        "mechanism classes; %d length and %d frame mismatches"
        % (c["named"], c["sequences"], c["sets"], c["trees"], c["psa_sets"],
           c["psa_sequences"], c["psa_keys"], c["sequences_with_notifies"],
           c["notify_instances"], c["with_bone_lists"], c["sequences"],
           c["length_mismatches"], c["frame_mismatches"]))
    return doc


def build_sequence(pkg, package: str, label: str, set_name: str, obj: dict,
                   removed_all: dict[str, dict[int, str]], by_index: dict,
                   set_bones: list[str]) -> dict:
    idx = obj["index"]
    name, name_number, tags = name_from_tags(pkg, idx)
    length = scalar(tags, 156, "FloatProperty")
    frames = scalar(tags, 160, "IntProperty")
    rate = scalar(tags, 168, "FloatProperty")
    notifies = []
    ntag = next((t for t in tags if t.get("name") == "Notifies"), None)
    for item in (ntag.get("items") if ntag else []) or []:
        notifies.append(notify_record(pkg, package, item, by_index, length))
    removed = dict(removed_all.get(name or "", {}))
    return {
        "package": package,
        "package_label": label,
        "set": set_name,
        "export_index": idx,
        "export_name": pkg.object_name(idx),
        "outer": pkg.object_path(pkg.exports[idx - 1]["outer_index"]),
        "name": name,
        "name_number": name_number,
        "sequence_length": fnum(length),
        "num_frames": frames,
        "rate_scale": fnum(rate),
        "_removed": removed,
        "removed_tracks": {set_bones[i]: mode for i, mode in sorted(removed.items())
                           if 0 <= i < len(set_bones)},
        "notifies": notifies,
        "notify_count": len(notifies),
        "psa_index": None,
        "psa_name": None,
        "psa_match": None,
        "psa_length": None,
        "psa_track_frames": None,
        "psa_rate": None,
        "psa_frames": None,
        "active_bones": [],
        "active_bone_count": 0,
        "moved_bones": [],
        "moved_bone_count": 0,
        "max_translation_cm": 0.0,
        "max_rotation_deg": 0.0,
        "mechanism": None,
        "mechanisms": [],
        "evidence": [],
    }


# ---------------------------------------------------------------------------------------------
# key-frame writer


def track_tables(psa: dict, seq: dict) -> list[dict]:
    tracks = []
    for bi, bone in enumerate(psa["bones"]):
        mode = seq["_removed"].get(bi)
        if mode == "all":
            continue
        raw = psa_track(psa, seq, bi)
        positions = [[fnum(x / 100.0, ROUND) for x in p] for p in raw["positions"]] \
            if raw["has_trans"] else None
        quats = [[fnum(x, ROUND) for x in q] for q in raw["quats"]] \
            if raw["has_rot"] else None
        eulers = None
        if quats is not None:
            eulers = [[fnum(v, ROUND) for v in quat_euler_xyz(q)] for q in quats]
        tracks.append({
            "bone": bone,
            "removed": mode,
            "position_m": positions,
            "rotation_quat": quats,
            "rotation_euler_xyz_rad": eulers,
        })
    return tracks


def write_keyframes(doc: dict) -> tuple[int, int]:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    count = 0
    for set_row in doc["sets"]:
        if not set_row["psa"]:
            continue
        psa = parse_psa(Path(set_row["psa"]))
        if not psa:
            continue
        seqs = [s for s in doc["sequences"]
                if s["package"] == set_row["package"] and s["set"] == set_row["name"]]
        key_doc = {
            "schema": 1,
            "generator": "grab_anims.py",
            "package": set_row["package"],
            "set": set_row["name"],
            "psa": set_row["psa"],
            "psa_sha256": set_row["psa_sha256"],
            "config": set_row["config"],
            "config_sha256": set_row["config_sha256"],
            "frame": ("PSK/UE3: position metres, rotation quaternion (x,y,z,w), "
                      "Euler XYZ radians; null = the RemoveTracks config says that "
                      "component was not exported"),
            "bones": psa["bones"],
            "sequences": [],
        }
        for seq in seqs:
            if seq["psa_index"] is None:
                continue
            info = psa["infos"][seq["psa_index"]]
            rate = info["rate"] or (info["num_raw_frames"] / info["track_time"]
                                    if info["track_time"] else 0.0)
            key_doc["sequences"].append({
                "name": seq["name"],
                "psa_name": seq["psa_name"],
                "psa_index": seq["psa_index"],
                "export_index": seq["export_index"],
                "sequence_length": seq["sequence_length"],
                "num_frames": seq["num_frames"],
                "rate_scale": seq["rate_scale"],
                "psa_track_frames": info["track_time"],
                "psa_rate": info["rate"],
                "frame_times_s": [fnum(i / rate, ROUND) for i in range(info["num_raw_frames"])]
                if rate else [],
                "removed_tracks": {psa["bones"][i]: mode
                                   for i, mode in sorted(seq["_removed"].items())
                                   if 0 <= i < len(psa["bones"])},
                "tracks": track_tables(psa, seq),
            })
        path = KEY_DIR / set_row["keyframes"]
        path.write_text(json.dumps(key_doc, separators=(",", ":"), ensure_ascii=False) + "\n",
                        encoding="utf-8")
        total += path.stat().st_size
        count += 1
        print("wrote %s (%d bytes)" % (path, path.stat().st_size))
    return count, total


# ---------------------------------------------------------------------------------------------
# markdown


def fmt_num(v, places=3):
    if v is None:
        return "-"
    return ("%%.%df" % places) % float(v)


def binding_text(item: dict) -> str:
    if item.get("sound"):
        s = item["sound"]
        return "`%s`%s" % (s.get("event"), "" if s.get("local") else " (external)")
    if item.get("script"):
        return "`%s`" % item["script"]
    parts = []
    for p in item.get("payload", []):
        if p.get("name") and p.get("value") is not None:
            parts.append("%s=%s" % (p["name"], json.dumps(p["value"])))
        elif p.get("ref"):
            parts.append("%s=%s" % (p.get("name") or "ref", p["ref"]))
    return ", ".join(parts[:3]) or "-"


def render_md(doc: dict) -> str:
    c = doc["counts"]
    L: list[str] = []
    add = L.append
    add("# Batmobile animation record (G1-10)")
    add("")
    add("Every `AnimSequence` in the four Batmobile packages, joined to its owning `AnimSet`, "
        "the AnimSet's `TrackBoneNames`, the umodel `RemoveTracks` config, the PSA header and "
        "the sequence's `Notifies`. Generated by `Tools/scripts/grab_anims.py`; nothing here "
        "is hand-listed.")
    add("")
    add("**Verdict:** " + doc["verdict"] + ".")
    add("")
    add("## 1. Totals")
    add("")
    rows = [
        ["sequences", str(c["sequences"])],
        ["named from `SequenceName`", "%d/%d" % (c["named"], c["sequences"])],
        ["AnimSets", str(c["sets"])],
        ["AnimTrees", str(c["trees"])],
        ["PSA exports matched", "%d sets / %d sequences" % (c["psa_sets"], c["psa_sequences"])],
        ["PSA keys read", "{:,}".format(c["psa_keys"])],
        ["active bone tracks", str(c["active_bone_tracks"])],
        ["moved bone tracks (>= %.1f cm or %.1f deg)" % (MOVE_CM, MOVE_DEG), str(c["moved_bones"])],
        ["sequences with notifies", "%d (%d items)" % (c["sequences_with_notifies"], c["notify_instances"])],
        ["notify classes", str(c["notify_classes"])],
        ["`AnimNotify_Sound` / `RAnimNotify_Script`", "%d / %d" % (c["sound_notifies"], c["script_notifies"])],
        ["names repeated across packages", str(c["duplicate_names"])],
        ["PSA name differs from SequenceName", str(c["psa_name_differences"])],
        ["length mismatches", str(c["length_mismatches"])],
        ["frame-count mismatches", str(c["frame_mismatches"])],
        ["PSA exports missing", str(c["psa_missing"])],
    ]
    add("\n".join(md_table(["quantity", "value"], rows)))
    add("")
    add("The old `MECHANICS.md` animation table shows `AnimSequence` in the name column "
        "because that **is** the export table name for all %d objects. The human name is the "
        "`SequenceName` NameProperty at tag offset 84; this record uses it and keeps the "
        "export name in `ANIMATIONS.json` as evidence." % c["export_name_is_class"])
    add("")
    add("## 2. Sets and AnimTrees")
    add("")
    rows = []
    for s in doc["sets"]:
        rows.append([s["package_label"], s["package"], "AnimSet `%s`" % s["name"],
                     str(s["export_index"]), str(s["track_bone_count"]),
                     str(s["sequence_count"]),
                     "`%s`" % s["psa"] if s["psa"] else "missing",
                     "`%s`" % s["keyframes"] if s["keyframes"] else "-"])
    for t in doc["trees"]:
        rows.append([t["package_label"], t["package"], "AnimTree `%s`" % t["name"],
                     str(t["export_index"]), "-", "-",
                     "children: " + (", ".join(str(x["name"]) for x in t["children"]) or "-"),
                     "skel controls: %d" % len(t["skel_controls"])])
    add("\n".join(md_table(["label", "package", "object", "export", "track bones",
                            "sequences", "PSA / node", "keyframes / controls"], rows)))
    add("")
    add("## 3. Mechanism classes")
    add("")
    add("A sequence is assigned one **primary** class from the bones that actually move "
        "(>= %.1f cm or %.1f deg from frame 0):" % (MOVE_CM, MOVE_DEG))
    add("")
    add("* `driver/Batman` - any `Bip01*`, `Gundummy*`, `FcFX_*`, `flower_root` or "
        "`ExposeTransform*` track.")
    add("* `canopy` - `CockPit_Mesh` / `Batmobile_Nose_Mesh`.")
    add("* `fins/air-brakes` - `Aero_Flap*` / `Jet_Fins`.")
    add("* `missile bays` - `Weapons_Missiles_*`.")
    add("* `cannon` - `Heavy_Cannon*`, `Heavy_Shells`, `Riot_Sup*`.")
    add("* `Vulcan` - `Machine_Gun*`.")
    add("* `turret` - `Weapons_Turret_*`.")
    add("* `wheels/strafe` - `Wheel_*` other than the suspension parents.")
    add("* `suspension` - `SUSP*`, `Damper*`, `Wheel_Parent*`, wheel-arch arms.")
    add("* `transformation` - `*Shell*`, or three or more strong weapon/body "
        "mechanisms moving together. `Weapons_Trans`, `Weapons_Root`, `Weapons_Sides*` "
        "and `Weapons_Top_Sides*` are grouped here in the per-sequence mechanism table, "
        "but they also move during fire and therefore do not classify a sequence alone.")
    add("* `other` - camera, batwing, chair, rear door, winch, jet, sonar, tracker or "
        "any motion with no listed mechanism; its bones are listed below.")
    add("")
    rows = []
    for m in MECHANISMS:
        if not doc["mechanism_counts"].get(m):
            continue
        seqs = [s for s in doc["sequences"] if s["mechanism"] == m]
        rows.append(["`%s`" % m, str(len(seqs)),
                     str(sum(s["active_bone_count"] for s in seqs)),
                     str(sum(s["moved_bone_count"] for s in seqs)),
                     ", ".join(list(dict.fromkeys(s["name"] for s in seqs))[:4])
                     + (" ..." if len(dict.fromkeys(s["name"] for s in seqs)) > 4 else "")])
    add("\n".join(md_table(["primary mechanism", "sequences", "active tracks",
                            "moved tracks", "examples"], rows)))
    add("")
    add("## 4. Every sequence")
    add("")
    rows = []
    for s in doc["sequences"]:
        rows.append([s["package_label"], "`%s`" % s["set"], "`%s`" % s["name"],
                     str(s["num_frames"]), fmt_num(s["sequence_length"], 3),
                     fmt_num(s["rate_scale"], 2), str(s["active_bone_count"]),
                     "`%s`" % s["mechanism"], str(s["notify_count"])])
    add("\n".join(md_table(["label", "AnimSet", "sequence", "frames", "length s",
                            "RateScale", "bones", "mechanism", "notifies"], rows)))
    add("")
    add("## 5. Bone lists")
    add("")
    add("Every sequence's **active** tracks in PSA bone order. A track removed as `trans` "
        "or `rot` is still listed here (one component remains); a track removed as `all` "
        "is not. `ANIMATIONS.json` has the same list plus the removed component per bone.")
    add("")
    current = None
    for s in doc["sequences"]:
        key = (s["package"], s["set"])
        if key != current:
            current = key
            add("")
            add("### %s / `%s`" % (s["package_label"], s["set"]))
            add("")
        add("- **%s** (%d tracks): %s" % (
            s["name"], s["active_bone_count"],
            ", ".join("`%s`" % b for b in s["active_bones"]) or "-"))
    add("")
    add("## 6. Mechanism evidence")
    add("")
    add("The strongest moved bones per sequence, with displacement from frame 0 in "
        "centimetres and rotation in degrees. A static sequence shows its active signature "
        "bones instead (zero motion).")
    add("")
    for m in MECHANISMS:
        seqs = [s for s in doc["sequences"] if s["mechanism"] == m]
        if not seqs:
            continue
        add("### `%s` (%d)" % (m, len(seqs)))
        add("")
        rows = []
        for s in seqs:
            ev = "; ".join("%s %s cm / %s deg" % (e["bone"], fmt_num(e["dpos_cm"], 2),
                                                  fmt_num(e["drot_deg"], 2))
                           for e in s["evidence"]) or "-"
            rows.append([s["package_label"], "`%s`" % s["set"], "`%s`" % s["name"], ev])
        add("\n".join(md_table(["label", "AnimSet", "sequence", "evidence"], rows)))
        add("")
    add("## 7. Notifies")
    add("")
    add("`time_s` is the float in the sequence's `Notifies` array (seconds; every value is "
        "within its sequence length). `AnimNotify_Sound` resolves its `AkEvent`; "
        "`RAnimNotify_Script` exposes the called script name; other classes keep their "
        "payload.")
    add("")
    rows = [[ "`%s`" % k, str(v)] for k, v in doc["notify_class_counts"].items()]
    add("\n".join(md_table(["notify class", "instances"], rows)))
    add("")
    rows = []
    for s in doc["sequences"]:
        for n in s["notifies"]:
            rows.append([s["package_label"], "`%s`" % s["set"], "`%s`" % s["name"],
                         fmt_num(n["time_s"], 6), fmt_num(n["time_fraction"], 3),
                         "`%s`" % n["class"] if n["class"] else "-",
                         "`%s`" % n["bone"] if n.get("bone") else "-",
                         binding_text(n)])
    add("\n".join(md_table(["label", "AnimSet", "sequence", "time s", "fraction",
                            "class", "bone", "target / payload"], rows)))
    add("")
    add("## 8. Names and joins")
    add("")
    add("* `objects.jsonl` records the **class** `AnimSequence` as the object's `name` for "
        "all %d sequences. The human name is the offset-84 `NameProperty` (`SequenceName`)."
        % c["export_name_is_class"])
    add("* `SequenceName` is repeated in the four packages (the same 37 sequence names exist "
        "in the base / MK2 / Funhouse / Joker car sets) and some names repeat inside the "
        "Joker Camera/Phase2 sets; `ANIMATIONS.json` keeps every instance. %d names occur "
        "more than once." % c["duplicate_names"])
    if doc["duplicate_names"]:
        add("")
        rows = [["`%s`" % d["name"], str(len(d["instances"])),
                 ", ".join("%s/%s" % (i["package"], i["set"]) for i in d["instances"])]
                for d in doc["duplicate_names"]]
        add("\n".join(md_table(["name", "instances", "where"], rows)))
    add("")
    add("PSA `ANIMINFO` is sorted by name and truncates `Name[64]` to 63 characters. "
        "`grab_anims.py` matches by name + frame count, then prefix + frame count, and "
        "records the match kind. The one duplicate inside a set is `Camera`'s "
        "`Disarm_Switch_Player`: two package sequences share the name, PSA calls the "
        "301-frame one `Disarm_Switch_Player_180` and the 284-frame one "
        "`Disarm_Switch_Player`; frame count disambiguates them. The three long "
        "`Phase2_JK_FACE` names are prefix-matched after the 63-character cut, and the two "
        "2007-frame `...Finale` / `...Finale_Ver01` rows truncate to the same 63 characters; "
        "they are assigned in full-name order (`Finale` before `Finale_Ver01`).")
    if doc["psa_name_differences"]:
        add("")
        rows = [["%s / `%s`" % (d["package"], d["set"]), "`%s`" % d["name"],
                 "`%s`" % d["psa_name"], d["match"]]
                for d in doc["psa_name_differences"]]
        add("\n".join(md_table(["where", "SequenceName", "PSA name", "match"], rows)))
    add("")
    add("## 9. Key-frames (outside the repository)")
    add("")
    add("`--write` exports one PSA per AnimSet with umodel and writes a compact JSON per "
        "set to:")
    add("")
    add("```text")
    add(KEY_DIR.as_posix())
    add("```")
    add("")
    add("Format: `position_m` is metres in the PSK/UE3 frame (PSA centimetres / 100), "
        "`rotation_quat` is `(x, y, z, w)`, `rotation_euler_xyz_rad` is Euler XYZ in radians "
        "(`R = Rz * Ry * Rx`). `null` means the set's `RemoveTracks` config says that "
        "component was not exported - it is not a zero. `frame_times_s` is `i / PSA rate`; "
        "no resampling or root-motion interpretation is applied.")
    add("")
    rows = []
    for s in doc["sets"]:
        rows.append([s["package_label"], "`%s`" % s["name"], str(s["sequence_count"]),
                     "`%s`" % s["keyframes"] if s["keyframes"] else "missing",
                     "`%s`" % s["config"] if s["config"] else "-"])
    add("\n".join(md_table(["label", "AnimSet", "sequences", "keyframe file", "config"], rows)))
    add("")
    add("The keyframe files are deliberately outside `Research/` (they are large and "
        "derived); `--check` compares the two committed records and reports whether the "
        "13 files are present, but does not re-serialize the keyframes.")
    add("")
    add("## 10. Limits")
    add("")
    add("* All 13 AnimSets exported to PSA; no set was skipped. The three AnimTrees are "
        "recorded but do not own sequences: `Batmobile_Skel_Ctrl_Door` has no sequence on "
        "its `AnimNodeSequence`, and `Batwing_Vehicle_AnimTree` points at "
        "`Batwing_Rescue_01`.")
    add("* `SequenceLength`, `NumFrames` and `RateScale` are the offset-156/160/168 tags. "
        "In this PSA version `ANIMINFO.TrackTime` is the **frame count**, not seconds; "
        "`psa_length` in `ANIMATIONS.json` is `TrackTime / PSA rate` and agrees with the "
        "package length (0 mismatches). The two values are kept separately.")
    add("* The bone list is `TrackBoneNames` minus `all`; `trans` and `rot` components are "
        "null in the keyframes. A bone with only one component still counts as animated.")
    add("* The `AnimNotify_Sound` with no `AkEvent` reference is recorded with `sound: "
        "null`; it is not dropped. Notify payloads outside the two named classes are kept "
        "generically, not interpreted.")
    add("* `AnimNotify` times are seconds (all %d are within their sequence's length); the "
        "fraction column is only a convenience." % c["notify_instances"])
    add("* Mechanism classes are a bone-based taxonomy, not shipped gameplay state. "
        "`transformation` groups all three-or-more-mechanism reconfigurations and shell "
        "motion; `other` includes camera, batwing, chair, rear door, winch and jet motion.")
    add("")
    add("## 11. Reproduce")
    add("")
    add("```bash")
    add("python Tools/scripts/grab_anims.py --write   # ANIMATIONS.json + .md + keyframes")
    add("python Tools/scripts/grab_anims.py --check   # re-derive and compare the two records")
    add("```")
    add("")
    add("Environment: `BMAK_GAME_DIR` (cooked packages) and `BMAK_ANIM_DIR` (the umodel "
        "exports). Defaults are the paths used by the Batmobile lab.")
    add("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------------------------
# entry points


def public_doc(doc: dict) -> dict:
    """Drop the in-memory `_removed` index maps; the JSON keeps names only."""
    out = dict(doc)
    out["sequences"] = [{k: v for k, v in s.items() if not k.startswith("_")}
                        for s in doc["sequences"]]
    return out


def json_text(doc: dict) -> str:
    return json.dumps(public_doc(doc), indent=1, ensure_ascii=False) + "\n"


def write(doc: dict) -> None:
    OUT_JSON.write_text(json_text(doc), encoding="utf-8")
    OUT_MD.write_text(render_md(doc), encoding="utf-8")
    print("wrote %s (%d bytes)" % (OUT_JSON, OUT_JSON.stat().st_size))
    print("wrote %s (%d bytes)" % (OUT_MD, OUT_MD.stat().st_size))
    count, total = write_keyframes(doc)
    c = doc["counts"]
    print("wrote %d keyframe files (%d bytes) under %s" % (count, total, KEY_DIR))
    print("%d sequences, %d sets, %d trees, %d notifies (%d sound, %d script); "
          "%d/%d named, %d bone lists, %d mechanisms"
          % (c["sequences"], c["sets"], c["trees"], c["notify_instances"],
             c["sound_notifies"], c["script_notifies"], c["named"], c["sequences"],
             c["with_bone_lists"], c["with_mechanism"]))


def check(doc: dict) -> int:
    bad = 0
    for path, text in ((OUT_JSON, json_text(doc)), (OUT_MD, render_md(doc))):
        if not path.exists():
            print("FAIL: %s is missing - run --write" % path)
            bad += 1
            continue
        old = path.read_text(encoding="utf-8")
        if old == text:
            print("ok %s" % path)
            continue
        bad += 1
        old_lines, new_lines = old.splitlines(), text.splitlines()
        at = next((i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b),
                  min(len(old_lines), len(new_lines)))
        print("FAIL: %s differs at line %d" % (path, at + 1))
        if at < len(old_lines):
            print("  on disk: %s" % old_lines[at][:160])
        if at < len(new_lines):
            print("  derived: %s" % new_lines[at][:160])
    c = doc["counts"]
    if bad:
        print("FAIL: animation record is stale")
        return 1
    present = 0
    for s in doc["sets"]:
        if s["keyframes"] and (KEY_DIR / s["keyframes"]).exists():
            present += 1
    print("PASS: %d sequences, %d sets, %d trees, %d PSA sequences, %d keys, "
          "%d notifies (%d sound, %d script); %d/%d named, %d bone lists, "
          "%d mechanisms; %d/%d keyframe files present"
          % (c["sequences"], c["sets"], c["trees"], c["psa_sequences"], c["psa_keys"],
             c["notify_instances"], c["sound_notifies"], c["script_notifies"],
             c["named"], c["sequences"], c["with_bone_lists"], c["with_mechanism"],
             present, len(doc["sets"])))
    if present != len(doc["sets"]):
        print("WARN: keyframe files are missing; run --write to regenerate them")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true",
                    help="regenerate ANIMATIONS.json, ANIMATIONS.md and the keyframes")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare the two records")
    a = ap.parse_args()
    if not a.write and not a.check:
        ap.error("choose --write or --check")
    doc = collect()
    if a.check:
        return check(doc)
    write(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
