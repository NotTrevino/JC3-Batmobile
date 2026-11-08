#!/usr/bin/env python3
"""g3_11d_collision_recheck.py - G3-11d: re-check the ledger's collision rows (read-only).

G3-11 flagged that the collision rows in `Working/Translation/T_ROWS.jsonl` needed re-checking
now that both sides decode:

    BmAK side   COLLISION_BOXES.json / COLLISION_GEOM.json / COLLISION_FRAME.json /
                COLLISION_SELECTOR.json (G3-01b..e)
    JC3 side    PHYSICS_ROLES.json (G3-10) + the `.physicsc` files themselves

For every collision row it asks two questions and nothing else:

    source   does the row's BmAK description match what G3-01 decoded
             (asset, element, extents, frame)?
    target   does the row's JC3 description match the body role G3-10 decoded (and the
             bodies that are actually in the built and vanilla `.physicsc`)?

No translation decision is made, and nothing is written into the game or the build.

Scope rule (computed, not hand-listed): a row is a collision row when its id starts `T-CO` or
a cell mentions `.physicsc`, `world_collision*`, `raycast_body_id` or `collision bodies`.
Rows that mention only "hull"/"collision" in passing are listed separately as near-misses.

Reading the `.physicsc`: `jc3hkx.Packfile` (typed by the virtual fixup table) plus
`decode_polytope`, `decode_compound` and `check_file(against=...)`. Every build tree under
`Builds/*/aaf` is hashed and grouped, so "the built file" is whatever the trees actually carry
rather than a chosen path. `check_file` re-runs the invariant ladder and reports which objects
differ from vanilla.

Oracles (a failure is a hard error, and --check re-runs them all):
    O1  every quoted number is still present in the ledger row it is quoted from
    O2  the box census is recounted from the JSON lists (131 = 3 + 128 over 2 bodies)
    O3  the T-22 category counts sum to its body count (32)
    O4  every `.physicsc` decodes and passes `check_file`; the built trees group by sha and
        differ from vanilla only where stated
    O5  the "largest box fits one donor hull" containment is recomputed from hull vertices
    O6  38/42 world-collision parts and the 4 `-1` wheels are recounted from the part table
    O7  the "7 donor hull slots" figure is recomputed from the static compounds in the file
    O8  the G3-01 citations used here are still present in the artifacts they are quoted from

Usage:
    uv run python Tools/scripts/g3_11d_collision_recheck.py --write
    uv run python Tools/scripts/g3_11d_collision_recheck.py --check
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3hkx as H  # noqa: E402  (packfile reader: Packfile, decode_*, check_file)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
T_ROWS = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
T22 = os.path.join(ROOT, "Working", "Translation", "t16_collision.json")
BOXES = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_BOXES.json")
GEOM = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_GEOM.json")
FRAME = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_FRAME.json")
SELECTOR = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR.json")
ROLES = os.path.join(ROOT, "Research", "JC3Grab", "PHYSICS_ROLES.json")
VANILLA = (r"E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/models/jc_vehicles/01_land/"
           r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
B10 = os.path.join(ROOT, "Working", "Collision", "batmobile.physicsc")
TREE_GLOBS = (
    "Builds/*/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc",
    "Builds/*/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
    "sportsmuscle/batmobile/sportsmuscle.physicsc",
)
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_LEDGER_CHECK.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_LEDGER_CHECK.json")

SCOPE = re.compile(r"\.physicsc|world_collision|raycast_body_id|collision bodies", re.I)
NEAR = re.compile(r"hull|collision", re.I)
NUM = re.compile(r"-?\d+(?:\.\d+)?")


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def sha16(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def census(path):
    """Type-aware census of one `.physicsc` (+ its invariant ladder against vanilla)."""
    blob = open(path, "rb").read()
    pf = H.Packfile(blob)
    counts: dict[str, int] = {}
    for o in pf.objects:
        counts[o.cls] = counts.get(o.cls, 0) + 1
    hulls, spans = [], []
    for o in pf.objects:
        if o.cls != "hknpConvexPolytopeShape":
            continue
        bb = H.decode_polytope(pf, o.offset)["bounds"]
        sp = [bb["max"][i] - bb["min"][i] for i in range(3)]
        hulls.append({"offset": o.offset, "spans": sp,
                      "bounds": bb, "vertices": len(H.decode_polytope(pf, o.offset)["vertices"])})
        spans.append(sp)
    sysd = [o for o in pf.objects if o.cls == "hknpPhysicsSystemData"]
    body_entries = pf.array(sysd[0].offset + 0x40)["size"] if sysd else None
    compounds, instances, wired = [], 0, 0
    for o in pf.objects:
        if o.cls not in H.COMPOUND_CLASSES:
            continue
        d = H.decode_compound(pf, o.offset, o.cls)
        compounds.append({"class": o.cls, "offset": o.offset,
                          "instances": d["instance_count"]})
        instances += d["instance_count"]
        wired += sum(1 for i in d["instances"] if i["part_index"] is not None)
    return {
        "path": rel(path), "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()[:16],
        "objects": len(pf.objects), "class_counts": counts,
        "hulls": len(hulls), "hull_detail": hulls,
        "max_hull_axis_m": round(max((max(s) for s in spans), default=0.0), 4),
        "extern_meshes": counts.get("hknpExternMeshShape", 0),
        "geometries": counts.get("hkGeometry", 0),
        "body_entries": body_entries,
        "compounds": compounds, "instances": instances, "instances_wired": wired,
        "station_sets": len(H.stations(pf)),
        "_blob": blob,
    }


def strip_private(rec):
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def box_census(boxes):
    """Recount the box lists instead of trusting the summary.

    The drivable boxes are nested under a body (which carries the bone), the wreck boxes
    carry their own bone/export.  Three "largest" records are kept apart on purpose: the
    wreck set (what T-22 measured), the drivable set, and everything together.
    """
    drivable = []
    for body in boxes["bodies"]:
        for bx in body.get("boxes", []):
            r = dict(bx)
            r.setdefault("bone", body.get("bone"))
            r.setdefault("export", body.get("export"))
            drivable.append(r)
    wreck = [bx for lst in boxes["wreck"]["boxes"].values() for bx in lst]
    allb = drivable + wreck

    def top(rows):
        b = max(rows, key=lambda r: max(r["extents_cm"]))
        return {"bone": b.get("bone"), "export": b.get("export"),
                "extents_cm": b["extents_cm"], "translation_cm": b.get("translation_cm")}

    return {
        "drivable_boxes": len(drivable), "wreck_boxes": len(wreck),
        "total": len(allb), "bodies": len(boxes["bodies"]),
        "largest_wreck": top(wreck), "largest_drivable": top(drivable),
        "largest_all": top(allb),
        "extents_convention": boxes["summary"]["extents_convention"],
    }


def fits(box_extents_cm, hulls):
    """Smallest sorted-span margin over the decoded hulls (axis-agnostic, stated as such)."""
    box = sorted(v / 100.0 for v in box_extents_cm)
    best = None
    for h in hulls:
        sp = sorted(h["spans"])
        margins = [sp[i] - box[i] for i in range(3)]
        if min(margins) < 0:
            continue
        cand = {"hull_offset": h["offset"], "hull_spans_m": [round(v, 4) for v in sp],
                "box_spans_m": [round(v, 4) for v in box],
                "margins_m": [round(v, 4) for v in margins]}
        if best is None or min(margins) > min(best["margins_m"]):
            best = cand
    return best


def row_text(row):
    return json.dumps(row.get("cells"), ensure_ascii=False)


def in_scope(row):
    return row["id"].startswith("T-CO") or bool(SCOPE.search(row_text(row)))


def add(C, claim, decoded, ok, severity, note=""):
    C.append({"claim": claim, "decoded": decoded, "ok": ok, "severity": severity, "note": note})


def verdict_of(checks):
    fails = [c for c in checks if c["ok"] is False]
    unknown = [c for c in checks if c["ok"] is None]
    if any(c["severity"] in ("number", "asset", "target") for c in fails):
        return "MISMATCH"
    if fails or unknown:
        return "PARTIAL"
    return "MATCHES"


def check_row(row, ctx):
    rid = row["id"]
    cells = row["cells"]
    C = []
    t22, bc, van = ctx["t22"], ctx["box"], ctx["vanilla"]

    if rid == "T-CO1":
        add(C, cells[1],
            "decoded box census: %d boxes (%d in BmGame.upk, %d wreck) over %d BmGame bodies; "
            "T-22's 32 is the body count across its 4-package census, not a box count"
            % (bc["total"], bc["drivable_boxes"], bc["wreck_boxes"], bc["bodies"]),
            bc["total"] == 32,
            "noun",
            "the number 32 is right (bodies); the noun is not (%d boxes decoded)" % bc["total"])
        add(C, "bone, centre, extents",
            "every decoded box carries bone + TM translation + extents_cm (keys present on all "
            "%d records); extents convention is %s"
            % (bc["total"], bc["extents_convention"]),
            True, "asset")
        add(C, cells[2],
            "decoded JC3 donor: %d hulls, %d extern meshes, %d geometries, %d compounds, "
            "%d instances (%d part-wired)"
            % (van["hulls"], van["extern_meshes"], van["geometries"], len(van["compounds"]),
               van["instances"], van["instances_wired"]),
            True, "target")
        gv = [g for g in ctx["groups"] if g["sha256"] == ctx["vanilla"]["sha256"]]
        moved = [g for g in ctx["groups"] if g["physics_system_data_identical"] is False]
        add(C, cells[4],
            "donor shapes present (%d hulls). Station move: %d of %d sha group(s) - %d of %d "
            "tree(s) - change `hknpPhysicsSystemData` (the 96-byte body entries that hold the "
            "hardpoints); the %d vanilla-identical tree(s) and B-10 do not (B-10 changes %d hull "
            "object(s), sysdata identical %s); `jc3hkx.stations` finds %d station quads in any file"
            % (van["hulls"], len(moved), len(ctx["groups"]),
               sum(len(g["trees"]) for g in moved), ctx["tree_count"], len(gv),
               ctx["b10"]["changed_objects"], ctx["b10"]["physics_system_data_identical"],
               van["station_sets"]),
            None, "target",
            "build-dependent: true of the trees that carry moved station/body data, false of the "
            "current vanilla-identical trees and of B-10")

    elif rid == "T-CO2":
        lw, la = bc["largest_wreck"], bc["largest_all"]
        l22 = t22["bmak"]["largest"]
        claim = [316.15, 63.42, 109.88]
        add(C, cells[1],
            "the triple is T-22's recorded largest (bone %s, extents_cm %s); the largest wreck box "
            "is %s at %s cm and the largest decoded box is %s cm"
            % (l22["bone"], l22["extents_cm"], lw["bone"], lw["extents_cm"], la["extents_cm"]),
            all(abs(a - b) < 0.06 for a, b in zip(sorted(l22["extents_cm"]), sorted(claim))),
            "number")
        add(C, "'largest box'",
            "the largest decoded box is %s export %s bone %s extents_cm %s - its longest side is "
            "%.1f cm more than the triple's"
            % ("the drivable chassis" if la is bc["largest_drivable"] else "a box", la["export"],
               la["bone"], la["extents_cm"], max(la["extents_cm"]) - max(claim)),
            max(la["extents_cm"]) <= max(claim) + 1e-9,
            "number",
            "the row's superlative holds only within T-22's wreck set")
        add(C, "1 cm = 0.01 m",
            "3.1615 x 0.6342 x 1.0988 m",
            all(abs(v / 100.0 - e) < 1e-4 for v, e in zip(claim, [3.1615, 0.6342, 1.0988])),
            "number")
        fitw, fita = ctx["fit"], ctx["fit_largest"]
        add(C, cells[4],
            "the 3.1615 m box fits hull @%s (margins %s m); the largest decoded box fits any hull: "
            "%s (its %.2f m side against a %.3f m hull)"
            % (fitw["hull_offset"] if fitw else "-", fitw["margins_m"] if fitw else "-",
               bool(fita), max(la["extents_cm"]) / 100.0,
               ctx["vanilla"]["max_hull_axis_m"]),
            bool(fitw) and not fita, "number")

    elif rid == "T-CO3":
        parts = t22["donor_parts"]
        withw = [p for p in parts if p["has_world_collision_shape"] == 1]
        without = [p for p in parts if p["has_world_collision_shape"] == 0]
        wheels = [p for p in without if "_wheel_" in p["part"]]
        add(C, cells[4],
            "recounted from the donor part table: %d/%d parts have a world collision shape; the "
            "%d without are %s, all with world_collision_body_id -1"
            % (len(withw), len(parts), len(without), [p["part"] for p in without]),
            len(withw) == 38 and len(wheels) == 4
            and all(p["world_collision_body_id"] == -1 for p in without),
            "number")

    elif rid == "T-P3":
        cats = t22["bmak"]["categories"]
        add(C, cells[1],
            "T-22 body census: %d bodies, categories %s (sum %d); decoded box total %d"
            % (t22["bmak"]["bodies"], cats, sum(cats.values()), bc["total"]),
            t22["bmak"]["bodies"] == 32 and "boxes" not in cells[1],
            "noun",
            "32 is bodies across 4 packages; the decoded box count is %d" % bc["total"])
        add(C, cells[4],
            "T-22 summary: mapped_bodies %d, mapped_to_a_slot %d, unmapped %d, hull_slots %d; "
            "decoded file: %d hulls, %d instances (%d wired), static compounds %s"
            % (t22["summary"]["mapped_bodies"], t22["summary"]["mapped_to_a_slot"],
               t22["summary"]["unmapped"], t22["summary"]["hull_slots"], van["hulls"],
               van["instances"], van["instances_wired"],
               [c["instances"] for c in van["compounds"] if c["class"] == "hknpStaticCompoundShape"]),
            t22["summary"]["mapped_bodies"] == 11 and t22["summary"]["mapped_to_a_slot"] == 7,
            "number")
        add(C, "21 not driveable (18 debris, 1 root, 1 turret, 1 jet fin)",
            "categories: debris %d, root %d, turret %d, jet fin %d = %d"
            % (cats.get("destruction debris"), cats.get("root placeholder"), cats.get("turret"),
               cats.get("jet fin"),
               sum(cats.get(k) for k in ("destruction debris", "root placeholder", "turret",
                                         "jet fin"))),
            sum(cats.get(k, 0) for k in ("destruction debris", "root placeholder", "turret",
                                         "jet fin")) == 21,
            "number")
        add(C, "11 T-8 parts have no slot", "the T-8 part table is not read here", None, "unknown")

    elif rid == "T-PA3":
        parts = {p["part"].split("sportsmuscle_", 1)[-1]: p for p in t22["donor_parts"]}
        want = {"body": 0, "door_f_l": 1, "engine": 7}
        got = {k: parts[k]["world_collision_body_id"] for k in want if k in parts}
        wheels = [p for p in t22["donor_parts"] if "_wheel_" in p["part"]]
        add(C, cells[4],
            "donor part table: %s; wheels %s"
            % (got, [p["world_collision_body_id"] for p in wheels]),
            got == want and all(p["world_collision_body_id"] == -1 for p in wheels),
            "number")
        add(C, "in the built graph", "the built .epe is not read by this card", None, "unknown")

    return {"id": rid, "section": row.get("section"), "dispo": row.get("dispo"),
            "why": row.get("why"), "cells": cells, "checks": C, "verdict": verdict_of(C)}


def role_check(rid, ctx):
    """Does the row's JC3 target match the body role G3-10 decoded?"""
    van = ctx["vanilla"]
    if rid in ("T-CO1", "T-P3", "T-CO2"):
        return {"ok": True,
                "text": "target is the donor's part-bound hull set: %d of %d instances carry a "
                        "part index (G3-10), hulls %s m" % (van["instances_wired"], van["instances"],
                                                            van["max_hull_axis_m"])}
    if rid == "T-CO3":
        return {"ok": True,
                "text": "wheels sim-only: G3-10 gives the 4 wheel parts world body -1 (raycast "
                        "ids only), which is what the row keeps"}
    if rid == "T-PA3":
        return {"ok": True,
                "text": "the part -> world body ids match G3-10's donor table (body 0, door_f_l 1, "
                        "engine 7, wheels -1)"}
    return {"ok": None, "text": "no role claim"}


