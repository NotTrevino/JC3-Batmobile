#!/usr/bin/env python
"""jc3_door_angles.py - every JC3 door part tied to its hinge, with the open range in degrees.

G3-10e decoded the two angle limits of a `hkpLimitedHingeConstraintData` (+0x0FC min,
+0x100 max, radians).  This pass walks the whole vehicle fleet and follows the link the
parts module itself carries:

    parts[i].part_index                        the door (a `door_parts[]` entry)
    parts[i].world_collision_body_id           the body that part rides on
    parts[i].constraint_index                  index into the physics system's constraint array
    hknpPhysicsSystemData +0x50, 24 B records  { constraint-data pointer @+0x00, body u32 @+0x08,
                                                 0x7fffffff @+0x0C, 0 @+0x10/+0x14 }
    hkpLimitedHingeConstraintData +0x0FC/+0x100  min / max angle, radians

The chain is decoded from the shipped bytes: the module comes out of the entity's own
`.ee` bundle, the physics file is the `.physicsc` member of the same bundle whose name is
`<module stem>.physicsc`, and the constraint record is read at `constraint_index`.

Oracles (`--check` re-runs every one against a fresh decode):
  * every record's +0x00 resolves to a `*ConstraintData` object and the record set equals
    the file's constraint-object set, in ascending offset order, with the 24 B stride
    fitting the array exactly;
  * +0x0C is 0x7fffffff and +0x10/+0x14 are 0 in every record;
  * every door part's `constraint_index` is in range and resolves to a limited hinge;
  * min <= max, both within +/-pi, both on a 0.5-degree grid, frame A orthonormal;
  * the record's body u32 equals the part's body id in 330 of 334 rows - the four that do
    not are listed by name and must not change;
  * the vanilla Serpente's three doors are 0..80, 0..80 and 0..70, the vanilla
    `vanilla_v0300.ee` bundle carries byte-identical module and physics members, and the
    four sampled vehicles agree with G2-15's published `DOORS.json`.

What is NOT decoded and stays UNKNOWN: what drives a door (no rate, curve or interaction
is stored), the meaning of the record's +0x0C constant, which body frame the hinge axis and
pivot are in, and why four parts' body ids differ from their record's body u32.

    python Tools/scripts/jc3_door_angles.py --write
    python Tools/scripts/jc3_door_angles.py --check
"""

import hashlib
import json
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3grab  # noqa: E402
import jc3hkx  # noqa: E402
import jc3index  # noqa: E402
from eetoc import sarc_dir, unaaf  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab")
OUT_MD = os.path.join(OUT, "DOOR_ANGLES.md")
OUT_JSON = os.path.join(OUT, "DOOR_ANGLES.json")
G2_15 = os.path.join(OUT, "DOORS.json")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
VANILLA_EE = os.path.join(RAW, "vanilla_v0300.ee")
VEHICLE_PREFIX = "editor/entities/jc_vehicles/"
PARTS_SUFFIX = "_vehicle_parts.vmodc"
LIMITED = "hkpLimitedHingeConstraintData"

SYSTEM_DATA = "hknpPhysicsSystemData"
CONSTRAINT_ARRAY = 0x50       # hkArray slot inside hknpPhysicsSystemData
REC_STRIDE = 24               # bytes per constraint-instance record
REC_DATA = 0x00               # hkpConstraintData* (fixup target)
REC_BODY = 0x08               # u32 body id
REC_SENTINEL = 0x0C           # constant 0x7fffffff
REC_TAIL = (0x10, 0x14)       # two zero u32
HINGE_MIN = 0x0FC
HINGE_MAX = 0x100
HINGE_FACTOR = 0x104
FRAME_A = 0x030
PIVOT = 0x060
SENTINEL = 0x7FFFFFFF

DEG = 180.0 / math.pi
BODY_MISMATCH_EXPECTED = {
    ("vintagesports_vehicle_parts.vmodc", "vintagesports_door_f_l", 21, 16),
    ("vintagesports_vehicle_parts.vmodc", "vintagesports_door_f_r", 24, 19),
    ("vintagesports_vehicle_parts.vmodc", "vintagesports_hood", 32, 29),
    ("oldbus_vehicle_parts.vmodc", "oldbus_trunk", 49, 50),
}


# ------------------------------------------------------------------ small helpers
def sha1(blob: bytes) -> str:
    return hashlib.sha1(blob).hexdigest()


def r3(v: float) -> float:
    """Round to 3 decimals, folding -0.0 to 0.0 so the output is stable."""
    v = round(v, 3)
    return 0.0 if v == 0 else v


def u32(blob: bytes, base: int, at: int) -> int:
    return struct.unpack_from("<I", blob, base + at)[0]


def f32(blob: bytes, base: int, at: int) -> float:
    return struct.unpack_from("<f", blob, base + at)[0]


def axis_class(axis) -> str:
    """Same bucket G2-15 used: which car axis the hinge's frame row 0 is closest to."""
    x, y, z = (abs(v) for v in axis)
    big = max(x, y, z)
    if big == 0:
        return "none"
    if big - sorted((x, y, z))[1] < 0.15:
        return "oblique"
    if x == big:
        return "X (transverse)"
    if y == big:
        return "Y (vertical)"
    return "Z (longitudinal)"


