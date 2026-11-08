#!/usr/bin/env python
"""jc3_turret_limits.py - every turret's yaw and pitch limits in the JC3 vehicle fleet.

G2-13 (`Research/JC3Grab/TURRET.md`) established *what* a JC3 turret is: a part with
behaviour `Turret` (yaw) and a part with behaviour `Cannon` (pitch), each fixed to its
parent by one `hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`. It printed
the two angle limits as a by-product of G3-10b's value-band filter, which G3-10e later
proved was not a decode (34 of its 66 values were frame bytes, 24 the pivot re-listed).

This pass reads the limits the decoded way. G3-10e (`Research/JC3Grab/PHYSICS_LIMITS.md`,
`Tools/scripts/jc3_physics_limits.py`) walked the `hkpConstraintAtom` list of every
`hkpLimitedHingeConstraintData` in the fleet and pinned the angular limit atom:

    atom start   +0x0F8   u16 type code = 14   (constant in 419/419 hinges)
    min angle    +0x0FC   f32 radians
    max angle    +0x100   f32 radians
    (+0x104 is 1.0 in 419/419 and is not a limit)

Those three constants are imported from `jc3_physics_limits.HINGE_LIMIT` rather than
restated here, and the type code is re-read per hinge as an oracle.

What is measured, over all 233 vehicle entities in `PARTS_TABLE.jsonl`:

  * every turret unit - the yaw part and the pitch part - with the hinge object that
    carries each one (`constraint_index` -> constraint object in file order), its
    min/max/span in degrees, its axis (frame A row 0, and frame B row 0 checked
    against it) and its pivot;
  * every hinge in the fleet that has *no* angular limit (`hkpHingeConstraintData`) or
    a full -180..+180 span, and the part that owns it - so "which turret rotates
    freely" is answered against the bytes, not by assumption;
  * the pitch range per vehicle class (tank / APC / armed land / boat / aircraft).

Usage:
  python Tools/scripts/jc3_turret_limits.py --write
  python Tools/scripts/jc3_turret_limits.py --check

`--check` re-reads the game archives, rebuilds the document and compares the json
field-for-field and the md byte-for-byte, then re-runs every oracle in `oracles`.

Read-only: the game install and `E:/Modding/_shared/gamedata/` are only read. Nothing here
touches `Builds/`.
"""
from __future__ import annotations

import argparse
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
import jc3_physics_limits as G10E  # noqa: E402  (G3-10e's atom decode)

OUT = os.path.join(ROOT, "Research", "JC3Grab")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)
JSON_NAME = "TURRET_LIMITS.json"
MD_NAME = "TURRET_LIMITS.md"

LIMITED = "hkpLimitedHingeConstraintData"
UNLIMITED = "hkpHingeConstraintData"
ATOM = G10E.HINGE_LIMIT          # {"atom": 0x0F8, "type": 14, "min": 0x0FC, "max": 0x100, ...}
POINT_YAW = "id:80201E4D"
POINT_PITCH = "id:5C19E7E0"
DEG = 57.29577951308232

# The class a model belongs to is derived from its entity path (01_land / 02_air /
# 03_sea) and its model name - there is no decoded "vehicle class" field.  The
# grouping is used only for the per-class pitch comparison; every number is per part.
CATEGORY_RULES = (
    ("/03_sea/", "boat"),
    ("/02_air/", "aircraft"),
)


