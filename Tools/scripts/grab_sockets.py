"""grab_sockets.py - every Batmobile_V2 socket in JC3 space (G1-13).

The 65 sockets are `SkeletalMeshSocket` objects in `Playable_Batmobile_SF`, decoded by
`grab_model.sockets(package="Playable_Batmobile_SF")`.  Each carries a bone name, a
relative location (centimetres) and optionally a relative FRotator (Pitch, Yaw, Roll;
65536 = 360 degrees).  The cooked socket objects are positional, so the values come from
the exported tag stream, not from a hand-written table.

Placement uses the one transform, through `BONES.json`:

    bone world = bind pose from BONES.json (PSK cm)
    socket world = bone world + qrot(bone world q, relative location, inverse=True)
    JC3 position = bat_assemble.to_jc3_rot(socket world) * 0.01 + offset

The forward vector is the socket's local +X (UE forward), rotated by the socket rotation
and then by the bone's bind rotation, and finally by the same proper JC3 rotation.  The
up vector is local +Y.  This is the socket's frame, not an assumption about where a
muzzle points; the muzzle and tail checks below prove the convention on known anchors.

Two different facts are kept apart:

  * GRB-8 orphan light references: light entries whose socket name does not exist in the
    shipped mesh (`HeadLight1c`, `HeadLight2c`).  They are not sockets and have no
    location, so they cannot be placed.  Two are in `Playable_Batmobile_SF`; six exist
    across the three packages that use `Batmobile_V2`.
  * Body-envelope outliers: sockets that are placed but lie outside the assembled body
    bbox expanded by 0.5 m.  These are the four `HangFromRope_*` anchors, which sit
    about 4.6 m above the wheel pivots by design.

The six `HeadLight*` sockets that ride `Winch_DOOR_Mesh` are neither missing nor outside
the body box; they are flagged as door-bound because a future winch-door part must carry
them.

Outputs:
  Research/BatmobileGrab/SOCKETS_JC3.json
  Research/BatmobileGrab/SOCKETS_JC3.md

Usage:
  python Tools/scripts/grab_sockets.py --write
  python Tools/scripts/grab_sockets.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bat_assemble as BA  # noqa: E402
import grab_bones as GB  # noqa: E402
import grab_model as GM  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GRAB = ROOT / "Research" / "BatmobileGrab"
OUT_JSON = GRAB / "SOCKETS_JC3.json"
OUT_MD = GRAB / "SOCKETS_JC3.md"
BONES_JSON = GRAB / "BONES.json"
LIGHTS_JSON = GRAB / "LIGHTS.json"
STATIONS = ROOT / "Working" / "TrueScale" / "stations.json"

PACKAGE = "Playable_Batmobile_SF"
SCHEMA = 1
SCALE = 0.01
BODY_PAD_M = 0.5
ROT_UNITS = 65536.0
REQUIRED = (
    "Driver", "CannonMuzzle", "ChainGunMuzzle", "RiotSuppressorMuzzle",
    "MissileL", "MissileR", "Afterburner", "Afterburner_Front", "WinchOrigin",
    "BattleModeSpotLight", "BootLight", "Dashboard_Light", "Headlight_Centre",
)


class SocketError(Exception):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fnum(v, places: int = 6):
    return None if v is None else round(float(v), places)


def vec(v, places: int = 6):
    return [fnum(x, places) for x in v]


def qnorm(q):
    q = np.asarray(q, dtype=np.float64)
    n = float(np.linalg.norm(q))
    if n < 1e-12:
        raise SocketError("zero quaternion")
    return q / n


def qconj(q):
    return np.array([-q[0], -q[1], -q[2], q[3]], dtype=np.float64)


def qmul(a, b):
    x1, y1, z1, w1 = qnorm(a)
    x2, y2, z2, w2 = qnorm(b)
    return np.array([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ], dtype=np.float64)


def qrot(q, v, inverse: bool = False):
    q = qnorm(q)
    u = q[:3].copy()
    w = q[3]
    if inverse:
        u = -u
    v = np.asarray(v, dtype=np.float64)
    return 2.0 * np.dot(u, v) * u + (w * w - np.dot(u, u)) * v + 2.0 * w * np.cross(u, v)


def jc3_vec(v):
    return BA.to_jc3_rot(np.asarray(v, dtype=np.float64).reshape(1, 3))[0]


def rotator_quat(raw):
    """UE3 FRotator (Pitch, Yaw, Roll; 65536 units per turn) -> PSK quaternion."""
    if raw is None:
        return np.array([0.0, 0.0, 0.0, 1.0])
    p = float(raw[0]) * 2.0 * math.pi / ROT_UNITS
    y = float(raw[1]) * 2.0 * math.pi / ROT_UNITS
    r = float(raw[2]) * 2.0 * math.pi / ROT_UNITS
    cp, sp = math.cos(p / 2.0), math.sin(p / 2.0)
    cy, sy = math.cos(y / 2.0), math.sin(y / 2.0)
    cr, sr = math.cos(r / 2.0), math.sin(r / 2.0)
    return qnorm(np.array([
        cr * sp * sy - sr * cp * cy,
        -cr * sp * cy - sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    ]))


def rotator_deg(raw):
    if raw is None:
        return None
    return [fnum(float(x) * 360.0 / ROT_UNITS, 4) for x in raw]


def role(name: str) -> str:
    n = name.lower()
    if n.startswith("hangfromrope"):
        return "rope_anchor"
    if "muzzle" in n:
        return "muzzle"
    if n.startswith("missile"):
        return "missile"
    if n.startswith("mine") or n.startswith("hydra"):
        return "mine"
    if n.startswith("afterburner"):
        return "afterburner"
    if "wheellight" in n:
        return "wheel_light"
    if n.startswith("headlight") or "spotlight" in n or n == "bootlight" or n == "dashboard_light":
        return "light"
    if n.startswith("brakelight") or n.startswith("braketrail"):
        return "tail_light"
    if n.startswith("winch"):
        return "winch"
    if "shell" in n:
        return "shells"
    if "gasvent" in n:
        return "vent"
    if "exhaust" in n:
        return "exhaust"
    if n.startswith("zapper"):
        return "zapper"
    if n.startswith("scrapesparks"):
        return "sparks"
    if "battery" in n:
        return "battery"
    if n.startswith("cockpit"):
        return "cockpit"
    if n.startswith("dashboard"):
        return "dashboard"
    if n == "speedlines":
        return "fx"
    if "noise" in n:
        return "audio"
    if n == "driver" or n == "driveranimorigin":
        return "driver"
    return "other"


def part_hint(bone: str) -> str:
    b = bone.lower()
    if "front_left" in b or "frnt_left" in b:
        return "wheel_f_l"
    if "front_right" in b or "frnt_right" in b:
        return "wheel_f_r"
    if "rear_left" in b:
        return "wheel_r_l"
    if "rear_right" in b:
        return "wheel_r_r"
    if b == "jetsmove" or "jet" in b:
        return "jet"
    if "aero_flap" in b:
        return "aero_flaps"
    if "weapons" in b:
        if "turret" in b:
            return "turret"
        return "weapons"
    if "winch_door" in b:
        return "winch_door"
    if "nose" in b:
        return "nose"
    if "cockpit" in b:
        return "cockpit"
    return "body"


def collect() -> dict:
    bdoc = json.loads(BONES_JSON.read_text(encoding="utf-8"))
    bones = bdoc["bones"]
    by_name = {b["name"]: b for b in bones}
    if len(bones) != 180:
        raise SocketError("BONES.json has %d bones, expected 180" % len(bones))

    g = GM.Grab()
    raw_socks = g.sockets(package=PACKAGE)
    socks = {v["socket"]: v for k, v in raw_socks.items() if not isinstance(k, tuple)}
    if len(socks) != 65:
        raise SocketError("found %d Batmobile_V2 sockets, expected 65" % len(socks))

    stations = json.loads(STATIONS.read_text(encoding="utf-8"))
    body_lo = np.array(stations["body_bbox"][0], dtype=np.float64)
    body_hi = np.array(stations["body_bbox"][1], dtype=np.float64)
    box_lo = body_lo - BODY_PAD_M
    box_hi = body_hi + BODY_PAD_M
    offset = np.array(bdoc["transform"]["offset_used"], dtype=np.float64)

    rows = []
    for name in sorted(socks):
        s = socks[name]
        bone = by_name.get(s["bone"])
        if bone is None:
            raise SocketError("%s rides missing bone %s" % (name, s["bone"]))
        loc = s["location"] or [0.0, 0.0, 0.0]
        if s["location"] is not None and len(s["location"]) != 3:
            raise SocketError("%s location is not a 3-vector" % name)
        lq = rotator_quat(s["rotation"])
        bwq = np.array(bone["bind"]["world_rotation_quat"], dtype=np.float64)
        bwp = np.array(bone["bind"]["world_position_cm"], dtype=np.float64)
        wq = qmul(lq, bwq)
        wp = bwp + qrot(bwq, np.array(loc, dtype=np.float64), inverse=True)
        p = BA.to_jc3_rot(wp.reshape(1, 3))[0] * SCALE + offset
        fwd = jc3_vec(qrot(wq, np.array([1.0, 0.0, 0.0])))
        up = jc3_vec(qrot(wq, np.array([0.0, 1.0, 0.0])))
        right = jc3_vec(qrot(wq, np.array([0.0, 0.0, 1.0])))
        inside = bool(np.all(p >= box_lo) and np.all(p <= box_hi))
        outside = max(0.0, float(np.max(np.maximum(box_lo - p, p - box_hi))))
        out_axes = [ax for ax, x in zip("xyz", p) if x < box_lo["xyz".index(ax)] or x > box_hi["xyz".index(ax)]]
        rows.append({
            "socket": name,
            "bone": s["bone"],
            "bone_parent": bone["parent"],
            "part_hint": part_hint(s["bone"]),
            "role": role(name),
            "relative_location_cm": None if s["location"] is None else vec(s["location"]),
            "relative_rotation_raw": None if s["rotation"] is None else [int(x) for x in s["rotation"]],
            "relative_rotation_deg": rotator_deg(s["rotation"]),
            "relative_rotation_quat": vec(lq, 8),
            "bone_position_m": vec(BA.to_jc3_rot(bwp.reshape(1, 3))[0] * SCALE + offset),
            "position_m": vec(p),
            "forward_jc3": vec(fwd),
            "up_jc3": vec(up),
            "right_jc3": vec(right),
            "inside_body_box": inside,
            "outside_by_m": fnum(outside),
            "outside_axes": out_axes,
            "door_bound": s["bone"] == "Winch_DOOR_Mesh",
            "location_missing": s["location"] is None,
            "rotation_missing": s["rotation"] is None,
        })

    # GRB-8 orphan light references, straight from LIGHTS.json
    ldoc = json.loads(LIGHTS_JSON.read_text(encoding="utf-8"))
    orphan_refs = []
    for v in ldoc["vehicles"]:
        for e in v["entries"]:
            if e.get("orphan_socket") or e.get("bone") is None:
                orphan_refs.append({
                    "package": v["package"],
                    "owner": v["owner"],
                    "socket": e["socket"],
                    "type": e.get("type"),
                    "behavior": e.get("behavior"),
                    "reason": "socket name is not a SkeletalMeshSocket in the shipped mesh",
                })
    orphan_refs.sort(key=lambda x: (x["package"], x["socket"], x["type"] or ""))

    parts = Counter(r["part_hint"] for r in rows)
    outside_rows = [r for r in rows if not r["inside_body_box"]]
    door_rows = [r for r in rows if r["door_bound"]]
    required_present = [n for n in REQUIRED if n in socks]
    headlights = sorted(n for n in socks if n.lower().startswith("headlight"))
    brake_lights = sorted(n for n in socks if n.startswith("BrakeLight"))
    wheel_lights = sorted(n for n in socks if "WheelLight" in n)

    def dot(row, v):
        return float(np.dot(row["forward_jc3"], v))

    by_socket = {r["socket"]: r for r in rows}
    checks = {
        "socket_count_65": len(rows) == 65,
        "all_sockets_placed": all(np.isfinite(r["position_m"]).all() for r in rows),
        "all_socket_bones_in_bones_json": all(r["bone"] in by_name for r in rows),
        "all_socket_parents_resolved": all(r["bone_parent"] in by_name for r in rows),
        "required_anchors_present": len(required_present) == len(REQUIRED),
        "headlight_family_present": headlights == sorted([
            "Headlight_Centre", "HeadLight1", "HeadLight1a", "HeadLight1b",
            "HeadLight2", "HeadLight2a", "HeadLight2b"]),
        "brakelight_family_present": brake_lights == ["BrakeLightL", "BrakeLightR"],
        "wheellight_family_6": len(wheel_lights) == 6,
        "forward_vectors_unit": all(abs(float(np.linalg.norm(r["forward_jc3"])) - 1.0) < 1e-6
                                    for r in rows),
        "muzzle_forward": min(dot(by_socket[n], [0.0, 0.0, -1.0])
                              for n in ("CannonMuzzle", "ChainGunMuzzle",
                                        "RiotSuppressorMuzzle")) > 0.999,
        "missile_forward_up": all(dot(by_socket[n], [0.0, 0.0, -1.0]) > 0.70 and
                                  dot(by_socket[n], [0.0, 1.0, 0.0]) > 0.70
                                  for n in ("MissileL", "MissileR")),
        "tail_forward": all(dot(by_socket[n], [0.0, 0.0, 1.0]) > 0.98
                            for n in ("BrakeLightL", "BrakeLightR")),
        "body_box_outliers_are_hang_ropes": sorted(r["socket"] for r in outside_rows) == sorted([
            "HangFromRope_Front_Left", "HangFromRope_Front_Right",
            "HangFromRope_Rear_Left", "HangFromRope_Rear_Right"]),
        "grb8_orphan_refs_total_6": len(orphan_refs) == 6,
        "grb8_orphan_refs_this_package_2": sum(1 for o in orphan_refs
                                               if o["package"] == PACKAGE) == 2,
        "door_bound_headlights_6": len(door_rows) == 6,
    }

    verdict = (
        "65/65 Batmobile_V2 sockets placed; 61/65 inside the body box +0.5 m. "
        "The four HangFromRope anchors are %.3f m above the box by design. "
        "GRB-8 has 6 orphan light references (2 in Batmobile); %d HeadLight* sockets ride "
        "Winch_DOOR_Mesh. Required anchors %d/%d."
        % (max(r["outside_by_m"] for r in outside_rows), len(door_rows),
           len(required_present), len(REQUIRED))
    )

    doc = {
        "schema": SCHEMA,
        "generator": "grab_sockets.py",
        "verdict": verdict,
        "inputs": {
            "package": PACKAGE,
            "bones_json": str(BONES_JSON),
            "bones_sha256": sha256_file(BONES_JSON),
            "grab_json": str(GRAB / "grab.json"),
            "grab_sha256": sha256_file(GRAB / "grab.json"),
            "objects_jsonl": str(GRAB / "objects.jsonl"),
            "objects_sha256": sha256_file(GRAB / "objects.jsonl"),
            "lights_json": str(LIGHTS_JSON),
            "lights_sha256": sha256_file(LIGHTS_JSON),
            "stations": str(STATIONS),
            "stations_sha256": sha256_file(STATIONS),
        },
        "convention": {
            "socket_source": "SkeletalMeshSocket objects, Playable_Batmobile_SF",
            "rotator": "UE3 FRotator (Pitch, Yaw, Roll), 65536 = 360 degrees; null = identity",
            "relative_location": "centimetres in the bone's local frame",
            "bone_frame": "BONES.json bind world (PSK: X length, Y width, Z up)",
            "world_position": "bone pivot + qrot(bone q, relative location, inverse=True)",
            "jc3_transform": "bat_assemble.to_jc3_rot(p) * 0.01 + offset",
            "forward": "socket local +X through socket rot * bone bind rot * JC3 rotation",
            "up": "socket local +Y through the same rotations",
            "body_box": "Working/TrueScale/stations.json body_bbox, expanded by 0.5 m",
        },
        "counts": {
            "sockets": len(rows),
            "placed": len(rows),
            "bones_found": len(rows),
            "inside_body_box": sum(1 for r in rows if r["inside_body_box"]),
            "outside_body_box": len(outside_rows),
            "door_bound": len(door_rows),
            "missing_locations": sum(1 for r in rows if r["location_missing"]),
            "missing_rotations": sum(1 for r in rows if r["rotation_missing"]),
            "by_part": dict(sorted(parts.items())),
            "by_role": dict(sorted(Counter(r["role"] for r in rows).items())),
            "required_anchors": len(REQUIRED),
            "required_present": len(required_present),
            "grb8_orphan_refs": len(orphan_refs),
            "grb8_orphan_refs_this_package": sum(1 for o in orphan_refs if o["package"] == PACKAGE),
        },
        "body_box": {
            "min_m": vec(body_lo),
            "max_m": vec(body_hi),
            "expanded_by_m": BODY_PAD_M,
            "expanded_min_m": vec(box_lo),
            "expanded_max_m": vec(box_hi),
            "outliers": [{
                "socket": r["socket"],
                "bone": r["bone"],
                "position_m": r["position_m"],
                "outside_by_m": r["outside_by_m"],
                "axes": r["outside_axes"],
            } for r in outside_rows],
        },
        "required_anchors": {
            "names": list(REQUIRED),
            "present": required_present,
            "missing": [n for n in REQUIRED if n not in socks],
        },
        "orphan_light_refs": orphan_refs,
        "door_bound": [{
            "socket": r["socket"], "bone": r["bone"], "part_hint": r["part_hint"],
            "position_m": r["position_m"],
        } for r in door_rows],
        "sockets": rows,
        "checks": checks,
    }

    # ---- markdown ----
    md = []
    md.append("# Batmobile_V2 — sockets in JC3 space (G1-13)")
    md.append("")
    md.append("Generated by `Tools/scripts/grab_sockets.py` from `grab_model.sockets("
              "package=\"%s\")`, `BONES.json`, `LIGHTS.json` and `stations.json`." % PACKAGE)
    md.append("")
    md.append("**Verdict:** " + verdict)
    md.append("")
    md.append("## Convention")
    md.append("")
    md.append("- Positions are JC3 metres: X width, Y up, Z length, nose at **-Z**.")
    md.append("- A socket location is centimetres in its bone's local frame. The socket"
              " world point is `bone + qrot(bone q, local, inverse=True)`, then the one "
              "`to_jc3_rot(p) * 0.01 + offset` transform.")
    md.append("- `forward` is the socket's local +X (UE forward), and `up` is local +Y. "
              "Both go through socket rotation, bone bind rotation and the JC3 rotation.")
    md.append("- A null rotator is identity. A null location (`DriverAnimOrigin`) places "
              "the socket at its bone pivot.")
    md.append("- Every socket lists its bone and that bone's parent from `BONES.json`; "
              "`Batmobile_Chassis` is the root and its parent is itself.")
    md.append("")
    md.append("## Counts")
    md.append("")
    md.append("| fact | value |")
    md.append("|---|---:|")
    for label, key in (("sockets", "sockets"), ("placed", "placed"),
                       ("inside body box +0.5 m", "inside_body_box"),
                       ("outside body box", "outside_body_box"),
                       ("door-bound HeadLight sockets", "door_bound"),
                       ("missing relative locations", "missing_locations"),
                       ("missing relative rotations", "missing_rotations"),
                       ("required anchors present", "required_present"),
                       ("GRB-8 orphan light references", "grb8_orphan_refs"),
                       ("GRB-8 orphan refs in this package", "grb8_orphan_refs_this_package")):
        md.append("| %s | %s |" % (label, doc["counts"][key]))
    md.append("")
    md.append("By part hint: " + ", ".join("`%s` %d" % (k, v)
                                           for k, v in doc["counts"]["by_part"].items()) + ".")
    md.append("")
    md.append("## Outliers")
    md.append("")
    md.append("| socket | bone | position (m) | outside by | axes |")
    md.append("|---|---|---|---:|---|")
    for r in outside_rows:
        md.append("| `%s` | `%s` | %s | %.3f m | %s |" % (
            r["socket"], r["bone"], ", ".join("%.3f" % x for x in r["position_m"]),
            r["outside_by_m"], ", ".join(r["outside_axes"])))
    md.append("")
    md.append("These four are the helicopter rope anchors. They are placed correctly and "
              "are not a transform error; the body box check simply excludes them.")
    md.append("")
    md.append("## GRB-8 orphan light references (not sockets)")
    md.append("")
    md.append("| package | owner | missing socket | type | behavior |")
    md.append("|---|---|---|---|---|")
    for o in orphan_refs:
        md.append("| `%s` | `%s` | `%s` | `%s` | `%s` |" % (
            o["package"], o["owner"], o["socket"], o["type"], o["behavior"]))
    md.append("")
    md.append("`HeadLight1c` and `HeadLight2c` are light entries in three packages, so six "
              "references exist; none is a `SkeletalMeshSocket` and none can be placed. "
              "They stay listed here as orphans rather than being given invented coordinates.")
    md.append("")
    md.append("## Door-bound light sockets")
    md.append("")
    md.append("These six are real sockets and are inside the body box, but they follow "
              "`Winch_DOOR_Mesh`; a future winch-door part must carry them.")
    md.append("")
    md.append("| socket | bone | position (m) |")
    md.append("|---|---|---|")
    for r in door_rows:
        md.append("| `%s` | `%s` | %s |" % (
            r["socket"], r["bone"], ", ".join("%.3f" % x for x in r["position_m"])))
    md.append("")
    md.append("## All 65 sockets")
    md.append("")
    md.append("| socket | bone | parent bone | part | role | pos x | pos y | pos z | fwd x | fwd y | fwd z | inside |")
    md.append("|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|")
    for r in rows:
        md.append("| `%s` | `%s` | `%s` | `%s` | %s | %.3f | %.3f | %.3f | %.3f | %.3f | %.3f | %s |" % (
            r["socket"], r["bone"], r["bone_parent"], r["part_hint"], r["role"],
            r["position_m"][0], r["position_m"][1], r["position_m"][2],
            r["forward_jc3"][0], r["forward_jc3"][1], r["forward_jc3"][2],
            "yes" if r["inside_body_box"] else "**no**"))
    md.append("")
    md.append("## Required anchors")
    md.append("")
    md.append("| socket | bone | position (m) | forward |")
    md.append("|---|---|---|---|")
    for n in REQUIRED:
        if n not in by_socket:
            md.append("| `%s` | **MISSING** | — | — |" % n)
            continue
        r = by_socket[n]
        md.append("| `%s` | `%s` | %s | %s |" % (
            n, r["bone"], ", ".join("%.3f" % x for x in r["position_m"]),
            ", ".join("%.3f" % x for x in r["forward_jc3"])))
    md.append("")
    md.append("The `MissileLaunchSockets` array on `Batmobile_EMP_Missile_Launcher` was "
              "recorded by G1-08 as two undecoded entries (shape only). The two physical "
              "missile sockets on this mesh are `MissileL` and `MissileR`; both are placed, "
              "but the array-to-socket mapping is inferred, not read.")
    md.append("")
    md.append("## Checks")
    md.append("")
    md.append("| check | result |")
    md.append("|---|---|")
    for k, v in checks.items():
        md.append("| `%s` | %s |" % (k, "PASS" if v else "**FAIL**"))
    md.append("")
    md.append("`--check` re-derives this table and both files.")
    md.append("")
    return doc, "\n".join(md)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write SOCKETS_JC3.json and .md")
    g.add_argument("--check", action="store_true", help="re-derive and compare the outputs")
    a = ap.parse_args()
    try:
        doc, md = collect()
    except (SocketError, GM.GrabError, KeyError, ValueError, OSError) as e:
        print("FAIL: %s" % e, file=sys.stderr)
        return 1

    fail = [k for k, v in doc["checks"].items() if not v]
    if fail:
        print("FAIL: checks %s" % ", ".join(fail), file=sys.stderr)
        return 1

    if a.write:
        OUT_JSON.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        OUT_MD.write_text(md + "\n", encoding="utf-8")
        print(doc["verdict"])
        print("wrote %s and %s" % (OUT_JSON, OUT_MD))
        return 0

    if not OUT_JSON.exists() or not OUT_MD.exists():
        print("FAIL: outputs missing; run --write", file=sys.stderr)
        return 1
    old = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    if json.dumps(old, sort_keys=True) != json.dumps(doc, sort_keys=True):
        print("FAIL: SOCKETS_JC3.json differs from the re-derived record", file=sys.stderr)
        return 1
    if OUT_MD.read_text(encoding="utf-8").rstrip("\n") != md.rstrip("\n"):
        print("FAIL: SOCKETS_JC3.md differs from the re-derived record", file=sys.stderr)
        return 1
    print("PASS: %s" % doc["verdict"])
    for k, v in doc["checks"].items():
        print("  %-42s %s" % (k, "PASS" if v else "FAIL"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