def frame(pf, base: int, off: int) -> dict:
    """Frame A: three 16 B rows (unit axes) and the translation at +0x30."""
    blob = pf.blob
    rows = [[f32(blob, base, off + FRAME_A + 16 * r + 4 * c) for c in range(3)] for r in range(3)]
    w = [f32(blob, base, off + FRAME_A + 16 * r + 12) for r in range(3)]
    dots = [sum(rows[a][k] * rows[b][k] for k in range(3))
            for a, b in ((0, 1), (0, 2), (1, 2))]
    lens = [math.sqrt(sum(v * v for v in row)) for row in rows]
    det = (rows[0][0] * (rows[1][1] * rows[2][2] - rows[1][2] * rows[2][1])
           - rows[0][1] * (rows[1][0] * rows[2][2] - rows[1][2] * rows[2][0])
           + rows[0][2] * (rows[1][0] * rows[2][1] - rows[1][1] * rows[2][0]))
    return {
        "rows": rows, "w": w,
        "axis": rows[0],
        "pivot": [f32(blob, base, off + PIVOT + 4 * k) for k in range(3)],
        "orthonormal": (all(abs(d) < 1e-3 for d in dots)
                        and all(abs(l - 1.0) < 1e-3 for l in lens)
                        and abs(det - 1.0) < 1e-3),
        "det": det,
    }


# --------------------------------------------------------------- entity decoding
def vehicle_entities(rows: list) -> list:
    return sorted({r["path"] for r in rows
                   if r["path"].startswith(VEHICLE_PREFIX) and r["path"].endswith(".ee")})


def decode_module(blob: bytes) -> dict:
    """Parts, the `door_parts[]` index array, and the raw row map of a parts module."""
    adf = jc3adf.Adf(blob)
    rows = {path: value for path, _t, value in jc3adf.walk(adf)}
    door_indices, i = [], 0
    while "door_parts[%d].part_index" % i in rows:
        door_indices.append(rows["door_parts[%d].part_index" % i])
        i += 1
    return {"parts": jc3adf.parts(adf), "door_indices": door_indices}


def physics_members(ee: str, rows: list) -> list:
    """Every `.physicsc` blob the entity bundle reaches, deduplicated."""
    return jc3hkx.physicsc_of(ee, rows, GAME)


def decode_physics(blob: bytes) -> dict:
    """Objects, the system-data constraint array and its records, plus hinge payloads."""
    pf = jc3hkx.Packfile(blob)
    base = pf.base
    systems = [o for o in pf.objects if o.cls == SYSTEM_DATA]
    if len(systems) != 1:
        return {"objects": len(pf.objects), "system_data": len(systems), "records": [],
                "constraint_objects": 0, "array": None}
    sd = systems[0]
    arr = pf.array(sd.offset + CONSTRAINT_ARRAY)
    nxt = pf.next_target(arr["ptr"]) if arr["ptr"] else arr["ptr"]
    records = []
    for i in range(arr["size"]):
        at = arr["ptr"] + REC_STRIDE * i
        ptr = pf.pointers.get(at, 0)
        cls = pf._starts.get(ptr, "") if ptr else ""
        rec = {
            "index": i, "slot": at, "data": ptr, "class": cls,
            "body": u32(blob, base, at + REC_BODY),
            "sentinel": u32(blob, base, at + REC_SENTINEL),
            "tail": [u32(blob, base, at + t) for t in REC_TAIL],
        }
        if cls == LIMITED:
            ext = pf.extents[ptr]
            rec["extent"] = ext
            rec["factor"] = f32(blob, base, ptr + HINGE_FACTOR)
            rec["min_rad"] = f32(blob, base, ptr + HINGE_MIN)
            rec["max_rad"] = f32(blob, base, ptr + HINGE_MAX)
            rec["min_deg"] = r3(rec["min_rad"] * DEG)
            rec["max_deg"] = r3(rec["max_rad"] * DEG)
            rec["travel_deg"] = r3((rec["max_rad"] - rec["min_rad"]) * DEG)
            fr = frame(pf, base, ptr)
            rec["axis"] = [r3(v) for v in fr["axis"]]
            rec["axis_class"] = axis_class(fr["axis"])
            rec["pivot"] = [r3(v) for v in fr["pivot"]]
            rec["frame_orthonormal"] = fr["orthonormal"]
            rec["frame_det"] = r3(fr["det"])
        records.append(rec)
    return {
        "objects": len(pf.objects),
        "system_data": 1,
        "system_data_offset": sd.offset,
        "array": {"slot": sd.offset + CONSTRAINT_ARRAY, "ptr": arr["ptr"],
                  "size": arr["size"], "capacity": arr["capacity"],
                  "stride": REC_STRIDE, "pad_after": (nxt - arr["ptr"] - REC_STRIDE * arr["size"])
                  if arr["ptr"] else None},
        "records": records,
        "constraint_objects": sum(1 for o in pf.objects if "Constraint" in o.cls),
        "constraint_offsets": sorted(o.offset for o in pf.objects if "Constraint" in o.cls),
    }


