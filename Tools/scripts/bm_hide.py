"""bm_hide.py - B-17: hide the Serpente panels that show through the Batmobile (starts_deleted).

Found by V-02 (`v02_render.py` + the per-part blame, 2026-10-31): 35 parts still draw vanilla Serpente
meshes; 10 of them are visible. User decision 2026-10-31: "unbind panels".

Method: `starts_deleted = 1` in the parts module - shipped practice: 478 parts in 234 fleet modules start
deleted (e.g. the medium/bavarium tanks' shield_body/turret/cannon, should_break 0, appears_on_death 0).
No part is removed, so no index, child list or hoisted array moves (B-04's removal path is not used).

B-17b (user decision 2026-10-31 "reparent then hide all three"): sportsmuscle_engine (parent of both
front wheels, the hoods, fenders, bumper, grill) and sportsmuscle_fender_l/_r (parents of the headlights
and signals) are hidden too. First every child of theirs that is NOT hidden is re-parented to
sportsmuscle_body with parent_space_offset = M_child @ M_fender @ M_engine, so its world transform is
unchanged (asserted to 1e-4) and no starts_deleted cascade can reach it. Children lists are moved with it.
Still drawn: taillight_r_r / headlight_f_r_02 (vanilla lamp parts; hiding may drop a light).

    bm_hide.apply(aaf) -> dict      (bm_rc.py step 3c)
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bm_parts  # noqa: E402

HIDE = ["sportsmuscle_front_bumper", "sportsmuscle_plate_f", "sportsmuscle_rear_bumper", "sportsmuscle_grill",
        "sportsmuscle_f_r_seat", "sportsmuscle_r_mirror",
        "sportsmuscle_f_l_seat", "sportsmuscle_hood"]  # B-17c 2026-10-31
HIDE_PARENTS = ["sportsmuscle_engine", "sportsmuscle_fender_l", "sportsmuscle_fender_r",
                "sportsmuscle_hood_signature"]  # carries missile_base_signature
TO = "sportsmuscle_body"
HELD = {"sportsmuscle_taillight_r_r": "vanilla lamp", "sportsmuscle_headlight_f_r_02": "vanilla lamp"}


def _M(p):
    import numpy as np
    return np.array(p["parent_space_offset"], np.float64).reshape(4, 4)


def _world(p, by_i):
    q = by_i.get(p["parent_part_index"])
    return _M(p) @ _world(q, by_i) if q is not None and q is not p else _M(p)


def apply(aaf: str, workdir: str) -> dict:
    mod = os.path.join(aaf, bm_parts.MODULE)
    import numpy as np
    plist = bm_parts.decode_parts(open(mod, "rb").read())
    before = {p["name"]: p for p in plist}
    by_i = {p["part_index"]: p for p in plist}
    hide_all = HIDE + HIDE_PARENTS
    body = before[TO]
    # children of the hidden parents that stay visible -> body, world transform preserved
    moves = {}
    for n in HIDE_PARENTS:
        for k in before[n]["children_part_indices"]:
            c = by_i[k]
            if c["name"] in hide_all:
                continue
            local = _world(c, by_i) @ np.linalg.inv(_world(body, by_i))
            moves[c["part_index"]] = (c["name"], local.reshape(-1).tolist())
    for n in hide_all:
        p = before.get(n)
        if p is None:
            raise SystemExit(f"B-17: {n} not in the parts module")
        kids = [k for k in p["children_part_indices"]]
        own_kids = [q["name"] for q in before.values() if q["part_index"] in kids
                    and q["name"] not in hide_all and q["part_index"] not in moves]
        if own_kids:
            raise SystemExit(f"B-17: {n} has children not being hidden: {own_kids}")
    os.makedirs(workdir, exist_ok=True)
    x_in, x_out = os.path.join(workdir, "hide_in.xml"), os.path.join(workdir, "hide_out.xml")
    r = subprocess.run([bm_parts.ADF, "--e", mod, x_in], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("B-17: ConvertAdf export failed")
    text = open(x_in, encoding="utf-8-sig").read()
    root = ET.fromstring(text)
    inst = root.find("instances/instance")
    parts_el = bm_parts.member(inst, "parts")
    arrays = {x.get("id"): x for x in inst.findall("member") if x.get("id")}
    body_pi = body["part_index"]
    body_ent = next(e for e in parts_el.findall("member") if bm_parts.string_of(e, "name") == TO)
    body_arr = arrays[bm_parts.member(body_ent, "children_part_indices").get("id")]
    for ent in parts_el.findall("member"):
        pi = int(bm_parts.member(ent, "part_index").text)
        if pi in moves:
            bm_parts.member(ent, "parent_part_index").text = str(body_pi)
            bm_parts.set_floats(bm_parts.member(ent, "parent_space_offset"), moves[pi][1])
            proto = body_arr.find("member")
            kid = ET.SubElement(body_arr, "member", dict(proto.attrib)); kid.text = str(pi)
            kid.attrib.pop("offset-in-file", None)
            kid.tail = proto.tail
        if bm_parts.string_of(ent, "name") in HIDE_PARENTS:
            ref = bm_parts.member(ent, "children_part_indices").get("id")
            for kid in list(arrays[ref].findall("member")):
                if int(kid.text) in moves:
                    arrays[ref].remove(kid)
    done = []
    for ent in parts_el.findall("member"):
        if bm_parts.string_of(ent, "name") in hide_all:
            m = bm_parts.member(ent, "starts_deleted")
            if m is None:
                raise SystemExit("B-17: no starts_deleted member")
            m.text = "1"
            done.append(bm_parts.string_of(ent, "name"))
    ET.ElementTree(root).write(x_out, encoding="utf-8", xml_declaration=True)
    r = subprocess.run([bm_parts.ADF, "--i", x_out, mod], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("B-17: ConvertAdf import failed: " + (r.stdout + r.stderr)[-300:])
    alist = bm_parts.decode_parts(open(mod, "rb").read())
    after = {p["name"]: p for p in alist}
    a_by_i = {p["part_index"]: p for p in alist}
    changed = sorted(n for n in after if after[n] != before[n])
    expect = set(hide_all) | {v[0] for v in moves.values()} | {TO}
    if len(after) != len(before) or sorted(done) != sorted(hide_all) or not set(changed) <= expect \
            or not all(after[n]["starts_deleted"] for n in hide_all):
        raise SystemExit(f"B-17: unexpected module change: {changed}")
    for pi, (n, _) in moves.items():
        c = after[n]
        if c["parent_part_index"] != body_pi or pi not in after[TO]["children_part_indices"] \
                or not np.allclose(_world(c, a_by_i), _world(by_i[pi], by_i), atol=1e-4):
            raise SystemExit(f"B-17: re-parent of {n} moved it")
    for n in HIDE_PARENTS:
        if set(after[n]["children_part_indices"]) & set(moves):
            raise SystemExit(f"B-17: {n} still lists a moved child")
    return {"card": "B-17", "hidden": sorted(hide_all), "reparented_to_body": sorted(v[0] for v in moves.values()),
            "held": HELD, "parts": len(after), "only_changed": changed}