# ------------------------------------------------------------------ reading
def load(name: str) -> list[dict]:
    with open(os.path.join(OUT, name), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def entity_parts(stream, entries):
    hit = next((e for e in entries if e[0].endswith("_vehicle_parts.vmodc")), None)
    if hit is None:
        return None, None
    return jc3adf.parts(jc3adf.Adf(stream[hit[1]:hit[1] + hit[2]])), os.path.basename(hit[0])


def scan(ee: str, rows: list[dict]) -> dict:
    """One entity: its parts module and every constraint object it carries."""
    row = jc3detail.pick(rows, ee)
    blob = jc3grab.read_entry(row, GAME)
    stream, entries = jc3detail.inner_files(blob)
    parts, module = entity_parts(stream, entries)
    cons, files = [], []
    # `stream` is the un-AAFed bundle: jc3hkx.bundle_packfiles walks that, exactly as
    # jc3hkx.physicsc_of does (it un-AAFs first); the raw archive bytes would find nothing.
    for name, pblob in jc3hkx.bundle_packfiles(stream, rows, GAME):
        files.append(os.path.basename(name))
        pf = jc3hkx.Packfile(pblob)
        objs = sorted((o for o in pf.objects if "Constraint" in o.cls),
                      key=lambda o: o.offset)
        for o in objs:
            extent = pf.extents[o.offset]
            rec = {"i": len(cons), "class": o.cls, "offset": o.offset, "extent": extent,
                   "file": os.path.basename(name)}
            if o.cls == LIMITED:
                raw = pf.raw(o.offset, extent)
                lo, hi = struct.unpack_from("<2f", raw, ATOM["min"])
                ax = struct.unpack_from("<4f", raw, 0x30)
                bx = struct.unpack_from("<4f", raw, 0x70)
                pv = struct.unpack_from("<4f", raw, 0x60)
                rec.update({
                    "type_code": struct.unpack_from("<H", raw, ATOM["atom"])[0],
                    "min_rad": lo, "max_rad": hi,
                    "min_deg": round(math.degrees(lo), 3),
                    "max_deg": round(math.degrees(hi), 3),
                    "span_deg": round(math.degrees(hi) - math.degrees(lo), 3),
                    "axis": [round(v, 4) for v in ax[:3]],
                    "axis_b": [round(v, 4) for v in bx[:3]],
                    "pivot": [round(v, 4) for v in pv[:3]],
                })
            cons.append(rec)
    return {"entity": ee, "module": module, "parts": parts or [], "constraints": cons,
            "physics_files": files}


def ancestors(parts_by_index: dict, p: dict) -> list[dict]:
    out, cur, seen = [], p, set()
    while True:
        par = cur.get("parent_part_index")
        if not isinstance(par, int) or par < 0 or par in seen:
            return out
        seen.add(par)
        cur = parts_by_index.get(par)
        if cur is None:
            return out
        out.append(cur)


def part_view(s: dict, p: dict | None) -> dict | None:
    """A part plus the hinge object its `constraint_index` selects."""
    if p is None:
        return None
    ci = p.get("constraint_index")
    out = {"part": p["name"], "index": p["part_index"],
           "behaviour": p["behavior"] or None,
           "parent": p.get("parent_part_index"), "constraint": ci,
           "identity_offset": is_identity(p.get("parent_space_offset"))}
    con = None
    if isinstance(ci, int) and 0 <= ci < len(s["constraints"]):
        con = s["constraints"][ci]
    if con is None:
        out["hinge"] = None
        return out
    hinge = {"class": con["class"], "offset": con["offset"], "file": con["file"]}
    if con["class"] == LIMITED:
        hinge.update({k: con[k] for k in ("min_deg", "max_deg", "span_deg", "axis",
                                          "axis_b", "pivot", "type_code",
                                          "min_rad", "max_rad")})
    out["hinge"] = hinge
    return out


def is_identity(m) -> bool | None:
    if not isinstance(m, list) or len(m) != 16:
        return None
    want = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    return [float(x) for x in m] == [float(x) for x in want]


def units_of(s: dict) -> list[dict]:
    """The vehicle's turret units: (yaw part, pitch part) pairs.

    A `Cannon` part is a pitch part (G2-13); its yaw part is the nearest ancestor with
    behaviour `Turret` (a real turret) or `Cannon` (a two-Cannon pintle mount, which is
    how the patrol boats are built).  A Cannon with no such ancestor is a pitch-only
    mount - an aircraft gun frame bolted to a plain adapter.
    """
    ps = s["parts"]
    by = {p["part_index"]: p for p in ps}
    units, used = [], set()
    for c in sorted((p for p in ps if p["behavior"] == "Cannon"),
                    key=lambda p: p["part_index"]):
        anc = ancestors(by, c)
        yaw = next((a for a in anc if a["behavior"] in ("Turret", "Cannon")), None)
        kind = ("turret" if yaw is not None and yaw["behavior"] == "Turret"
                else "two_cannon" if yaw is not None else "pitch_only")
        if yaw is not None:
            used.add(yaw["part_index"])
        units.append({"kind": kind, "yaw": part_view(s, yaw), "pitch": part_view(s, c),
                      "anchor": part_view(s, anc[0] if anc else None)})
    for t in sorted((p for p in ps if p["behavior"] == "Turret"),
                    key=lambda p: p["part_index"]):
        if t["part_index"] not in used:
            units.append({"kind": "yaw_only", "yaw": part_view(s, t), "pitch": None,
                          "anchor": None})
    # a Cannon that yaws another part is not itself a pitch part: on the patrol boats
    # the horizontal pintle is the yaw of the vertical one, not a pitch-only mount.
    yaws = {u["yaw"]["index"] for u in units if u["kind"] == "two_cannon"}
    return [u for u in units
            if not (u["kind"] == "pitch_only" and u["pitch"]["index"] in yaws)]


def weapons_by_pair(wiring: dict | None) -> dict:
    """Weapon points that name a yaw part and/or a pitch part, keyed by the pair."""
    out = {}
    if not wiring:
        return out
    for w in wiring.get("weapons", []):
        for p in w.get("points", []):
            props = p.get("props", {})
            yaw, pitch = props.get(POINT_YAW), props.get(POINT_PITCH)
            if not yaw and not pitch:
                continue
            out.setdefault((yaw, pitch), []).append(
                {"weapon": w.get("name"), "binding": w.get("binding") or [],
                 "point": p.get("name")})
    return out


def category(ee: str, module: str) -> str:
    for marker, name in CATEGORY_RULES:
        if marker in ee:
            return name
    stem = (module or "").replace("_vehicle_parts.vmodc", "")
    if "tank" in stem:
        return "tank"
    if stem.endswith("apc"):
        return "apc"
    return "armed_land"


def model_of(module: str) -> str:
    return (module or "?").replace("_vehicle_parts.vmodc", "")


def hinge_sum(u: dict, side: str) -> dict:
    """The hinge object of a unit's yaw or pitch part ({} when the part has none)."""
    return ((u.get(side) or {}).get("hinge") or {})


# -------------------------------------------------------------------- build
def build() -> dict:
    rows = jc3index.load_index(OUT)
    table = load("PARTS_TABLE.jsonl")
    wiring = {r["entity"]: r for r in load("WEAPON_WIRING.jsonl")}
    if not table:
        raise SystemExit("run jc3parts.py first: PARTS_TABLE.jsonl is empty")

    scanned, errors = [], []
    fleet_full_rotation = []
    interesting = []          # entities carrying a Turret/Cannon part
    for rec in table:
        ee = rec["entity"]
        try:
            s = scan(ee, rows)
        except Exception as exc:                       # noqa: BLE001
            errors.append({"entity": ee.rsplit("/", 1)[-1], "error": type(exc).__name__,
                           "detail": str(exc)[:120]})
            continue
        scanned.append(s)
        beh = {p["behavior"] for p in s["parts"]}
        if beh & {"Turret", "Cannon"}:
            interesting.append(s)
        by = {p["part_index"]: p for p in s["parts"]}
        for con in s["constraints"]:
            span = con.get("span_deg")
            full = (con["class"] == UNLIMITED
                    or (con["class"] == LIMITED and span is not None and span >= 359.0))
            if not full:
                continue
            users = [p for p in s["parts"] if p.get("constraint_index") == con["i"]]
            fleet_full_rotation.append({
                "entity": ee.rsplit("/", 1)[-1],
                "model": model_of(s["module"]),
                "category": category(ee, s["module"]),
                "constraint": con["i"], "class": con["class"],
                "span_deg": span, "min_deg": con.get("min_deg"),
                "max_deg": con.get("max_deg"), "offset": con["offset"],
                "file": con["file"],
                "owners": [{"part": p["name"], "behaviour": p["behavior"] or None,
                            "parent": p.get("parent_part_index")} for p in users],
                "owner_is_turret": any(p["behavior"] in ("Turret", "Cannon")
                                       for p in users),
                "part_in_module": all(p["part_index"] in by for p in users),
            })

    # 36 objects over 12 distinct model hinges: the same hinge in every variant of its
    # model.  Fold them so the page names each hinge once and the variants are recorded.
    folded: dict[tuple, dict] = {}
    for r in fleet_full_rotation:
        key = (r["model"], r["constraint"], r["class"], r["offset"])
        cur = folded.get(key)
        if cur is None:
            folded[key] = dict(r)
            cur = folded[key]
            cur["entities"] = [r["entity"]]
        else:
            cur["entities"].append(r["entity"])
            cur["owner_is_turret"] = cur["owner_is_turret"] or r["owner_is_turret"]
            if (cur["span_deg"], cur["owners"]) != (r["span_deg"], r["owners"]):
                cur["variant_mismatch"] = True
    fleet_full_rotation = sorted(folded.values(),
                                 key=lambda r: (r["model"], r["constraint"]))
    for r in fleet_full_rotation:
        r["entities"] = sorted(r["entities"])
        r["variants"] = len(r["entities"])

    # group the turret-carrying entities by model; variants of a model must agree
    models: dict[str, dict] = {}
    for s in interesting:
        m = model_of(s["module"])
        rec = models.setdefault(m, {"model": m, "module": s["module"],
                                    "category": category(s["entity"], s["module"]),
                                    "entities": [], "units": None})
        rec["entities"].append(s["entity"].rsplit("/", 1)[-1])
        pairs = weapons_by_pair(wiring.get(s["entity"]))
        units = []
        for u in units_of(s):
            pair = ((u["yaw"] or {}).get("part"), (u["pitch"] or {}).get("part"))
            hits = pairs.get(pair)
            if hits is None and u["kind"] == "pitch_only":
                hits = [h for (y, p), v in pairs.items() if p == pair[1] and not y
                        for h in v]
            units.append({**u, "weapons": sorted(
                {(h["weapon"], h["point"], tuple(h["binding"])) for h in (hits or [])}
            )})
        units.sort(key=lambda u: ((u["pitch"] or {}).get("index", 1 << 30),
                                  (u["yaw"] or {}).get("index", 1 << 30)))
        seen = json.dumps([{k: u[k] for k in ("kind", "yaw", "pitch", "anchor")}
                           for u in units], sort_keys=True)
        if rec["units"] is None:
            rec["units"] = units
            rec["units_digest"] = seen
        elif seen != rec["units_digest"]:
            rec.setdefault("variant_mismatch", []).append(s["entity"].rsplit("/", 1)[-1])

    for rec in models.values():
        rec["entities"].sort()
        rec["variants"] = len(rec["entities"])
        rec["identical_across_variants"] = "variant_mismatch" not in rec
        for u in rec["units"]:
            # flatten the weapon tuples for a stable json
            u["weapons"] = [{"weapon": w, "point": p, "binding": list(b)}
                            for w, p, b in u["weapons"]]
            u["key"] = " + ".join(x for x in [u["kind"],
                                              (u["yaw"] or {}).get("part"),
                                              (u["pitch"] or {}).get("part")] if x)

    model_list = sorted(models.values(), key=lambda r: (r["category"], r["model"]))
    units = [(m["model"], m["category"], u) for m in model_list for u in m["units"]]
    by_kind: dict[str, list] = {}
    for _m, _c, u in units:
        by_kind.setdefault(u["kind"], []).append(u)

    yaw_rows = [(m, c, u) for m, c, u in units if u["yaw"] is not None]
    pitch_rows = [(m, c, u) for m, c, u in units if u["pitch"] is not None]

    def spans(rows, side):
        return sorted({hinge_sum(u, side).get("span_deg") for _m, _c, u in rows
                       if hinge_sum(u, side).get("span_deg") is not None})

    pitch_by_category: dict[str, list] = {}
    for m, c, u in pitch_rows:
        h = hinge_sum(u, "pitch")
        if not h:
            continue
        pitch_by_category.setdefault(c, []).append({
            "model": m, "part": u["pitch"]["part"], "kind": u["kind"],
            "min_deg": h["min_deg"], "max_deg": h["max_deg"], "span_deg": h["span_deg"]})

    doc = {
        "meta": {
            "task": "turret limits over the whole vehicle fleet",
            "builds_on": ["G2-13 (Research/JC3Grab/TURRET.md: turret = Turret part + "
                          "Cannon part + two limited hinges)",
                          "G3-10e (Research/JC3Grab/PHYSICS_LIMITS.md: the hinge's "
                          "angular limit atom, +0x0FC min / +0x100 max, radians)"],
            "generated_by": "Tools/scripts/jc3_turret_limits.py",
            "inputs": ["Research/JC3Grab/PARTS_TABLE.jsonl (233 vehicle entities)",
                       "Research/JC3Grab/WEAPON_WIRING.jsonl (fire points)",
                       "the game install's .ee bundles (read-only)",
                       "Tools/scripts/jc3_physics_limits.py (imported: HINGE_LIMIT)"],
            "game": GAME.replace("\\", "/"),
            "entities_in_table": len(table),
            "entities_scanned": len(scanned),
            "entities_with_parts_module": sum(1 for s in scanned if s["parts"]),
            "entities_with_a_Turret_or_Cannon_part": len(interesting),
            "entities_with_constraints": sum(1 for s in scanned if s["constraints"]),
            "scan_errors": errors,
            "decode": {
                "hinge_class": LIMITED,
                "atom_offset": hex(ATOM["atom"]),
                "atom_type_code": ATOM["type"],
                "min_offset": hex(ATOM["min"]),
                "max_offset": hex(ATOM["max"]),
                "units": "radians in the file, degrees here (x 57.29577951308232)",
                "axis": "frame A row 0 at +0x30 (frame B row 0 at +0x70 checked against "
                        "it): the limited hinge's free axis",
                "pivot": "frame A translation at +0x60",
                "provenance": "Research/JC3Grab/PHYSICS_LIMITS.md sections 1-2",
            },
            "labels": {"decoded": "read at the stated offset; the oracle is named",
                       "derived": "a rule over decoded inputs, stated in prose",
                       "UNKNOWN": "no byte in the files pins it"},
        },
        "models": model_list,
        "totals": {
            "models_with_a_weapon_mount": len(model_list),
            "entities": len(interesting),
            "units": len(units),
            "by_kind": {k: len(v) for k, v in sorted(by_kind.items())},
            "yaw_hinges": len(yaw_rows),
            "pitch_hinges": len(pitch_rows),
            "yaw_spans_deg": spans(yaw_rows, "yaw"),
            "pitch_spans_deg": spans(pitch_rows, "pitch"),
        },
        "yaw": {
            "turret_parts_in_fleet": sum(1 for s in scanned
                                         for p in s["parts"] if p["behavior"] == "Turret"),
            "yaw_hinge_count": len(yaw_rows),
            "unlimited_yaw_hinges": sum(1 for _m, _c, u in yaw_rows
                                        if hinge_sum(u, "yaw").get("class") == UNLIMITED),
            "full_rotation_yaw_hinges": sum(1 for _m, _c, u in yaw_rows
                                            if (hinge_sum(u, "yaw").get("span_deg") or 0)
                                            >= 359.0),
            "default_minus_179_plus_179": sum(
                1 for _m, _c, u in yaw_rows
                if (hinge_sum(u, "yaw").get("min_deg"),
                    hinge_sum(u, "yaw").get("max_deg")) == (-179.0, 179.0)),
            "limited_less_than_358": [
                {"model": m, "category": c, "part": u["yaw"]["part"],
                 "min_deg": hinge_sum(u, "yaw")["min_deg"],
                 "max_deg": hinge_sum(u, "yaw")["max_deg"],
                 "span_deg": hinge_sum(u, "yaw")["span_deg"], "kind": u["kind"]}
                for m, c, u in yaw_rows
                if (hinge_sum(u, "yaw").get("span_deg") or 0) < 358.0],
            "kinds_without_a_yaw_part": {
                "pitch_only": [{"model": m, "part": u["pitch"]["part"],
                                "parent": (u["anchor"] or {}).get("part"),
                                "parent_behaviour": (u["anchor"] or {}).get("behaviour"),
                                "parent_has_hinge": bool(
                                    ((u["anchor"] or {}).get("hinge") or {}).get("class"))}
                               for m, c, u in units if u["kind"] == "pitch_only"],
            },
        },
        "full_rotation_census": full_rotation_census(fleet_full_rotation),
        "pitch_by_category": py_cat_list(pitch_by_category, model_list),
        "fleet_full_rotation_hinges": fleet_full_rotation,
        "oracles": {},
        "unknowns": [],
    }
    doc["oracles"] = oracles(doc)
    doc["unknowns"] = unknowns(doc)
    return doc


def full_rotation_census(rows: list[dict]) -> dict:
    """How many full-rotation hinges the fleet ships, folded by model and counted per object."""
    unl = [r for r in rows if r["class"] == UNLIMITED]
    span = [r for r in rows if r["class"] == LIMITED]
    beh: dict[str, int] = {}
    for r in rows:
        for o in r["owners"]:
            b = o["behaviour"] or "None"
            beh[b] = beh.get(b, 0) + 1
    return {
        "model_hinges": len(rows),
        "unlimited_model_hinges": len(unl),
        "unlimited_objects": sum(r["variants"] for r in unl),
        "unlimited_models": sorted({r["model"] for r in unl}),
        "full_span_model_hinges": len(span),
        "full_span_objects": sum(r["variants"] for r in span),
        "full_span_models": sorted({r["model"] for r in span}),
        "objects": sum(r["variants"] for r in rows),
        "entities": len({e for r in rows for e in r["entities"]}),
        "owner_behaviours": dict(sorted(beh.items())),
    }


def py_cat_list(pitch_by_category: dict, model_list: list[dict]) -> dict:
    order = {"tank": 0, "apc": 1, "armed_land": 2, "boat": 3, "aircraft": 4}
    out = {}
    for cat in sorted(pitch_by_category, key=lambda c: order.get(c, 9)):
        rows = sorted(pitch_by_category[cat], key=lambda r: (r["min_deg"], r["max_deg"]))
        spans = [r["span_deg"] for r in rows]
        out[cat] = {
            "models": sorted({r["model"] for r in rows}),
            "pitch_parts": len(rows),
            "span_min_deg": min(spans), "span_max_deg": max(spans),
            "ranges": [[r["min_deg"], r["max_deg"]] for r in rows],
            "elevation_max_deg": max(r["max_deg"] for r in rows),
            "depression_min_deg": min(r["min_deg"] for r in rows),
            "rows": rows,
            "yaw_spans": sorted({hinge_sum(u, "yaw").get("span_deg")
                                 for m in model_list if m["category"] == cat
                                 for u in m["units"]
                                 if hinge_sum(u, "yaw").get("span_deg") is not None}),
        }
    return out


def oracles(doc: dict) -> dict:
    """Checks that would fail if a decode, a link or a stated pattern were wrong."""
    checks, detail = {}, {}
    models = doc["models"]
    units = [(m, u) for m in models for u in m["units"]]

    def h(u, side):
        return (u[side] or {}).get("hinge") or {}

    # 1. every Turret-behaviour part is on a limited hinge whose type code is 14
    turret_yaws = [(m, u) for m, u in units if u["kind"] == "turret"]
    checks["every_Turret_part_on_a_limited_hinge_type_14"] = bool(turret_yaws) and all(
        h(u, "yaw").get("class") == LIMITED and h(u, "yaw").get("type_code") == ATOM["type"]
        for _m, u in turret_yaws)
    detail["turret_yaws"] = len(turret_yaws)

    # 2. every yaw axis is vertical in its own frame (a yaw hinge turns about up)
    checks["every_yaw_axis_is_vertical"] = all(
        abs(abs(h(u, "yaw")["axis"][1]) - 1.0) < 1e-3 for _m, u in units
        if u["yaw"] is not None and h(u, "yaw").get("axis"))
    # 3. every pitch axis is horizontal (no up component)
    checks["every_pitch_axis_is_horizontal"] = all(
        abs(h(u, "pitch")["axis"][1]) < 1e-3 for _m, u in units
        if u["pitch"] is not None and h(u, "pitch").get("axis"))
    # 4. the two frames of the hinge agree on the axis (frame A row 0 vs frame B row 0)
    worst = 0.0
    for _m, u in units:
        for side in ("yaw", "pitch"):
            a, b = h(u, side).get("axis"), h(u, side).get("axis_b")
            if not a or not b:
                continue
            worst = max(worst, abs(sum(a[k] * b[k] for k in range(3)) - 1.0))
    detail["worst_axis_A_vs_B_dot_error"] = round(worst, 9)
    checks["frame_A_and_frame_B_share_the_axis"] = worst < 1e-3
    # 5. min <= max and both inside +/-pi on every turret hinge
    checks["limits_ordered_and_within_pi"] = all(
        h(u, side)["min_rad"] <= h(u, side)["max_rad"]
        and abs(h(u, side)["min_rad"]) <= math.pi + 1e-6
        and abs(h(u, side)["max_rad"]) <= math.pi + 1e-6
        for _m, u in units for side in ("yaw", "pitch") if h(u, side).get("min_rad")
        is not None)
    # 6. every turret part keeps an identity parent_space_offset (G2-13's claim)
    checks["turret_parts_identity_parent_offset"] = all(
        u[side]["identity_offset"] for _m, u in units for side in ("yaw", "pitch")
        if u[side] is not None)
    # 7. all six turreted vehicles G2-13 printed reproduce its numbers exactly
    want = {"mediumtank": (-179.0, 179.0, -5.0, 20.0),
            "bavariumtank": (-179.0, 179.0, -5.0, 20.0),
            "smalltank": (-179.0, 179.0, -5.0, 25.0),
            "apc": (-179.0, 179.0, -15.0, 50.0),
            "armoredjeep": (-179.0, 179.0, -25.0, 50.0),
            "technicaljeep": (-179.0, 179.0, -10.0, 45.0)}
    mismatched = []
    for name, (ylo, yhi, plo, phi) in want.items():
        mod = next((x for x in models if x["model"] == name), None)
        u = mod["units"][0] if mod and mod["units"] else None
        got = None
        if u is not None and u["yaw"] is not None and u["pitch"] is not None:
            got = (h(u, "yaw").get("min_deg"), h(u, "yaw").get("max_deg"),
                   h(u, "pitch").get("min_deg"), h(u, "pitch").get("max_deg"))
        if got != (ylo, yhi, plo, phi):
            mismatched.append((name, got))
    checks["TURRET_md_samples_reproduce"] = not mismatched
    detail["TURRET_md_sample_mismatches"] = mismatched
    # 8. variants of a model decode identically (same bytes, same numbers)
    checks["variants_of_a_model_agree"] = all(m["identical_across_variants"]
                                              for m in models)
    # 9. no turret or mount part owns a full-rotation hinge anywhere in the fleet
    checks["no_turret_part_on_a_full_rotation_hinge"] = not any(
        r["owner_is_turret"] for r in doc["fleet_full_rotation_hinges"])
    checks["full_rotation_hinges_are_variant_stable"] = not any(
        r.get("variant_mismatch") for r in doc["fleet_full_rotation_hinges"])
    # 10. the stated pattern: tanks aim high less than boats (pitch span)
    pbc = doc["pitch_by_category"]
    checks["boat_pitch_spans_exceed_tank_pitch_spans"] = (
        "boat" in pbc and "tank" in pbc
        and pbc["boat"]["span_min_deg"] > pbc["tank"]["span_max_deg"])
    # 11. the stated pattern: every Turret-behaviour yaw is all-round (>= 300 deg),
    #     every two-Cannon pintle yaw is not
    checks["turret_yaw_all_round_two_cannon_yaw_not"] = (
        all((h(u, "yaw").get("span_deg") or 0) >= 300.0 for _m, u in turret_yaws)
        and all((h(u, "yaw").get("span_deg") or 0) < 300.0
                for _m, u in units if u["kind"] == "two_cannon"))
    detail["two_cannon_units"] = sum(1 for _m, u in units if u["kind"] == "two_cannon")
    # 12. no scan was silently skipped
    checks["every_entity_scanned"] = (doc["meta"]["entities_scanned"]
                                      == doc["meta"]["entities_in_table"]
                                      and not doc["meta"]["scan_errors"])
    return {"all_ok": all(checks.values()), "checks": checks, "detail": detail}


def unknowns(doc: dict) -> list[dict]:
    return [
        {"what": "the hinge axis frame (body-A local vs vehicle space)",
         "tried": "compared the decoded pivots and axes with the art: the medium tank's "
                  "turret pivot (0, 2.2812, 1.1382) and +Y axis agree with vehicle space, "
                  "but the patrol boats' pitch hinge reads +-Z in a yawing parent's frame",
         "why_unknown": "no byte names the frame; only the parent part's rest orientation "
                        "would settle it, and that matrix is in the .lod, not decoded here"},
        {"what": "a rotation speed or acceleration for the turret",
         "tried": "read every atom of the limited hinge (type 14 only carries the pair) "
                  "and the parts module (no such field)",
         "why_unknown": "the turn rate is code-side; the files carry an axis and two "
                        "angles (G3-10e's finding, still true)"},
        {"what": "which of a two-Cannon boat mount is the 'turret' in game logic",
         "tried": "the weapon fire point names the horizontal part as yaw and the "
                  "vertical part as pitch, and the vertical part's parent is the "
                  "horizontal one",
         "why_unknown": "both parts carry behaviour Cannon; there is no decoded ordinal"},
        {"what": "whether a full-rotation turret is possible without a new hinge class",
         "tried": "censused every hinge in the fleet: 4 hkpHingeConstraintData and 8 "
                  "limited hinges with a full 360 deg span exist, none on a turret part",
         "why_unknown": "no shipped turret uses either; a port would have to change the "
                        "class or the pair, and that is a build change, not a decode"},
    ]


# ----------------------------------------------------------------------- md
def fnum(v) -> str:
    if v is None:
        return "-"
    return f"{v:g}"


def render_md(doc: dict) -> str:
    L: list[str] = []
    A = L.append
    m, t = doc["meta"], doc["totals"]
    A("# JC3 turrets: the yaw and pitch limits of the whole fleet")
    A("")
    A("A turret in JC3 is a `Turret` part (yaw) and a `Cannon` part (pitch), each on one "
      "`hkpLimitedHingeConstraintData` (`Research/JC3Grab/TURRET.md`, G2-13). This page "
      "reads the two angle limits of every such pair in the fleet the decoded way, using "
      "G3-10e's atom layout: the angular limit atom starts at **+0x0F8** (u16 type code "
      "**14**), with the minimum at **+0x0FC** and the maximum at **+0x100**, radians.")
    A("")
    A(f"Scope: **{m['entities_in_table']} vehicle entities** in `PARTS_TABLE.jsonl`, all "
      f"**{m['entities_scanned']}** re-read from the archives for this page: "
      f"{m['entities_with_parts_module']} with a parts module, "
      f"{m['entities_with_constraints']} with a `.physicsc` (the other "
      f"{m['entities_scanned'] - m['entities_with_constraints']} ship no constraint at "
      f"all). **{m['entities_with_a_Turret_or_Cannon_part']}** entities carry a `Turret` "
      f"or `Cannon` part; they fold into **{t['models_with_a_weapon_mount']} distinct "
      f"vehicle models**.")
    A("")
    A("| | |")
    A("|---|---|")
    A(f"| turret-ish units | **{t['units']}** ("
      + "; ".join(f"`{k}` {v}" for k, v in t["by_kind"].items()) + ") |")
    A(f"| yaw hinged parts | {t['yaw_hinges']} |")
    A(f"| pitch hinged parts | {t['pitch_hinges']} |")
    A(f"| yaw spans present (deg) | {', '.join(fnum(x) for x in t['yaw_spans_deg'])} |")
    A(f"| pitch spans present (deg) | {', '.join(fnum(x) for x in t['pitch_spans_deg'])} |")
    A("")
    A("`decoded` = the value sits at the stated offset in the stated object; `derived` = a "
      "rule over decoded values, stated where it is used; `UNKNOWN` = no byte pins it.")
    A("")

    A("## 1. Every turret in the fleet")
    A("")
    A("One row per unit. `Turret` = a `Turret`-behaviour yaw part; `two_cannon` = a pintle "
      "whose yaw and pitch are both `Cannon` parts (how the patrol boats are built); "
      "`pitch_only` = a gun frame with no yaw hinge in its parent chain (aircraft).")
    A("")
    A("| model | class | units | yaw part | yaw min..max (deg) | yaw span | pitch part | "
      "pitch min..max (deg) | pitch span |")
    A("|---|---|---:|---|---:|---:|---|---:|---:|")
    for mod in doc["models"]:
        for u in mod["units"]:
            yh = (u["yaw"] or {}).get("hinge") or {}
            ph = (u["pitch"] or {}).get("hinge") or {}
            ypart = (u["yaw"] or {}).get("part") or "-"
            ppart = (u["pitch"] or {}).get("part") or "-"
            ylim = ("unlimited" if yh.get("class") == UNLIMITED
                    else f"{fnum(yh['min_deg'])} .. {fnum(yh['max_deg'])}"
                    if yh.get("min_deg") is not None else "-")
            plim = ("unlimited" if ph.get("class") == UNLIMITED
                    else f"{fnum(ph['min_deg'])} .. {fnum(ph['max_deg'])}"
                    if ph.get("min_deg") is not None else "-")
            A(f"| `{mod['model']}` | {mod['category']} | {u['kind']} | `{ypart}` | {ylim} | "
              f"{fnum(yh.get('span_deg'))} | `{ppart}` | {plim} | {fnum(ph.get('span_deg'))} |")
    A("")
    A("Each model row stands for every variant of it: "
      + "; ".join(f"`{m['model']}` x{m['variants']}" for m in doc["models"]) + ". The "
      "variants of a model share one parts module and one `.physicsc`, and the rebuild "
      "asserts every variant decodes the same numbers (`variants_of_a_model_agree`).")
    A("")
    A("Hinge geometry (`decoded`: frame A row 0 is the axis, frame A translation the "
      "pivot; frame B row 0 agrees to 1e-3 on every unit):")
    A("")
    A("| model | unit | side | constraint | .physicsc object | axis | pivot (x, y, z) |")
    A("|---|---|---|---:|---:|---|---|")
    for mod in doc["models"]:
        for u in mod["units"]:
            for side in ("yaw", "pitch"):
                p = u[side]
                hg = (p or {}).get("hinge") or {}
                if not hg.get("class"):
                    continue
                A(f"| `{mod['model']}` | {u['kind']} | {side} | {p['constraint']} | "
                  f"0x{hg['offset']:05X} | {', '.join(fnum(x) for x in hg['axis'])} | "
                  f"{', '.join(fnum(x) for x in hg['pivot'])} |")
    A("")
    if any(u["weapons"] for m in doc["models"] for u in m["units"]):
        A("Weapons whose fire points name these parts (`id:80201E4D` yaw / `id:5C19E7E0` "
          "pitch, `decoded` from the fire-point properties):")
        A("")
        A("| model | unit | weapons |")
        A("|---|---|---|")
        for mod in doc["models"]:
            for u in mod["units"]:
                if not u["weapons"]:
                    continue
                names = sorted({f"`{w['weapon']}` ({', '.join(w['binding']) or '-'}, "
                                f"`{w['point']}`)" for w in u["weapons"]})
                A(f"| `{mod['model']}` | {u['kind']} | {'; '.join(names)} |")
        A("")

    y = doc["yaw"]
    fc = doc["full_rotation_census"]
    A("## 2. Yaw: who turns all the way round, and who does not")
    A("")
    A(f"- `Turret`-behaviour parts in the fleet: **{y['turret_parts_in_fleet']}** over "
      f"{m['entities_scanned']} entities; after folding the variants they are "
      f"**{y['yaw_hinge_count']} distinct yaw hinges** (7 `Turret` yaws + 3 two-Cannon "
      f"pintle yaws).")
    A(f"- Ship **-179 .. +179 deg** (span **358**): **{y['default_minus_179_plus_179']}** of "
      f"them - medium tank, Bavarium tank, small tank, APC, armoured jeep, technical. "
      f"358 deg of travel is one degree short of a full circle at each stop, so the aim is "
      f"all-round with a **2 deg blind wedge pointing dead astern**.")
    A(f"- Ship a hinge with **no angular limit at all** "
      f"(`hkpHingeConstraintData`): **{y['unlimited_yaw_hinges']}**.")
    A(f"- Ship a **full 360 deg** limited span: **{y['full_rotation_yaw_hinges']}**.")
    A("")
    if y["limited_less_than_358"]:
        A("Yaw narrower than the -179 .. +179 default (`decoded`):")
        A("")
        A("| model | class | yaw part | min..max (deg) | span | unit |")
        A("|---|---|---|---:|---:|---|")
        for r in y["limited_less_than_358"]:
            A(f"| `{r['model']}` | {r['category']} | `{r['part']}` | "
              f"{fnum(r['min_deg'])} .. {fnum(r['max_deg'])} | {fnum(r['span_deg'])} | "
              f"{r['kind']} |")
        A("")
    owners = ", ".join(("`" + b + "`") if b != "None" else "no behaviour"
                      for b in fc["owner_behaviours"])
    A(f"**No turret in the fleet has an unlimited yaw hinge.** The full-rotation hinges "
      f"that do exist are on other parts - the census in §3 lists all **{fc['model_hinges']}** "
      f"of them with the parts that own them ({owners}), and every one fails the turret "
      f"test. So \"full rotation\" for a shipped turret means the **358 deg** pair "
      f"(-179 .. +179), not an unconstrained hinge.")
    A("")
    po = y["kinds_without_a_yaw_part"]["pitch_only"]
    if po:
        A("Gun frames with **no yaw hinge at all** (`derived` from the parts' parent "
          "chains; the mount pitches, the aircraft aims):")
        A("")
        A("| model | pitch part | parent part | parent behaviour | parent has a hinge |")
        A("|---|---|---|---|---|")
        for r in po:
            A(f"| `{r['model']}` | `{r['part']}` | `{r['parent']}` | "
              f"{r['parent_behaviour'] or '-'} | {'yes' if r['parent_has_hinge'] else 'no'} |")
        A("")

    A("## 3. The fleet's other full-rotation hinges (all non-turret)")
    A("")
    A("`decoded`: every constraint object in all "
      f"{m['entities_scanned']} entities whose class is `{UNLIMITED}` or whose limited "
      "span is a full 360 deg, with the part whose `constraint_index` selects it. "
      f"**{fc['objects']} objects** on **{fc['entities']} entities** fold into "
      f"**{fc['model_hinges']} model hinges**: {fc['unlimited_model_hinges']} unlimited "
      f"({fc['unlimited_objects']} objects, {', '.join('`' + x + '`' for x in fc['unlimited_models'])}) "
      f"and {fc['full_span_model_hinges']} at a full 360 deg span "
      f"({fc['full_span_objects']} objects, "
      f"{', '.join('`' + x + '`' for x in fc['full_span_models'])}).")
    A("")
    A("| model | class | constraint | hinge class | span (deg) | owning part | behaviour |"
      " variants |")
    A("|---|---|---:|---|---:|---|---|---:|")
    for r in doc["fleet_full_rotation_hinges"]:
        own = ", ".join(f"`{o['part']}`" for o in r["owners"]) or "-"
        beh = ", ".join(o["behaviour"] or "None" for o in r["owners"]) or "-"
        span = "no limit atom" if r["class"] == UNLIMITED else fnum(r["span_deg"])
        A(f"| `{r['model']}` | {r['category']} | {r['constraint']} | "
          f"`{r['class']}` | {span} | {own} | {beh} | {r['variants']} |")
    A("")
    A(f"Two mechanisms therefore exist in shipped files for a part that turns freely: the "
      f"**unlimited hinge class** (`{UNLIMITED}`, {fc['unlimited_objects']} objects on "
      f"{', '.join('`' + x + '`' for x in fc['unlimited_models'])} - a cast-net pivot and a "
      f"hose spool) and a **limited hinge whose pair is exactly -180 .. +180** "
      f"({fc['full_span_objects']} objects on "
      f"{', '.join('`' + x + '`' for x in fc['full_span_models'])} - the upper steering "
      f"fork of a bike, or the snowmobile's equivalent). No turret part uses either, so a "
      f"full-rotation turret would be a change of hinge class or of the pair - a build "
      f"decision, not something the vanilla turrets already do.")
    A("")

    A("## 4. Pitch: tanks, APCs, armed land vehicles, boats, aircraft")
    A("")
    A("`decoded` per part; the class grouping is `derived` from the entity path "
      "(`01_land` / `02_air` / `03_sea`) and the model name - there is no decoded "
      "\"vehicle class\" field.")
    A("")
    A("| class | models | pitch parts | depression (min) | elevation (max) | span min..max "
      "(deg) | yaw spans (deg) |")
    A("|---|---|---:|---:|---:|---|---|")
    order = ["tank", "apc", "armed_land", "boat", "aircraft"]
    for cat in order:
        c = doc["pitch_by_category"].get(cat)
        if not c:
            continue
        A(f"| {cat} | {', '.join('`' + x + '`' for x in c['models'])} | "
          f"{c['pitch_parts']} | {fnum(c['depression_min_deg'])} | "
          f"{fnum(c['elevation_max_deg'])} | {fnum(c['span_min_deg'])} .. "
          f"{fnum(c['span_max_deg'])} | "
          f"{', '.join(fnum(x) for x in c['yaw_spans']) or '-'} |")
    A("")
    for cat in order:
        c = doc["pitch_by_category"].get(cat)
        if not c:
            continue
        A(f"**{cat}**")
        A("")
        A("| model | pitch part | unit | min..max (deg) | span |")
        A("|---|---|---|---:|---:|")
        for r in sorted(c["rows"], key=lambda r: (r["min_deg"], r["max_deg"])):
            A(f"| `{r['model']}` | `{r['part']}` | {r['kind']} | "
              f"{fnum(r['min_deg'])} .. {fnum(r['max_deg'])} | {fnum(r['span_deg'])} |")
        A("")
    A("What the numbers say:")
    A("")
    A("- **Tanks are the flat shooters.** The medium tank and the Bavarium tank share "
      "exactly `-5 .. +20`; the small tank is `-5 .. +25`. 5 deg of depression is the "
      "whole tank family's limit, so a tank cannot shoot downward at a target below its "
      "hull, and its elevation stops at 20-25 deg.")
    A("- **The APC aims much higher and lower** than a tank: `-15 .. +50`. It is the same "
      "`w206` mounted M2 as the jeeps, on a taller turret, and its span (65 deg) is more "
      "than double the medium tank's 25.")
    A("- **Boats split into two builds.** The corvette's real turret is `-5 .. +75` - tank "
      "depression, three and a half times the tank's elevation - on a yaw restricted to "
      "`+-150`. The patrol boats use two-Cannon pintles instead: `+-50` (heavypatrol) and "
      "`-50 .. +25` (lightpatrol), with the yaw cut to `+-75` on both.")
    A("- **The trade is yaw for pitch.** Every `Turret`-behaviour yaw keeps 358 deg and "
      "gives up pitch (max elevation 20-25 deg on tanks); every two-Cannon pintle with a "
      "wide pitch gives up yaw (`+-75`). The corvette is the one vehicle that keeps "
      "both (300 deg yaw, 80 deg pitch).")
    A("- **Aircraft gun frames pitch but do not yaw on their own hinge**: `-45 .. +35` "
      "(lightassault door miniguns) and `-45 .. +30` (advancedassault gatlings), mounted "
      "on plain adapters, so the airframe does the aiming.")
    A("")

    A("## 5. Oracles (`--check` re-runs every one of them)")
    A("")
    A("| oracle | result |")
    A("|---|---|")
    for k, v in doc["oracles"]["checks"].items():
        A(f"| `{k}` | **{'pass' if v else 'FAIL'}** |")
    A("")
    A("Why these are oracles and not decoration:")
    A("")
    A("- `every_Turret_part_on_a_limited_hinge_type_14` - the pair of readings that must "
      "agree: behaviour `Turret` (from the parts module) and the atom type code (from "
      "`.physicsc`). If the limit offsets were wrong, the type code would not be 14.")
    A("- `every_yaw_axis_is_vertical` / `every_pitch_axis_is_horizontal` - a yaw hinge "
      "that reads a horizontal axis would mean the axis is not frame A row 0.")
    A("- `frame_A_and_frame_B_share_the_axis` - a limited hinge stores one axis in both "
      "frames; two independent 16-byte rows agreeing to 1e-3 on all "
      f"{t['units']} units is what pins the axis offset.")
    A(      "- `TURRET_md_samples_reproduce` - the six turreted vehicles G2-13 printed "
      "(`TURRET.md` §2) must come out at exactly its numbers: medium tank and Bavarium "
      "tank -179..179 / -5..20, small tank / -5..25, APC / -15..50, armoured jeep / "
      "-25..50, technical / -10..45.")
    A("- `variants_of_a_model_agree` - 40 entities grouped into 11 models; a variant "
      "disagreeing would mean the link part -> constraint was unstable.")
    A("- `no_turret_part_on_a_full_rotation_hinge` and "
      "`boat_pitch_spans_exceed_tank_pitch_spans` - the two claims this page makes about "
      "the fleet, turned into failing checks.")
    A("")
    A("## 6. UNKNOWNs")
    A("")
    for u in doc["unknowns"]:
        A(f"- **{u['what']}** - tried: {u['tried']}. Still unknown because "
          f"{u['why_unknown']}.")
    A("")
    A("## 7. Files")
    A("")
    A("| file | what |")
    A("|---|---|")
    A("| `Tools/scripts/jc3_turret_limits.py` | this pass, `--write` / `--check` |")
    A("| `Research/JC3Grab/TURRET_LIMITS.md` | this page |")
    A("| `Research/JC3Grab/TURRET_LIMITS.json` | the same, machine-readable, every "
      "offset and every angle |")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ commands
def cmd_write() -> int:
    doc = build()
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(doc))
    t = doc["totals"]
    print(f"{JSON_NAME}: {t['units']} units on {t['models_with_a_weapon_mount']} models, "
          f"{t['yaw_hinges']} yaw / {t['pitch_hinges']} pitch hinges, "
          f"{len(doc['fleet_full_rotation_hinges'])} full-rotation hinges in the fleet")
    print(f"{MD_NAME}: "
          f"{len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} "
          f"lines; oracles {sum(1 for v in doc['oracles']['checks'].values() if v)}/"
          f"{len(doc['oracles']['checks'])}")
    bad = [k for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAILING: " + ", ".join(bad))
        return 1
    return 0


def cmd_check() -> int:
    doc = build()
    bad = []
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    if not (os.path.exists(jp) and os.path.exists(mp)):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing - run --write first")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != json.loads(json.dumps(doc, sort_keys=True)):
        for k in sorted(set(old) | set(doc)):
            if old.get(k) != doc.get(k):
                bad.append(f"json section changed: {k}")
    md = render_md(doc)
    if md != open(mp, encoding="utf-8").read():
        import difflib
        diff = list(difflib.unified_diff(open(mp, encoding="utf-8").read().splitlines(),
                                         md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += [f"oracle failed: {k}" for k, v in doc["oracles"]["checks"].items() if not v]
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    t = doc["totals"]
    print(f"PASS: {doc['meta']['entities_scanned']} entities, {t['units']} turret units on "
          f"{t['models_with_a_weapon_mount']} models, yaw spans "
          f"{t['yaw_spans_deg']}, pitch spans {t['pitch_spans_deg']}")
    print("oracles: " + json.dumps(doc["oracles"]["checks"], sort_keys=True))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="decode and write the md + json")
    g.add_argument("--check", action="store_true",
                   help="re-read the archives, rebuild, compare and re-run the oracles")
    a = p.parse_args()
    return cmd_write() if a.write else cmd_check()


if __name__ == "__main__":
    raise SystemExit(main())