# ---------------------------------------------------------------------- the fleet
def collect() -> dict:
    rows = jc3index.load_index(OUT)
    entities = vehicle_entities(rows)
    modules: dict = {}          # (member path, sha1) -> car; a path can ship two payloads
    anomalies: list = []
    with_doors: set = set()
    for ee in entities:
        entry = jc3detail.pick(rows, ee)
        stream, members = jc3detail.inner_files(jc3grab.read_entry(entry, GAME))
        mods = sorted(m for m in members if m[0].endswith(PARTS_SUFFIX))
        if not mods:
            anomalies.append({"entity": ee, "what": "no parts module"})
            continue
        for name, off, size in mods:
            blob = stream[off:off + size]
            digest = sha1(blob)
            car = modules.get((name, digest))
            if car is None:
                dec = decode_module(blob)
                car = {"module": name, "module_sha1": digest, "module_bytes": len(blob),
                       "parts": dec["parts"], "door_indices": dec["door_indices"],
                       "variants": []}
                modules[(name, digest)] = car
            if ee not in car["variants"]:
                car["variants"].append(ee)
            if car["door_indices"]:
                with_doors.add(ee)
    entities_with_doors = len(with_doors)

    cars = []
    physics_ok = 0
    for key in sorted(modules):
        car = modules[key]
        name = car["module"]
        if not car["door_indices"]:
            continue
        stem = os.path.basename(name)[:-len(PARTS_SUFFIX)]
        want = stem + ".physicsc"
        found = {}
        for ee in car["variants"]:
            files = physics_members(ee, rows)
            hits = [(n, b) for n, b in files if os.path.basename(n) == want]
            if len(hits) != 1:
                anomalies.append({"entity": ee, "what": "physics member for module",
                                  "module": name, "want": want,
                                  "seen": [n for n, _b in files]})
                continue
            pname, pblob = hits[0]
            found.setdefault((pname, sha1(pblob)), []).append(ee)
        if len(found) > 1:
            anomalies.append({"module": name, "what": "physics differs across variants",
                              "variants": {str(k[0]): len(v) for k, v in found.items()}})
        car["physics"] = None
        car["constraint_offsets"] = []
        car["_records"] = []
        if found:
            pname, pdigest = sorted(found)[0]
            first_ee = min(found[(pname, pdigest)])
            pblob = None
            for n, b in physics_members(first_ee, rows):
                if os.path.basename(n) == want:
                    pblob = b
                    break
            if pblob is not None:
                physics_ok += 1
                phys = decode_physics(pblob)
                car["physics"] = {"name": pname, "sha1": sha1(pblob), "bytes": len(pblob),
                                  "objects": phys["objects"],
                                  "system_data": phys["system_data"],
                                  "system_data_offset": phys.get("system_data_offset"),
                                  "array": phys.get("array"),
                                  "constraint_objects": phys["constraint_objects"]}
                car["constraint_offsets"] = phys["constraint_offsets"]
                car["_records"] = phys["records"]
        recs = car["_records"]
        by_index = {p["part_index"]: p for p in car["parts"]}
        doors = []
        for part_index in car["door_indices"]:
            part = by_index.get(part_index)
            if part is None:
                anomalies.append({"module": name, "what": "door part missing",
                                  "part_index": part_index})
                continue
            ci = part["constraint_index"]
            row = {
                "part_index": part_index,
                "part_name": part["name"],
                "behaviour": part["behavior"],
                "parent_part_index": part["parent_part_index"],
                "body_id": part["world_collision_body_id"],
                "constraint_index": ci,
                "in_door_array": car["door_indices"].count(part_index),
            }
            if not isinstance(ci, int) or ci < 0 or ci >= len(recs):
                row["hinge"] = None
                if not recs and isinstance(ci, int) and ci >= 0:
                    row["why_no_hinge"] = "physics file not resolved for this car"
                elif isinstance(ci, int) and ci >= 0:
                    row["why_no_hinge"] = ("constraint_index %d is outside the %d records"
                                           % (ci, len(recs)))
                else:
                    row["why_no_hinge"] = "constraint_index %r (no constraint)" % (ci,)
                doors.append(row)
                continue
            rec = recs[ci]
            hinge = {
                "record_index": rec["index"],
                "record_slot": rec["slot"],
                "data_offset": rec["data"],
                "class": rec["class"],
                "body_id": rec["body"],
                "body_matches_part": rec["body"] == part["world_collision_body_id"],
            }
            if rec["class"] == LIMITED:
                hinge.update({
                    "min_rad": rec["min_rad"], "max_rad": rec["max_rad"],
                    "min_deg": rec["min_deg"], "max_deg": rec["max_deg"],
                    "travel_deg": rec["travel_deg"],
                    "min_at": rec["data"] + HINGE_MIN,
                    "max_at": rec["data"] + HINGE_MAX,
                    "factor": rec["factor"],
                    "axis": rec["axis"], "axis_class": rec["axis_class"],
                    "pivot": rec["pivot"],
                    "frame_orthonormal": rec["frame_orthonormal"],
                })
            row["hinge"] = hinge
            doors.append(row)
        car["doors"] = doors
        car["parts_in_module"] = len(car.pop("parts"))
        cars.append(car)
    for car in cars:
        car.setdefault("doors", [])
        car.setdefault("parts_in_module", len(car.pop("parts", []) or []))

    doc = {
        "meta": {
            "task": "JC3 door parts -> body -> hinge -> open range",
            "generated_by": "Tools/scripts/jc3_door_angles.py",
            "game": GAME.replace("\\", "/"),
            "index": "Research/JC3Grab/INDEX.json",
            "g2_15": "Research/JC3Grab/DOORS.json",
            "vanilla_bundle": VANILLA_EE.replace("\\", "/"),
            "entities_scanned": len(entities),
            "entities_with_door_parts": entities_with_doors,
            "cars_with_door_parts": len(cars),
            "cars_with_physics": physics_ok,
            "door_rows": sum(len(c["doors"]) for c in cars),
            "door_rows_with_hinge": sum(1 for c in cars for d in c["doors"] if d["hinge"]),
            "door_rows_without_hinge": sum(1 for c in cars for d in c["doors"] if not d["hinge"]),
            "constraint_records": sum((c.get("physics") or {}).get("array", {}).get("size", 0)
                                      for c in cars),
            "labels": {
                "decoded": "read at the stated offset/file, oracle named in section 7",
                "derived": "a rule over decoded inputs (e.g. travel = max - min)",
                "UNKNOWN": "no header/decoder pins it; the blocker is named in section 8",
            },
            "offsets": {
                "module": "parts[i].part_index, parts[i].world_collision_body_id, "
                          "parts[i].constraint_index (ADF rows of <car>_vehicle_parts.vmodc)",
                "constraint_array": "hknpPhysicsSystemData +0x%02X (hkArray: ptr, size, "
                                    "capacityAndFlags)" % CONSTRAINT_ARRAY,
                "constraint_record": "24 B: +0x00 hkpConstraintData* (fixup), +0x08 u32 body, "
                                     "+0x0C 0x7fffffff, +0x10/+0x14 zero",
                "hinge_limits": "+0x%02X min, +0x%02X max, +0x%02X factor (radians)"
                                % (HINGE_MIN, HINGE_MAX, HINGE_FACTOR),
                "hinge_frame": "frame A rows at +0x%02X (+0x10 stride), pivot at +0x%02X, "
                               "data-section relative" % (FRAME_A, PIVOT),
            },
        },
        "cars": cars,
        "anomalies": anomalies,
    }
    doc["summary"] = summarise(cars)
    doc["exceptions"] = exceptions(cars)
    doc["vanilla_serpente"] = vanilla_serpente(doc, rows)
    doc["cross_check_g2_15"] = cross_check(doc)
    doc["oracles"] = oracles(doc)
    doc["unknowns"] = UNKNOWNS
    for car in doc["cars"]:
        car.pop("_records", None)
    return doc