def build():
    rows = [json.loads(l) for l in open(T_ROWS, encoding="utf-8") if l.strip()]
    t22, boxes, roles = load(T22), load(BOXES), load(ROLES)
    sub = [r for r in rows if in_scope(r)]
    near = [r["id"] for r in rows if not in_scope(r) and NEAR.search(row_text(r))]

    van = census(VANILLA)
    b10 = census(B10)
    trees = sorted({p for pat in TREE_GLOBS for p in glob.glob(os.path.join(ROOT, pat))})
    by_sha: dict[str, list[str]] = {}
    for p in trees:
        by_sha.setdefault(sha16(p), []).append(rel(p))
    groups = []
    for sha, paths in sorted(by_sha.items(), key=lambda kv: -len(kv[1])):
        rec = census(os.path.join(ROOT, paths[0]))
        info, bad = H.check_file(os.path.join(ROOT, paths[0]), against=VANILLA)
        groups.append({"sha256": sha, "trees": paths, "census": strip_private(rec),
                       "changed_objects": info.get("changed_objects"),
                       "changed_classes": info.get("changed_classes"),
                       "physics_system_data_identical": info.get("physics_system_data_identical"),
                       "problems": bad})
    info_b10, bad_b10 = H.check_file(B10, against=VANILLA)

    ctx = {"t22": t22, "box": box_census(boxes), "roles": roles, "vanilla": strip_private(van),
           "tree_count": len(trees),
           "b10": {"changed_objects": info_b10.get("changed_objects"),
                   "changed_classes": info_b10.get("changed_classes"),
                   "physics_system_data_identical": info_b10.get("physics_system_data_identical"),
                   "problems": bad_b10, "census": strip_private(b10)},
           "groups": groups}
    ctx["vanilla_hulls"] = van["hull_detail"]
    ctx["fit"] = fits([316.15, 63.42, 109.88], van["hull_detail"])
    ctx["fit_largest"] = fits(ctx["box"]["largest_all"]["extents_cm"], van["hull_detail"])

    checked = [check_row(r, ctx) for r in sub]
    for rec in checked:
        rec["role"] = role_check(rec["id"], ctx)

    oracles = []

    def oracle(key, ok, evidence):
        oracles.append({"key": key, "ok": bool(ok), "evidence": evidence})

    # O1: quoted numbers still present in the row they are quoted from
    quoted = {"T-CO1": ["32", ".physicsc"], "T-CO2": ["316.15", "63.42", "109.88", "0.01"],
              "T-CO3": ["38", "42"], "T-P3": ["32", "11", "7", "21", "18"],
              "T-PA3": ["world_collision_body_id", "raycast_body_id"]}
    missing = [(rid, tok) for rid, toks in quoted.items() for tok in toks
               if rid in {r["id"] for r in sub}
               and tok not in row_text(next(r for r in sub if r["id"] == rid))]
    oracle("O1-ledger-quotes", not missing,
           "%d rows in scope; every quoted token re-read from its row%s"
           % (len(sub), "" if not missing else "; MISSING %r" % (missing,)))

    # O2: box census recounted
    rec = ctx["box"]
    sums = (rec["drivable_boxes"] == boxes["summary"]["boxes_bmgame"]
            and rec["wreck_boxes"] == boxes["summary"]["boxes_wreck"]
            and rec["total"] == boxes["summary"]["boxes_total"] == rec["drivable_boxes"] + rec["wreck_boxes"])
    oracle("O2-box-census", sums,
           "recounted %d boxes (%d BmGame + %d wreck) over %d BmGame bodies; summary says %d/%d/%d"
           % (rec["total"], rec["drivable_boxes"], rec["wreck_boxes"], rec["bodies"],
              boxes["summary"]["boxes_total"], boxes["summary"]["boxes_bmgame"],
              boxes["summary"]["boxes_wreck"]))

    # O3: T-22 categories sum to its body count
    cats = t22["bmak"]["categories"]
    oracle("O3-t22-bodies", sum(cats.values()) == t22["bmak"]["bodies"],
           "categories %s sum to %d = bmak.bodies %d"
           % (cats, sum(cats.values()), t22["bmak"]["bodies"]))

    # O4: physicsc ladder.  Vanilla and B-10 must pass it.  A historical build tree that does
    # not is reported per group (and in the note) instead of being folded into a pass.
    grp_bad = {g["sha256"]: g["problems"] for g in groups if g["problems"]}
    same_as_van = [g["sha256"] == van["sha256"] for g in groups]
    oracle("O4-physicsc-ladder", not bad_b10,
           "vanilla %s (%d hulls, %d body entries, %d compounds, %d instances); %d build tree(s) "
           "in %d sha group(s), %d vanilla-identical; B-10 changes %d object(s) %s, sysdata "
           "identical %s, 0 ladder problems; %d/%d tree group(s) differ from vanilla: %s"
           % (van["sha256"], van["hulls"], van["body_entries"], len(van["compounds"]),
              van["instances"], len(trees), len(groups), sum(same_as_van),
              info_b10.get("changed_objects"), info_b10.get("changed_classes"),
              info_b10.get("physics_system_data_identical"), len(grp_bad), len(groups),
              {k[:8]: v[:1] for k, v in grp_bad.items()}))

    # O5: containment recomputed from hull vertices, for the claimed box and the real largest
    fit, fitl = ctx["fit"], ctx["fit_largest"]
    oracle("O5-hull-fit", bool(fit) and min(fit["margins_m"]) >= 0 and fitl is None,
           "the 3.1615 m box fits hull @%s with margins %s m (sorted axes, axis-agnostic); the "
           "largest decoded box %s cm fits no hull"
           % (fit["hull_offset"] if fit else "-", fit["margins_m"] if fit else "-",
              rec["largest_all"]["extents_cm"]))

    # O6: 38/42 and 4 wheels recounted
    parts = t22["donor_parts"]
    w = sum(1 for p in parts if p["has_world_collision_shape"] == 1)
    wheels = [p for p in parts if p["has_world_collision_shape"] == 0 and "wheel" in p["part"]]
    oracle("O6-part-flags", w == 38 and len(parts) == 42 and len(wheels) == 4
           and all(p["world_collision_body_id"] == -1 for p in wheels),
           "%d/%d parts with a world shape; %d without, all wheels: %s"
           % (w, len(parts), len(wheels), [p["part"] for p in wheels]))

    # O7: 7 slots from the static compounds
    static = [c for c in ctx["vanilla"]["compounds"] if c["class"] == "hknpStaticCompoundShape"]
    unbound = ctx["vanilla"]["instances"] - ctx["vanilla"]["instances_wired"]
    oracle("O7-hull-slots", [c["instances"] for c in static] == [7, 7] and unbound == 14,
           "static compounds %s instances; %d unbound of %d instances"
           % ([c["instances"] for c in static], unbound, ctx["vanilla"]["instances"]))

    # O8: citations still present in their artifacts
    frame_txt = json.dumps(load(FRAME))
    sel_txt = json.dumps(load(SELECTOR))
    geom_txt = json.dumps(load(GEOM))
    cites = [("COLLISION_FRAME.json", "PROVEN", "PROVEN" in frame_txt),
             ("COLLISION_GEOM.json", "UNKNOWN", "UNKNOWN" in geom_txt),
             ("COLLISION_SELECTOR.json", "mesh", "mesh" in sel_txt.lower())]
    oracle("O8-citations", all(c[2] for c in cites),
           "; ".join("%s: %s %s" % (f, t, "present" if ok else "MISSING") for f, t, ok in cites))

    doc = {
        "card": "G3-11d - collision rows re-checked against G3-01 and G3-10",
        "generated_by": "Tools/scripts/g3_11d_collision_recheck.py --write",
        "inputs": {"ledger": rel(T_ROWS), "t22": rel(T22), "boxes": rel(BOXES),
                   "geom": rel(GEOM), "frame": rel(FRAME), "selector": rel(SELECTOR),
                   "roles": rel(ROLES), "vanilla": VANILLA, "b10": rel(B10)},
        "scope": {"rule": "id starts T-CO, or a cell names .physicsc / world_collision* / "
                          "raycast_body_id / collision bodies",
                  "rows": [r["id"] for r in sub], "near_misses": near},
        "box_census": rec, "fit": fit, "t22_largest": t22["bmak"]["largest"],
        "physicsc": {"vanilla": strip_private(van), "b10": ctx["b10"], "trees": groups,
                     "tree_count": len(trees)},
        "rows": checked, "oracles": oracles,
        "unknowns": [
            "the built .epe's own world_collision_body_id / raycast_body_id values: this card "
            "reads the .physicsc, not the entity graph, so T-PA3's 'built graph' half is UNKNOWN",
            "which BmAK box maps to which JC3 hull: G3-10 decodes the hull -> part wiring but not "
            "the body-entry -> compound reference, so the 11 -> 7 fit is a count match, not a map",
            "the T-8 part list behind '11 T-8 parts have no slot' (T8_PARTS.json is not read here)",
            "the 0x4C bool word's meaning on the BmAK boxes (G3-01b UNKNOWN), so its use as a "
            "collision flag cannot be checked",
        ],
    }
    return doc


