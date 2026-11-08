"""bm_schema.py - B-04L (translate): lift the Batmobile parts module to the game's LIVE schema.

Found by the B-18 crash (2026-11-02, MODLOG): READ of 0x8 at JustCause3.exe+0x2d49e0, the signature
MODLOG sect 43-48 traced to a parts module out of step with the patched game. B-04 rewrote the parts
module from bm-001's copy, which is the PRE-PATCH file inside the shipped .ee (29,886 B, type
`VehicleParts` 176 B, hash 3002630396). The game runs the patch_win64/game4 copy (30,540 B): the same
data under `VehicleParts` 192 B (hash 2760276721) with one more member, `ik_chains` (A[IKChain], empty
in the vanilla Serpente). Until B-18 the vanilla module shadowed ours (shared path), so B-04's file was
never read by the game; once it got its own path the engine read `ik_chains` past the old struct.

The port (through the patched ConvertAdf XML, like B-04/B-17):
  * the `VehicleParts` type definition is replaced by the live one, and the live `A[IKChain]` / `IKChain`
    definitions are added - copied from the live file, not written by hand;
  * the instance's two type-hash references follow; `ik_chains` is added as the live file has it (null
    array, id -1: the Batmobile has no IK chains, nor does the Serpente).
Checks: every part decodes identical before/after; the result's type library contains every live type
with the live hash; the instance differs from the input only by those lines.

    bm_schema.port_parts(module_path, live_bytes, workdir) -> dict
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bm_parts  # noqa: E402

BODY_REQUIRED = {"Turret", "Cannon", "GatlingGun", "AirBrake", "EngineRotatingPart"}
TYPE_RE = r'<type type="{kind}" [^>]*name="{name}" name-hash="(\d+)"'


def _x(adf_path: str, xml: str) -> str:
    r = subprocess.run([bm_parts.ADF, "--e", adf_path, xml], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"B-04L: ConvertAdf --e {adf_path} failed")
    return open(xml, encoding="utf-8-sig").read()


def _struct(t: str, name: str) -> re.Match:
    m = re.search(rf'([ \t]*)<type type="Structure" [^>]*name="{re.escape(name)}" name-hash="(\d+)".*?</type>\n',
                  t, re.S)
    if not m:
        raise SystemExit(f"B-04L: no {name} structure")
    return m


def _types(t: str) -> set:
    return set(re.findall(r'<type [^>]*name="([^"]+)" name-hash="(\d+)"', t))


def _instance(t: str) -> list[str]:
    i = t[t.index("<instances"):]
    return [re.sub(r' offset-in-file="[^"]*"', "", ln) for ln in i.splitlines()]


def port_parts(module: str, live: bytes, workdir: str) -> dict:
    os.makedirs(workdir, exist_ok=True)
    lv = os.path.join(workdir, "live_parts.vmodc")
    open(lv, "wb").write(live)
    L = _x(lv, os.path.join(workdir, "live.xml"))
    O = _x(module, os.path.join(workdir, "ours.xml"))
    lvp, ovp = _struct(L, "VehicleParts"), _struct(O, "VehicleParts")
    old_h, new_h = ovp.group(2), lvp.group(2)
    if old_h == new_h:
        return {"card": "B-04L", "ported": False, "reason": "already the live schema", "hash": new_h}
    ik_arr = re.search(r'[ \t]*<type type="Array" [^>]*name="A\[IKChain\]"[^>]*/>\n', L)
    ik = _struct(L, "IKChain")
    ik_line = re.search(r'[ \t]*<member name="ik_chains" gbltype="Array"[^>]*/>\n', L)
    if not (ik_arr and ik_line) or 'id="-1"' not in ik_line.group(0):
        raise SystemExit("B-04L: the live file's ik_chains is not the expected null array")
    t = O[:ovp.start()] + lvp.group(0) + O[ovp.end():]
    t = t.replace("    </type-definitions>", ik_arr.group(0) + ik.group(0) + "    </type-definitions>", 1)
    n_h = t.count(f'type-hash="{old_h}"')
    if n_h != 2:
        raise SystemExit(f"B-04L: expected 2 instance refs to VehicleParts {old_h}, found {n_h}")
    t = t.replace(f'type-hash="{old_h}"', f'type-hash="{new_h}"')
    anchor = re.search(r'[ \t]*<member name="point_part_constraints" gbltype="Array"[^>]*/>\n', t)
    t = t[:anchor.end()] + ik_line.group(0) + t[anchor.end():]
    xo = os.path.join(workdir, "ported.xml")
    open(xo, "w", encoding="utf-8").write(t)
    before = open(module, "rb").read()
    r = subprocess.run([bm_parts.ADF, "--i", xo, module], capture_output=True, text=True)
    if r.returncode:
        open(module, "wb").write(before)
        raise SystemExit("B-04L: ConvertAdf --i failed: " + (r.stdout + r.stderr)[-300:])
    # checks
    after = open(module, "rb").read()
    if bm_parts.decode_parts(after) != bm_parts.decode_parts(before):
        raise SystemExit("B-04L: parts changed by the port")
    A = _x(module, os.path.join(workdir, "after.xml"))
    missing = _types(L) - _types(A)
    if missing:
        raise SystemExit(f"B-04L: live types missing after the port: {missing}")
    ia, io = _instance(A), _instance(O)
    added = [x for x in ia if x not in io]
    gone = [x for x in io if x not in ia]
    if len(added) != 3 or len(gone) != 2 or not any("ik_chains" in x for x in added):
        raise SystemExit(f"B-04L: instance changed beyond the port: +{added[:4]} -{gone[:4]}")
    return {"card": "B-04L", "ported": True, "vehicle_parts_type": f"{old_h} -> {new_h}",
            "bytes": f"{len(before)} -> {len(after)}", "parts": len(bm_parts.decode_parts(after)),
            "instance_lines_changed": {"added": len(added), "removed": len(gone)}}


# ---------------------------------------------------------------------------------------------------------------
# B-04R (translate): rebuild the parts module on the LIVE file, in the vanilla index space.
#
# Found by the B-04L crash (2026-11-02, MODLOG): READ 0x60 at +0x14fbac1 = a per-part physics-body toggle for
# body 4 on a NULL owner. Body 4 is door_f_r's world_collision_body_id. B-04 deleted the doors (indices 1, 2)
# and appended 19 parts out of order, so its array broke the invariant every vanilla module keeps
# (part_index == array position, 0..n-1) while the physicsc still has the door bodies and the vanilla deform
# module (archives) addresses parts by `from_part_index`. Translation rule: the Batmobile keeps the donor's
# index space - parts the Batmobile does not have stay in their slot with starts_deleted = 1 (the shipped
# convention for absent parts, bm_hide.py docstring), and new parts are appended in index order.
def rebuild_parts(stage_module: str, live: bytes, workdir: str) -> dict:
    if os.environ.get("BM_PARTS_PURE") == "1":   # Q probe 6: the live module, unmodified
        open(stage_module, "wb").write(live)
        return {"card": "B-04R", "probe": "BM_PARTS_PURE=1: live patch_win64 module, 0 edits",
                "parts": len(bm_parts.decode_parts(live))}
    import copy
    os.makedirs(workdir, exist_ok=True)
    plan = bm_parts.build_plan()
    doors = [] if os.environ.get("BM_DOORS_LIVE") == "1" else [r["name"] for r in plan["removals"]]   # Q probe 4
    if not doors:   # doors live: their children stay theirs (vanilla tree)
        plan = dict(plan, reparent=[])
    plan = dict(plan, removals=[], start_deleted=doors, link_children=True,
                new_parts=sorted(copy.deepcopy(plan["new_parts"]), key=lambda p: p["part_index"]))
    if os.environ.get("BM_BEHAVIOUR_NONE") == "1":
        # Fleet rule (PARTS_TABLE.jsonl, 233 entities): Turret/Cannon/GatlingGun/AirBrake/EngineRotatingPart
        # parts ALWAYS carry a world collision body; B-04's have none. Until they get bodies they are plain parts.
        for p in plan["new_parts"]:
            if p["behaviour"] in BODY_REQUIRED:
                p["behaviour"], p["behaviour_hash"] = "None", 0
        plan["hinged"], plan["rotating"] = [], []
    lv = os.path.join(workdir, "live_parts.vmodc")
    open(lv, "wb").write(live)
    out = os.path.join(workdir, "rebuilt_parts.vmodc")
    bm_parts.write_module(plan, lv, out, workdir)
    new = bm_parts.decode_parts(open(out, "rb").read())
    old = {p["name"]: p for p in bm_parts.decode_parts(open(stage_module, "rb").read())}
    van = {p["name"]: p for p in bm_parts.decode_parts(live)}
    N = {p["name"]: p for p in new}
    errs = []
    if [p["part_index"] for p in new] != list(range(len(new))):
        errs.append("part_index != array position")
    if len(new) != len(van) + len(plan["new_parts"]):
        errs.append(f"{len(new)} parts, expected {len(van) + len(plan['new_parts'])}")
    moved = {r["name"] for r in plan["reparent"]}
    skip = {"children_part_indices", "starts_deleted", "parent_part_index"}
    for n, v in van.items():   # donor parts: identical to the live file but for the declared edits
        d = [k for k in v if k not in skip and N[n][k] != v[k]
             and not (k == "parent_space_offset" and n in moved)]
        if d:
            errs.append(f"{n} changed {d}")
        if (N[n]["starts_deleted"] != 0) != (n in doors) and not v["starts_deleted"]:
            errs.append(f"{n} starts_deleted {N[n]['starts_deleted']}")
        if N[n]["parent_part_index"] != (0 if n in moved else v["parent_part_index"]):
            errs.append(f"{n} parent {N[n]['parent_part_index']}")
    import numpy as np
    def world(pl, n):
        by_i = {q["part_index"]: q for q in pl.values()}
        p, M = pl[n], np.eye(4)
        while True:
            M = M @ np.array(p["parent_space_offset"], np.float64).reshape(4, 4)
            q = by_i.get(p["parent_part_index"])
            if q is None or q is p:
                return M
            p = q
    for n in moved:   # door children re-parented to the body keep their world transform
        if not np.allclose(world(N, n), world(van, n), atol=1e-4):
            errs.append(f"{n} moved by the door re-parent")
    hoist = plan.get("hoisted_off_wheels", {})
    for n in hoist:   # off-wheel hoist: new parent + offset, same world transform as B-04's
        if not np.allclose(world(N, n), world(old, n), atol=1e-4):
            errs.append(f"{n} moved by the wheel hoist")
    for p in plan["new_parts"]:   # B-04 parts: identical to what B-04 wrote
        ign = ("children_part_indices", "behavior") + (("parent_part_index", "parent_space_offset")
                                                        if p["name"] in hoist else ())
        d = [k for k in N[p["name"]] if k not in ign and N[p["name"]][k] != old[p["name"]][k]]
        if N[p["name"]]["behavior"] != p["behaviour"]:
            d.append("behavior")
        if d:
            errs.append(f"{p['name']} differs from B-04 in {d}")
    for p in new:   # tree: every child lists its parent and vice versa
        for k in p["children_part_indices"]:
            if new[k]["parent_part_index"] != p["part_index"]:
                errs.append(f"{p['name']} lists child {k} whose parent is {new[k]['parent_part_index']}")
    for p in new:
        if p["parent_part_index"] not in (p["part_index"], -1, 255) and \
                p["part_index"] not in new[p["parent_part_index"]]["children_part_indices"]:
            errs.append(f"{p['name']} not in its parent's children")
    under_wheel = [p["name"] for p in new if p["parent_part_index"] in plan["wheel_parts"]
                   and p["parent_part_index"] != p["part_index"]]
    if under_wheel:   # fleet rule: no car parents a part under a wheel part (0/170)
        errs.append(f"parts under a wheel part: {under_wheel}")
    if errs:
        raise SystemExit("B-04R: " + " | ".join(errs[:8]))
    import shutil
    shutil.copyfile(out, stage_module)
    return {"card": "B-04R", "parts": len(new), "start_deleted": doors, "reparented": sorted(moved),
            "index_space": f"0..{len(new) - 1} contiguous",
            "hoisted_off_wheels": plan["hoisted_off_wheels"], "base": "live patch_win64 module"}