def summarise(cars: list) -> dict:
    by_beh: dict = {}
    by_cat: dict = {}
    for car in cars:
        cat = car["module"].split("/")[2]
        n = len(car["doors"])
        by_cat[cat] = by_cat.get(cat, 0) + n
        for d in car["doors"]:
            b = by_beh.setdefault(d["behaviour"] or "None",
                                  {"rows": 0, "cars": set(), "pairs": {}, "travel": []})
            b["rows"] += 1
            b["cars"].add(car["module"])
            h = d["hinge"]
            if h and h.get("min_deg") is not None:
                key = "%g..%g" % (h["min_deg"], h["max_deg"])
                b["pairs"][key] = b["pairs"].get(key, 0) + 1
                b["travel"].append(h["travel_deg"])
    behaviours = []
    for name, b in sorted(by_beh.items(), key=lambda kv: (-kv[1]["rows"], kv[0])):
        behaviours.append({
            "behaviour": name, "rows": b["rows"], "cars": len(b["cars"]),
            "pairs": dict(sorted(b["pairs"].items(), key=lambda kv: (-kv[1], kv[0]))),
            "min_travel_deg": min(b["travel"]) if b["travel"] else None,
            "max_travel_deg": max(b["travel"]) if b["travel"] else None,
        })
    limit_pairs: dict = {}
    for car in cars:
        for d in car["doors"]:
            h = d["hinge"]
            if h and h.get("min_deg") is not None:
                key = "%g..%g" % (h["min_deg"], h["max_deg"])
                limit_pairs[key] = limit_pairs.get(key, 0) + 1
    return {
        "by_behaviour": behaviours,
        "by_category": dict(sorted(by_cat.items())),
        "limit_pairs": dict(sorted(limit_pairs.items(), key=lambda kv: (-kv[1], kv[0]))),
        "cars_per_category": {c: sum(1 for x in cars if x["module"].split("/")[2] == c)
                              for c in sorted({x["module"].split("/")[2] for x in cars})},
    }


def exceptions(cars: list) -> dict:
    no_hinge = [{"module": c["module"], "part": d["part_name"],
                 "behaviour": d["behaviour"], "constraint_index": d["constraint_index"],
                 "why": d.get("why_no_hinge")}
                for c in cars for d in c["doors"] if not d["hinge"]]
    mismatch = [{"module": c["module"], "part": d["part_name"],
                 "part_body_id": d["body_id"],
                 "record_body_id": d["hinge"]["body_id"],
                 "constraint_index": d["constraint_index"]}
                for c in cars for d in c["doors"]
                if d["hinge"] and not d["hinge"]["body_matches_part"]]
    other = [{"module": c["module"], "part": d["part_name"],
              "class": d["hinge"]["class"]}
             for c in cars for d in c["doors"]
             if d["hinge"] and d["hinge"]["class"] != LIMITED]
    return {"no_hinge": no_hinge, "body_id_mismatch": mismatch,
            "non_limited_hinge": other}


def vanilla_serpente(doc: dict, rows: list) -> dict:
    path = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
            "sportsmuscle_vehicle_parts.vmodc")
    car = next((c for c in doc["cars"] if c["module"] == path), None)
    out = {"module": path, "found": car is not None, "doors": [],
           "bundle": VANILLA_EE.replace("\\", "/"), "bundle_available": os.path.exists(VANILLA_EE)}
    if car is None:
        return out
    for d in car["doors"]:
        h = d["hinge"] or {}
        out["doors"].append({
            "part_index": d["part_index"], "part_name": d["part_name"],
            "behaviour": d["behaviour"], "body_id": d["body_id"],
            "constraint_index": d["constraint_index"],
            "hinge_at": h.get("data_offset"), "min_deg": h.get("min_deg"),
            "max_deg": h.get("max_deg"), "travel_deg": h.get("travel_deg"),
            "axis": h.get("axis"), "pivot": h.get("pivot"),
        })
    out["module_sha1"] = car["module_sha1"]
    out["physics_sha1"] = (car.get("physics") or {}).get("sha1")
    if not os.path.exists(VANILLA_EE):
        out["bundle_check"] = None
        return out
    stream = unaaf(open(VANILLA_EE, "rb").read())
    members = {n: (off, size) for n, off, size in sarc_dir(stream)}
    phys_name = (car.get("physics") or {}).get("name")
    checks = {}
    for label, name, want in (("module", path, car["module_sha1"]),
                              ("physics", phys_name, out["physics_sha1"])):
        if not name or name not in members:
            checks[label] = {"member": name, "present": False}
            continue
        off, size = members[name]
        got = sha1(stream[off:off + size])
        checks[label] = {"member": name, "present": True, "sha1": got, "matches": got == want}
    out["bundle_check"] = checks
    return out