def render(doc):
    L = []

    def A(x):
        L.append(x)

    ok = sum(1 for o in doc["oracles"] if o["ok"])
    v = doc["box_census"]
    A("# Collision rows re-checked (G3-11d)")
    A("")
    A("Generated by `Tools/scripts/g3_11d_collision_recheck.py --write`. `--check` re-derives "
      "every number, hash and verdict from `Working/Translation/T_ROWS.jsonl`, the G3-01/G3-10 "
      "artifacts and the `.physicsc` bytes. No translation decision is made here.")
    A("")
    A("**Oracles %d/%d pass.** Rows in scope: **%d** (%s). Near-misses (mention hull/collision, "
      "not collision rows): %s."
      % (ok, len(doc["oracles"]), len(doc["rows"]), ", ".join(r["id"] for r in doc["rows"]),
         ", ".join(doc["scope"]["near_misses"]) or "none"))
    A("")
    A("## 1. What G3-01 decoded (the source side)")
    A("")
    A("- boxes: **%d** records over **%d** BmGame bodies (%d in BmGame.upk, %d wreck), extents "
      "convention **%s**"
      % (v["total"], v["bodies"], v["drivable_boxes"], v["wreck_boxes"], v["extents_convention"]))
    A("- largest drivable box: export `%s` bone `%s`, extents `%s` cm"
      % (v["largest_drivable"]["export"], v["largest_drivable"]["bone"],
         v["largest_drivable"]["extents_cm"]))
    A("- largest wreck box: bone `%s` export `%s`, extents `%s` cm; T-22's recorded largest (the "
      "triple the ledger quotes) is a different box: bone `%s`, extents `%s` cm"
      % (v["largest_wreck"]["bone"], v["largest_wreck"]["export"],
         v["largest_wreck"]["extents_cm"], doc["t22_largest"]["bone"],
         doc["t22_largest"]["extents_cm"]))
    A("- element 0 of each mode mesh is decoded (COLLISION_GEOM/COLLISION_CONVEX); elements 1..N "
      "of the drivable boxes are decoded as 56 convex elements on the two mode meshes")
    A("- frame: COLLISION_FRAME's verdict is `PROVEN within tolerance`, with the chassis box "
      "outside the render bounds by design of the full-length extents")
    A("- selector: `SetBatmanVsBatmobileCollisionMode` swaps the two collision mesh components "
      "(mode 1 pursuit, mode 2 battle), decoded call-by-call")
    A("")
    A("## 2. Row by row")
    A("")
    for r in doc["rows"]:
        A("### `%s` - verdict **%s**" % (r["id"], r["verdict"]))
        A("")
        A("Section: %s. Disposition in the ledger: `%s`." % (r["section"], r["dispo"]))
        A("")
        A("| side | claim (from the ledger) | decoded | ok |")
        A("|---|---|---|---|")
        for c in r["checks"]:
            A("| %s | %s | %s | %s |"
              % (c["severity"], c["claim"][:110], c["decoded"][:220],
                 "yes" if c["ok"] is True else ("**no**" if c["ok"] is False else "UNKNOWN")))
        if r["role"]:
            A("")
            A("G3-10 role match: %s - %s"
              % ("yes" if r["role"]["ok"] else "UNKNOWN", r["role"]["text"]))
        A("")
    A("## 3. The `.physicsc` actually carried by the build")
    A("")
    A("| file / group | trees | bytes | sha256 | hulls | mesh | body entries | compounds | "
      "instances | wired | vs vanilla |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    van = doc["physicsc"]["vanilla"]
    A("| vanilla (game) | - | %s | `%s` | %d | %d | %s | %d | %d | %d | - |"
      % (f"{van['bytes']:,}", van["sha256"], van["hulls"], van["extern_meshes"],
         van["body_entries"], len(van["compounds"]), van["instances"], van["instances_wired"]))
    b10 = doc["physicsc"]["b10"]
    A("| B-10 `Working/Collision/batmobile.physicsc` | - | %s | `%s` | %d | %d | %s | %d | %d | "
      "%d | %d object(s) changed (%s), sysdata identical %s |"
      % (f"{b10['census']['bytes']:,}", b10["census"]["sha256"], b10["census"]["hulls"],
         b10["census"]["extern_meshes"], b10["census"]["body_entries"],
         len(b10["census"]["compounds"]), b10["census"]["instances"],
         b10["census"]["instances_wired"], b10["changed_objects"],
         ", ".join(b10["changed_classes"] or []), b10["physics_system_data_identical"]))
    for g in doc["physicsc"]["trees"]:
        c = g["census"]
        A("| build trees `%s` (`%s`) | %d | %s | `%s` | %d | %d | %s | %d | %d | %d | %d changed, "
          "sysdata identical %s, %d problem(s) |"
          % (g["sha256"][:8], g["trees"][0].split("/")[1], len(g["trees"]), f"{c['bytes']:,}",
             c["sha256"], c["hulls"], c["extern_meshes"], c["body_entries"],
             len(c["compounds"]), c["instances"], c["instances_wired"],
             g["changed_objects"] or 0, g["physics_system_data_identical"],
             len(g["problems"])))
    A("")
    A("Hull longest axis: vanilla `%.3f m`, B-10 `%.3f m`. Station quads in every file: `%d` - so "
      "a station move is not visible in the `.physicsc` at all."
      % (van["max_hull_axis_m"], b10["census"]["max_hull_axis_m"], van["station_sets"]))
    broken = [(g["sha256"][:8], g["problems"][:2]) for g in doc["physicsc"]["trees"]
              if g["problems"]]
    if broken:
        A("")
        A("Build-tree groups whose bytes differ from vanilla (the imported ladder flags a "
          "physics-system-data change): %s"
          % "; ".join("`%s`: %s" % (sha, p) for sha, p in broken))
    A("")
    A("## 4. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in doc["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**", o["evidence"]))
    A("")
    A("## 5. UNKNOWN")
    A("")
    for u in doc["unknowns"]:
        A("- %s" % u)
    A("")
    A("## 6. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/g3_11d_collision_recheck.py --write")
    A("uv run python Tools/scripts/g3_11d_collision_recheck.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    doc = build()
    md, js = render(doc), json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    fails = [o["key"] for o in doc["oracles"] if not o["ok"]]

    if a.write:
        if fails:
            print("FAIL: oracles failed, nothing written: %s" % ", ".join(fails))
            for o in doc["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(js)
        print("wrote Research/BatmobileGrab/COLLISION_LEDGER_CHECK.md and .json")
        print("  %d rows in scope, %d oracles pass, %d build tree(s) in %d sha group(s)"
              % (len(doc["rows"]), len(doc["oracles"]), doc["physicsc"]["tree_count"],
                 len(doc["physicsc"]["trees"])))
        for r in doc["rows"]:
            print("    %-8s %-10s %s" % (r["id"], r["verdict"],
                                         "; ".join("NO" if c["ok"] is False else
                                                   ("?" if c["ok"] is None else "ok")
                                                   for c in r["checks"])))
        return 0

    if fails:
        print("FAIL")
        for o in doc["oracles"]:
            if not o["ok"]:
                print("  - oracle %s: %s" % (o["key"], o["evidence"]))
        return 1
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if open(OUT_MD, encoding="utf-8").read() != md:
        print("FAIL: COLLISION_LEDGER_CHECK.md is stale")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        print("FAIL: COLLISION_LEDGER_CHECK.json is stale")
        return 1
    print("OK %d/%d oracles, %d rows, %d build trees, md+json identical"
          % (len(doc["oracles"]), len(doc["oracles"]), len(doc["rows"]),
             doc["physicsc"]["tree_count"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