def cross_check(doc: dict) -> dict:
    if not os.path.exists(G2_15):
        return {"available": False, "rows": 0, "agree": 0, "disagree": []}
    old = json.load(open(G2_15, encoding="utf-8"))
    by_entity = {}
    for car in doc["cars"]:
        for ee in car["variants"]:
            by_entity[ee] = car
    agree, disagree, total = 0, [], 0
    for sample in old.get("samples", []):
        car = by_entity.get(sample.get("entity"))
        if car is None:
            continue
        mine = {d["part_name"]: d for d in car["doors"]}
        for row in sample.get("door_parts", []):
            total += 1
            d = mine.get(row["name"])
            h = (d or {}).get("hinge") or {}
            old_h = row.get("hinge") or {}
            same = (d is not None and d["constraint_index"] == row.get("constraint")
                    and h.get("class") == old_h.get("class")
                    and h.get("min_deg") is not None
                    and round(h["min_deg"], 1) == round(old_h.get("min_deg", 1e9), 1)
                    and round(h["max_deg"], 1) == round(old_h.get("max_deg", 1e9), 1))
            if same:
                agree += 1
            else:
                disagree.append({"entity": sample.get("entity"), "part": row.get("name"),
                                 "mine": None if d is None else
                                 [d["constraint_index"], h.get("min_deg"), h.get("max_deg")],
                                 "g2_15": [row.get("constraint"), old_h.get("min_deg"),
                                           old_h.get("max_deg")]})
    return {"available": True, "rows": total, "agree": agree, "disagree": disagree}


UNKNOWNS = [
    "what drives a door: the module stores no open rate, animation curve or interaction for "
    "the part, so the hinge limits are the authored travel, not a measured swing (G2-15 §1/§3)",
    "the meaning of the constraint record's +0x0C u32: it is 0x7fffffff in every record of the "
    "fleet, decoded as a constant, but no Havok 2014 header in this project names the field",
    "why four door parts' body ids differ from their constraint record's body u32 "
    "(vintagesports door_f_l/door_f_r/hood, oldbus_trunk): the hinge is still resolved by the "
    "module's own constraint_index, and its pivot mirrors the opposite door with the same "
    "limits, but the two numberings are not one space and the body enumeration is not decoded",
    "the field names inside the 24 B constraint record: its stride and typed pointer are "
    "decoded by pattern (stride fits the array, +0x00 resolves to a *ConstraintData), not from "
    "a Havok header",
    "the frame the hinge axis and pivot are expressed in (body-local vs parent): the values "
    "are decoded as frame A row 0 and the translation, but comparing them to part centroids "
    "does not hold across the fleet, so that comparison is not used as an oracle",
    "which column of the hinge frame is the joint's free axis: G3-10e §2 leaves that UNKNOWN; "
    "the axis column reported here is frame A row 0, the convention G2-15 published",
    "the open range of the four door rows with constraint_index -1 (propeller and floatplane "
    "wing parts): there is no hinge at all, so no range is authored in the files",
    "vehicles outside INDEX.json's 233 jc_vehicles entity bundles: nothing else with a parts "
    "module was scanned, so a vehicle absent from the index is absent here",
]


# ---------------------------------------------------------------------- oracles
def oracles(doc: dict) -> dict:
    cars = doc["cars"]
    door_rows = [(c, d) for c in cars for d in c["doors"]]
    with_hinge = [(c, d) for c, d in door_rows if d["hinge"]]
    limited = [(c, d) for c, d in with_hinge if d["hinge"]["class"] == LIMITED]
    recs = [r for c in cars for r in records_of(c)]
    checks = {}

    checks["cars_have_physics"] = (doc["meta"]["cars_with_physics"] == len(cars))
    checks["record_count_equals_constraint_objects"] = all(
        (c.get("physics") or {}).get("array", {}).get("size")
        == (c.get("physics") or {}).get("constraint_objects") for c in cars)
    checks["record_pointers_are_constraint_objects"] = all(
        r["data"] in set(c.get("constraint_offsets") or []) for c in cars for r in records_of(c))
    checks["record_set_equals_constraint_objects"] = all(
        sorted(r["data"] for r in records_of(c)) == (c.get("constraint_offsets") or []) for c in cars)
    checks["records_ascending_by_offset"] = all(
        [r["data"] for r in records_of(c)] == sorted(r["data"] for r in records_of(c))
        for c in cars)
    checks["record_stride_fits_array"] = all(
        ((c.get("physics") or {}).get("array") or {}).get("pad_after") is not None
        and 0 <= c["physics"]["array"]["pad_after"] < 16 for c in cars)
    checks["record_sentinel_constant"] = bool(recs) and all(
        r["sentinel"] == SENTINEL and r["tail"] == [0, 0] for r in recs)
    checks["constraint_index_in_range"] = all(
        isinstance(d["constraint_index"], int) and 0 <= d["constraint_index"]
        < len(records_of(c)) for c, d in with_hinge)
    checks["every_door_hinge_is_limited"] = len(limited) == len(with_hinge) and bool(limited)
    checks["door_rows_resolve_to_a_part"] = len(door_rows) == doc["meta"]["door_rows"]
    checks["hinge_min_le_max"] = all(
        d["hinge"]["min_rad"] <= d["hinge"]["max_rad"] + 1e-9 for _c, d in limited)
    checks["hinge_limits_within_pi"] = all(
        abs(d["hinge"]["min_rad"]) <= math.pi + 1e-6
        and abs(d["hinge"]["max_rad"]) <= math.pi + 1e-6 for _c, d in limited)
    checks["hinge_limits_on_half_degree_grid"] = all(
        all(abs(v / 0.5 - round(v / 0.5)) < 0.02
            for v in (d["hinge"]["min_deg"], d["hinge"]["max_deg"])) for _c, d in limited)
    checks["hinge_factor_is_one"] = all(d["hinge"]["factor"] == 1.0 for _c, d in limited)
    checks["hinge_frame_orthonormal"] = all(
        d["hinge"]["frame_orthonormal"] for _c, d in limited)
    mismatch = {("%s" % os.path.basename(c["module"]), d["part_name"], d["body_id"],
                 d["hinge"]["body_id"]) for c, d in with_hinge
                if not d["hinge"]["body_matches_part"]}
    checks["body_id_mismatch_set_unchanged"] = mismatch == BODY_MISMATCH_EXPECTED
    checks["body_ids_match_mostly"] = (
        sum(1 for c, d in with_hinge if d["hinge"]["body_matches_part"])
        == len(with_hinge) - len(BODY_MISMATCH_EXPECTED))

    van = doc["vanilla_serpente"]
    by_name = {d["part_name"]: d for d in van["doors"]}
    checks["serpente_vanilla_limits"] = (
        van["found"]
        and [(by_name[n]["min_deg"], by_name[n]["max_deg"]) for n in
             ("sportsmuscle_door_f_l", "sportsmuscle_door_f_r", "sportsmuscle_hood_signature")]
        == [(0.0, 80.0), (0.0, 80.0), (0.0, 70.0)])
    bc = van.get("bundle_check") or {}
    checks["vanilla_bundle_members_match"] = (
        not van["bundle_available"]
        or (bc.get("module", {}).get("matches") and bc.get("physics", {}).get("matches")))
    cross = doc["cross_check_g2_15"]
    checks["agrees_with_g2_15_samples"] = (
        not cross["available"] or (cross["rows"] > 0 and cross["agree"] == cross["rows"]))
    checks["no_anomalies"] = not doc["anomalies"]

    return {
        "all_ok": all(checks.values()),
        "checks": checks,
        "detail": {
            "cars": len(cars), "door_rows": len(door_rows), "with_hinge": len(with_hinge),
            "limited": len(limited), "records": len(recs),
            "body_id_mismatch": sorted(list(x) for x in mismatch),
            "g2_15": {"rows": cross["rows"], "agree": cross["agree"]},
        },
    }


def records_of(car: dict) -> list:
    return car.get("_records") or []


# ------------------------------------------------------------------- rendering
def fmt(v) -> str:
    return "%g" % v if v is not None else "-"


def car_labels(cars: list) -> dict:
    """Readable ``class/vehicle[/subdir]`` label; disambiguated when one path ships two payloads."""
    labels = {}
    for c in cars:
        cls = c["module"].split("/")[2]
        rest = c["module"].split("/jc_vehicles/")[1][len(cls) + 1:]
        rest = rest[:-len(os.path.basename(c["module"]))].rstrip("/")
        labels[id(c)] = (cls + "/" + rest).rstrip("/")
    seen = {}
    for label in labels.values():
        seen[label] = seen.get(label, 0) + 1
    for c in cars:
        if seen[labels[id(c)]] > 1:
            labels[id(c)] += " [sha %s]" % c["module_sha1"][:8]
    return labels


def render(doc: dict) -> str:
    m = doc["meta"]
    L = []
    A = L.append
    A("# Every JC3 door part, its body and its hinge range in degrees")
    A("")
    A("Generated by `%s` from the shipped bytes. `decoded` = read at the stated offset/file; "
      "`derived` = a rule over decoded inputs; `UNKNOWN` = no header or decoder pins it."
      % m["generated_by"])
    A("")
    A("A door is three things (`Research/JC3Grab/DOORS.md`): a part whose `behavior` names a "
      "door behaviour, an entry in the parts module's `door_parts[]`, and a "
      "`hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`. Since G3-10e the hinge's "
      "two angle limits decode at **+0x0FC (min)** and **+0x100 (max)**, radians - so the "
      "door's open range is exactly that pair.")
    A("")
    A("This page follows the whole link across the fleet: **%d entities** in `INDEX.json`, "
      "**%d cars** whose parts module carries `door_parts[]`, **%d door rows**, **%d of them "
      "on a limited hinge**, over **%d constraint records**."
      % (m["entities_scanned"], m["cars_with_door_parts"], m["door_rows"],
         m["door_rows_with_hinge"], m["constraint_records"]))
    A("")
    A("## 1. The chain, hop by hop")
    A("")
    A("| hop | stored where | field | oracle |")
    A("|---|---|---|---|")
    A("| 1 | `<car>_vehicle_parts.vmodc` | `door_parts[i].part_index` names a part | "
      "%d rows resolve to a part in their module |" % m["door_rows"])
    A("| 2 | same module | `parts[i].world_collision_body_id` = the body the part rides on | "
      "it equals hop 4's body u32 in %d/%d door rows |"
      % (len([1 for c in doc["cars"] for d in c["doors"]
              if d["hinge"] and d["hinge"]["body_matches_part"]]), m["door_rows_with_hinge"]))
    A("| 3 | same module | `parts[i].constraint_index` | in range in %d/%d rows |"
      % (m["door_rows_with_hinge"], m["door_rows_with_hinge"]))
    A("| 4 | `.physicsc`, `hknpPhysicsSystemData +0x50` | 24 B record: `+0x00` "
      "`hkpConstraintData*`, `+0x08` u32 body, `+0x0C` 0x7fffffff | record count = constraint "
      "object count in %d/%d files; pointer typed in every record |"
      % (len(doc["cars"]), len(doc["cars"])))
    A("| 5 | `.physicsc`, that constraint | class `%s`; `+0x0FC` min, `+0x100` max (rad), "
      "`+0x104` factor | min <= max %d/%d, within +/-pi %d/%d, on a 0.5-deg grid %d/%d |"
      % (LIMITED,
         sum(1 for c in doc["cars"] for d in c["doors"] if d["hinge"] and d["hinge"]["min_rad"] <= d["hinge"]["max_rad"]),
         m["door_rows_with_hinge"],
         sum(1 for c in doc["cars"] for d in c["doors"] if d["hinge"] and abs(d["hinge"]["min_rad"]) <= math.pi),
         m["door_rows_with_hinge"],
         sum(1 for c in doc["cars"] for d in c["doors"] if d["hinge"] and
             all(abs(v / 0.5 - round(v / 0.5)) < 0.02 for v in (d["hinge"]["min_deg"], d["hinge"]["max_deg"]))),
         m["door_rows_with_hinge"]))
    A("")
    A("Worked example - the vanilla Serpente's left door. `sportsmuscle_vehicle_parts.vmodc`'s "
      "`door_parts[0].part_index` is 1; part 1 is `sportsmuscle_door_f_l`, body "
      "`world_collision_body_id` 1, `constraint_index` 0. The `.physicsc` system data's "
      "constraint array (slot `hknpPhysicsSystemData+0x50`) has 11 records of 24 B; record 0 "
      "points at `0x4DA80` (`%s`) with body 1 at `+0x08`. Its `+0x0FC` reads 0.0 rad and its "
      "`+0x100` reads 1.3963 rad = 80 deg, so the door's open range is **0..80 deg**." % LIMITED)
    A("")
    A("## 2. The cars")
    A("")
    A("`class` is the entity folder (`01_land`, `02_air`, `03_sea`). `ranges` lists the "
      "distinct `min..max` pairs on that car's doors. `variants` counts the `.ee` entities "
      "that bundle the module; a module path that ships two different payloads appears twice, "
      "tagged with the first bytes of its sha1. G2-15's census read the 78 cached parts "
      "modules (56 with doors); this pass reads every entity bundle in the index, so it sees "
      "more cars, including air and sea vehicles that also carry door behaviours.")
    A("")
    labels = car_labels(doc["cars"])
    A("| car | doors | records | physics | variants | ranges (deg) |")
    A("|---|---:|---:|---|---:|---|")
    for c in doc["cars"]:
        label = labels[id(c)]
        pairs = {}
        for d in c["doors"]:
            h = d["hinge"]
            if h and h.get("min_deg") is not None:
                k = "%g..%g" % (h["min_deg"], h["max_deg"])
                pairs[k] = pairs.get(k, 0) + 1
        rng = ", ".join("%s x%d" % (k, v) if v > 1 else k for k, v in pairs.items()) or "-"
        ph = c.get("physics") or {}
        A("| `%s` | %d | %d | `%s` | %d | %s |"
          % (label, len(c["doors"]), (ph.get("array") or {}).get("size", 0),
             os.path.basename(ph.get("name") or "-"), len(c["variants"]), rng))
    A("")
    A("## 3. Every door row")
    A("")
    A("`body` is the part's `world_collision_body_id`; `con` is its `constraint_index`; `hinge @` "
      "is the constraint object's offset in the `.physicsc` data section; `min`/`max` are read "
      "at `hinge+0x0FC` / `hinge+0x100`; `travel` is `derived` as `max - min`. Every resolved "
      "hinge is a `hkpLimitedHingeConstraintData` (section 6).")
    A("")
    A("| car | part | behaviour | part idx | parent | body | con | hinge @ | axis | "
      "min deg | max deg | travel deg |")
    A("|---|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|")
    for c in doc["cars"]:
        label = labels[id(c)]
        for d in c["doors"]:
            h = d["hinge"] or {}
            axis = ("(" + ", ".join("%g" % v for v in h["axis"]) + ")") if h.get("axis") else "-"
            A("| `%s` | `%s` | %s | %d | %d | %d | %d | %s | %s | %s | %s | %s |"
              % (label, d["part_name"], d["behaviour"] or "-", d["part_index"],
                 d["parent_part_index"], d["body_id"], d["constraint_index"],
                 ("0x%05X" % h["data_offset"]) if h.get("data_offset") is not None else "-",
                 axis, fmt(h.get("min_deg")), fmt(h.get("max_deg")),
                 fmt(h.get("travel_deg"))))
    A("")
    s = doc["summary"]
    A("## 4. Summary by behaviour")
    A("")
    A("`rows` counts every `door_parts[]` row, including the four without a hinge; the pair "
      "counts and the travel range cover only the hinged rows.")
    A("")
    A("| behaviour | rows | cars | limit pairs (rows) | travel deg |")
    A("|---|---:|---:|---|---|")
    for b in s["by_behaviour"]:
        pairs = ", ".join("%s (%d)" % (k, v) for k, v in list(b["pairs"].items())[:4])
        if len(b["pairs"]) > 4:
            pairs += ", +%d more" % (len(b["pairs"]) - 4)
        A("| `%s` | %d | %d | %s | %s .. %s |"
          % (b["behaviour"], b["rows"], b["cars"], pairs or "-",
             fmt(b["min_travel_deg"]), fmt(b["max_travel_deg"])))
    A("")
    A("Fleet-wide limit pairs: %s."
      % ", ".join("%s (%d)" % (k, v) for k, v in doc["summary"]["limit_pairs"].items()))
    A("")
    A("## 5. The vanilla Serpente (sportsmuscle)")
    A("")
    van = doc["vanilla_serpente"]
    A("The donor's parts module is `%s`; every number below is read from it and from "
      "`sportsmuscle.physicsc` in the same entity bundle." % van["module"])
    A("")
    A("| part | behaviour | part idx | body | con | hinge @ | axis | min deg | max deg | "
      "travel deg | pivot |")
    A("|---|---|---:|---:|---:|---|---|---:|---:|---:|---|")
    for d in van["doors"]:
        A("| `%s` | %s | %d | %d | %d | %s | %s | %s | %s | %s | %s |"
          % (d["part_name"], d["behaviour"], d["part_index"], d["body_id"],
             d["constraint_index"], ("0x%05X" % d["hinge_at"]) if d["hinge_at"] else "-",
             "(" + ", ".join("%g" % v for v in (d["axis"] or [])) + ")" if d["axis"] else "-",
             fmt(d["min_deg"]), fmt(d["max_deg"]), fmt(d["travel_deg"]),
             "(" + ", ".join("%g" % v for v in (d["pivot"] or [])) + ")" if d["pivot"] else "-"))
    A("")
    bc = van.get("bundle_check")
    if bc:
        A("**Vanilla bundle cross-check.** `E:/Modding/_shared/gamedata/JC3grab/vanilla_v0300.ee` is "
          "an extracted vanilla Serpente bundle (566 members). Its members are byte-identical "
          "to the archive members this page decoded:")
        A("")
        A("| member | sha1 | matches this decode |")
        A("|---|---|---|")
        for label in ("module", "physics"):
            x = bc.get(label) or {}
            A("| `%s` | `%s` | %s |"
              % (os.path.basename(x.get("member") or "-"), (x.get("sha1") or "-")[:16],
                 "yes" if x.get("matches") else "**no**"))
        A("")
    else:
        A("`vanilla_v0300.ee` was not available, so the bundle cross-check did not run.")
        A("")
    A("## 6. Exceptions")
    A("")
    ex = doc["exceptions"]
    A("**%d door rows with no hinge at all** (`constraint_index` -1). Their open range does not "
      "exist in the files:" % len(ex["no_hinge"]))
    A("")
    A("| module | part | behaviour | constraint_index |")
    A("|---|---|---|---:|")
    for x in ex["no_hinge"]:
        A("| `%s` | `%s` | %s | %s |"
          % (os.path.basename(x["module"]), x["part"], x["behaviour"], x["constraint_index"]))
    A("")
    A("**%d door rows whose part body id differs from the constraint record's body u32.** The "
      "hinge is still the one the module's `constraint_index` names - its pivot is the mirror "
      "of the opposite door and its limits are the same - so the link is kept and the two "
      "numberings are reported side by side:" % len(ex["body_id_mismatch"]))
    A("")
    A("| module | part | part body id | record body u32 | con |")
    A("|---|---|---:|---:|---:|")
    for x in ex["body_id_mismatch"]:
        A("| `%s` | `%s` | %d | %d | %d |"
          % (os.path.basename(x["module"]), x["part"], x["part_body_id"],
             x["record_body_id"], x["constraint_index"]))
    A("")
    if ex["non_limited_hinge"]:
        A("**Door rows on a non-limited constraint:** %s"
          % ", ".join("%s (%s)" % (x["part"], x["class"]) for x in ex["non_limited_hinge"]))
        A("")
    else:
        A("No door row resolves to a constraint of another class: every one of the %d hinged "
          "door rows is a `%s`." % (m["door_rows_with_hinge"], LIMITED))
        A("")
    if doc["anomalies"]:
        A("**Decode anomalies:** %s" % json.dumps(doc["anomalies"], ensure_ascii=False))
        A("")
    A("## 7. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | result |")
    A("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        A("| `%s` | **%s** |" % (k, "pass" if v else "FAIL"))
    A("")
    A("The G2-15 cross-check replays that task's four sampled vehicles: %d/%d door rows agree "
      "on constraint index, class and both limits. The body-id exception set is pinned by name, "
      "so a new mismatch (or a fixed one) fails the check instead of drifting silently."
      % (doc["cross_check_g2_15"]["agree"], doc["cross_check_g2_15"]["rows"]))
    A("")
    A("## 8. UNKNOWNs")
    A("")
    for u in doc["unknowns"]:
        A("- %s" % u)
    A("")
    A("## 9. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/jc3_door_angles.py` | this pass, `--write` / `--check` |")
    A("| `Research/JC3Grab/DOOR_ANGLES.md` | this page |")
    A("| `Research/JC3Grab/DOOR_ANGLES.json` | the same, machine-readable, every value with its "
      "offset |")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------------ io
def build() -> dict:
    return collect()


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, sort_keys=False, ensure_ascii=False) + "\n"


def write() -> int:
    doc = build()
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(render(doc))
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps(doc))
    print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT).replace("\\", "/"),
                               os.path.relpath(OUT_JSON, ROOT).replace("\\", "/")))
    print("cars %d / door rows %d (hinged %d) / entities %d / records %d"
          % (doc["meta"]["cars_with_door_parts"], doc["meta"]["door_rows"],
             doc["meta"]["door_rows_with_hinge"], doc["meta"]["entities_scanned"],
             doc["meta"]["constraint_records"]))
    bad = [k for k, v in doc["oracles"]["checks"].items() if not v]
    print("oracles %d/%d%s"
          % (sum(1 for v in doc["oracles"]["checks"].values() if v),
             len(doc["oracles"]["checks"]),
             (" FAILING: " + ", ".join(bad)) if bad else ""))
    return 0 if doc["oracles"]["all_ok"] else 1


def check() -> int:
    doc = build()
    md = render(doc)
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    disk_md = open(OUT_MD, encoding="utf-8").read()
    disk_json = open(OUT_JSON, encoding="utf-8").read()
    if disk_md != md:
        import difflib
        diff = list(difflib.unified_diff(disk_md.splitlines(), md.splitlines(),
                                         "on disk", "rebuilt", n=1))
        fails.append("DOOR_ANGLES.md is stale: " + " | ".join(diff[2:6]))
    if disk_json != dumps(doc):
        fails.append("DOOR_ANGLES.json is stale")
    bad = [k for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        fails.append("oracles: " + ", ".join(bad))
    if fails:
        for f in fails:
            print("FAIL " + f)
        print("detail " + json.dumps(doc["oracles"]["detail"], ensure_ascii=False)[:2000])
        return 1
    print("OK cars %d / door rows %d (hinged %d) / entities %d / records %d; md+json "
          "byte-identical to a fresh decode"
          % (doc["meta"]["cars_with_door_parts"], doc["meta"]["door_rows"],
             doc["meta"]["door_rows_with_hinge"], doc["meta"]["entities_scanned"],
             doc["meta"]["constraint_records"]))
    print("oracles: " + json.dumps(doc["oracles"]["checks"], sort_keys=True))
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("--write", "--check"):
        print("usage: jc3_door_angles.py --write | --check")
        return 2
    return write() if sys.argv[1] == "--write" else check()


if __name__ == "__main__":
    raise SystemExit(main())
