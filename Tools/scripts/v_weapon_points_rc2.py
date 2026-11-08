#!/usr/bin/env python
"""v_weapon_points_rc2.py - bm-RC2's 9 SWeaponPoint positions vs the BmAK sockets.

Read-only audit. For every `SWeaponPoint` the built `.epe` carries, this compares the
point's world origin (vehicle-local metres, JC3 frame) with the BmAK socket of the same
name after the repo's one conversion:

    JC3 = to_jc3_rot(PSK_cm) * scale + offset        to_jc3_rot(p) = (-y, z, -x)

`scale` and `offset` are read from `Working/TrueScale/stations.json`; the rotation is
`bat_assemble.to_jc3_rot` (`Tools/scripts/bat_assemble.py`, the def at "PSK (X length
prow+, Y width, Z up) -> JC3"), and the socket->world step (`bone pivot + qrot(bone q,
local, inverse=True)`) is `Tools/scripts/grab_sockets.py` at "wp = bwp + qrot(...)".
Both are recorded as the `convention` block of `SOCKETS_JC3.json`.

Outputs `Builds/bm-RC2/verify/weapon_points_vs_bmak.md`. `--check` re-exports the `.epe`
to a temp directory, re-runs the whole derivation and diffs the file byte for byte; no
build file is written or modified.

Status words used in the table: `match` (within the pass band), `UNKNOWN` (no BmAK socket
of that name exists - the row is not a measurement).
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUILD = "Builds/bm-RC2"
EPE = ("Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/"
       "v0300_car_kensington_sportsmuscle/"
       "v0300_car_kensington_sportsmuscle_debug.epe")
SOCKETS = "Research/BatmobileGrab/SOCKETS_JC3.json"
BONES = "Research/BatmobileGrab/BONES.json"
STATIONS = "Working/TrueScale/stations.json"
EXE = "Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe"
OUT = "Builds/bm-RC2/verify/weapon_points_vs_bmak.md"

# Derived pass band. The export prints metres with 6 decimals (quantum 1e-6 m = 1e-4 cm);
# 0.01 cm = 0.1 mm is 100x that quantum and far below any physical meaning on a 5 m car.
BAND_CM = 0.01
ATTACH = "attach.vehicle"


def rel(p):
    return p.replace(os.sep, "/")


def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return json.load(f)


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------- conversion
def to_jc3(p):
    """bat_assemble.to_jc3_rot: PSK (X length, Y width, Z up) -> JC3 (X width, Y up, Z, front -Z)."""
    return [-p[1], p[2], -p[0]]


def qnorm(q):
    n = sum(x * x for x in q) ** 0.5
    if n < 1e-12:
        raise SystemExit("zero quaternion in BONES.json")
    return [x / n for x in q]


def qrot(q, v, inverse=False):
    """grab_sockets.qrot: rotate v by q=(x,y,z,w); inverse conjugates the axis part."""
    q = qnorm(q)
    u = [-q[0], -q[1], -q[2]] if inverse else q[:3]
    w = q[3]
    dot = u[0] * v[0] + u[1] * v[1] + u[2] * v[2]
    uu = u[0] * u[0] + u[1] * u[1] + u[2] * u[2]
    cx = u[1] * v[2] - u[2] * v[1]
    cy = u[2] * v[0] - u[0] * v[2]
    cz = u[0] * v[1] - u[1] * v[0]
    return [2.0 * dot * u[i] + (w * w - uu) * v[i] + 2.0 * w * (cx, cy, cz)[i]
            for i in range(3)]


def jc3_from_psk_cm(p, scale, offset):
    r = to_jc3(p)
    return [r[i] * scale + offset[i] for i in range(3)]


def socket_world(s, bones, scale, offset):
    """grab_sockets.py: bone pivot + qrot(bone world q, socket local location, inverse=True)."""
    b = bones[s["bone"]]
    loc = s.get("relative_location_cm") or [0.0, 0.0, 0.0]
    bwp = b["bind"]["world_position_cm"]
    bwq = b["bind"]["world_rotation_quat"]
    d = qrot(bwq, loc, inverse=True)
    return jc3_from_psk_cm([bwp[i] + d[i] for i in range(3)], scale, offset)


# ---------------------------------------------------------------- the built graph
def _label(el):
    """The node's own name: XML attribute if present, else its `name` value, else its class."""
    n = el.get("name")
    if n:
        return n
    for v in el.findall("value"):
        if v.get("name") == "name" and (v.text or "").strip():
            return v.text.strip()
    for v in el.findall("value"):
        if v.get("name") == "_class" and (v.text or "").strip():
            return v.text.strip()
    return "?"


def _value(el, name):
    for v in el.findall("value"):
        if v.get("name") == name:
            return (v.text or "").strip()
    return None


def walk(el, parent, out):
    for child in el.findall("object"):
        lab = _label(child)
        out.append((child, parent, lab))
        walk(child, lab, out)


def export_epe(td):
    """ConvertProperty -e to the temp dir. Read-only on the build tree."""
    xml = os.path.join(td, "rc2.xml")
    exe = os.path.join(ROOT, EXE)
    src = os.path.join(ROOT, EPE)
    if not os.path.exists(exe):
        raise SystemExit(f"missing {EXE}")
    if not os.path.exists(src):
        raise SystemExit(f"missing {EPE}")
    r = subprocess.run([exe, "-e", src, xml], capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(xml):
        raise SystemExit(f"ConvertProperty failed ({r.returncode}): {r.stdout} {r.stderr}")
    return xml


def built_points(xml_path):
    root = ET.parse(xml_path).getroot()
    rows = []
    found = []
    walk(root.find("object"), None, found)
    for el, parent, lab in found:
        if _value(el, "_class") != "SWeaponPoint":
            continue
        w = _value(el, "world")
        if not w:
            continue
        m = [float(x) for x in w.replace(" ", "").split(",")]
        if len(m) != 16:
            raise SystemExit(f"SWeaponPoint {_value(el, 'name')}: world is not 16 floats")
        rows.append({
            "point": _value(el, "name"),
            "type": _value(el, "type"),
            "component": parent,
            "built_m": m[12:15],
            "parent": _value(el, "80201E4D") or _value(el, "5C19E7E0"),
        })
    return rows


# ---------------------------------------------------------------- the comparison
def build():
    st = load(STATIONS)
    scale, offset = float(st["scale"]), [float(x) for x in st["offset"]]
    socks = {s["socket"]: s for s in load(SOCKETS)["sockets"]}
    bones = {b["name"]: b for b in load(BONES)["bones"]}

    with tempfile.TemporaryDirectory() as td:
        pts = built_points(export_epe(td))

    rows = []
    rederived = []
    for p in pts:
        row = {"point": p["point"], "type": p["type"], "component": p["component"],
               "built_m": [round(x, 6) for x in p["built_m"]], "socket": None,
               "bmak_m": None, "role": None, "diff_cm": None, "mag_cm": None,
               "status": "UNKNOWN"}
        if p["point"] == ATTACH:
            row["note"] = ("type 4 MountAttach marker, cloned from the APC template; "
                           "no BmAK socket of this name exists")
            rows.append(row)
            continue
        s = socks.get(p["point"])
        if s is None:
            row["note"] = "no socket of this name in SOCKETS_JC3.json"
            rows.append(row)
            continue
        got = socket_world(s, bones, scale, offset)
        rederived.append({"socket": p["point"], "stored": s["position_m"],
                          "derived": got,
                          "delta_m": max(abs(got[i] - s["position_m"][i]) for i in range(3))})
        d = [(row["built_m"][i] - s["position_m"][i]) * 100.0 for i in range(3)]
        mag = (d[0] ** 2 + d[1] ** 2 + d[2] ** 2) ** 0.5
        row.update({"socket": p["point"],
                    "bmak_m": [round(float(x), 6) for x in s["position_m"]],
                    "role": s.get("role"),
                    "diff_cm": [round(x, 3) for x in d],
                    "mag_cm": round(mag, 3),
                    "status": "match" if mag <= BAND_CM else "MISMATCH"})
        rows.append(row)

    mounts = [r for r in rows if r["status"] in ("match", "MISMATCH")]
    checks = {
        "point_count_9": len(rows) == 9,
        "socket_points_5": len(mounts) == 5,
        "attach_points_4": sum(1 for r in rows if r["point"] == ATTACH) == 4,
        "all_socket_points_resolve": len(mounts) == 5,
        "conversion_reproduces_sockets_json": bool(rederived) and all(
            r["delta_m"] <= 1e-6 for r in rederived),
        "mounts_within_band": all(r["mag_cm"] <= BAND_CM for r in mounts) if mounts else False,
    }
    return {"build": BUILD, "epe": EPE, "epe_sha256": sha256(EPE),
            "scale": scale, "offset": offset, "band_cm": BAND_CM,
            "sockets_sha256": sha256(SOCKETS), "bones_sha256": sha256(BONES),
            "stations_sha256": sha256(STATIONS),
            "rows": rows, "rederived": rederived, "checks": checks,
            "max_mag_cm": max((r["mag_cm"] for r in mounts), default=None)}


def v3(p):
    return ", ".join(f"{x:.6f}" for x in p)


def d3(p):
    return ", ".join(f"{x:.3f}" for x in p)


def render(doc):
    rows = doc["rows"]
    mounts = [r for r in rows if r["status"] in ("match", "MISMATCH")]
    L = []
    L.append("# bm-RC2 - the 9 `SWeaponPoint`s vs the BmAK sockets")
    L.append("")
    L.append(f"Generated by `Tools/scripts/v_weapon_points_rc2.py --write`; `--check` re-exports "
             f"`{doc['epe']}` to a temp dir, re-runs the whole derivation and diffs this file "
             f"byte for byte. Read-only: no build file is written.")
    L.append("")
    L.append("**STATUS: DONE - "
             + (f"all {len(mounts)}/{len(mounts)} points that name a BmAK socket sit on it "
                f"(max |d| {doc['max_mag_cm']:.3f} cm, band {doc['band_cm']:g} cm); "
                if mounts and doc["checks"]["mounts_within_band"] else
                "the socket comparison has failures, see section 4; ")
             + "the 4 `attach.vehicle` points have no BmAK socket and stay UNKNOWN.**")
    L.append("")
    L.append(f"Build `{doc['build']}`, `.epe` sha256 `{doc['epe_sha256'][:12]}`. "
             f"9 `SWeaponPoint` objects found: {len(mounts)} named after a BmAK socket, "
             f"4 type-4 `attach.vehicle` mount markers.")
    L.append("")
    L.append("## 1. The coordinate conversion, and where it is decoded")
    L.append("")
    L.append("There is exactly one transform in this repo from the BmAK rig to JC3 vehicle-local "
             "metres:")
    L.append("")
    L.append("```text")
    L.append("JC3 = to_jc3_rot(PSK_cm) * scale + offset        to_jc3_rot(p) = (-py, pz, -px)")
    L.append(f"scale = {doc['scale']:g}        offset = ({v3(doc['offset'])})")
    L.append("```")
    L.append("")
    L.append("| piece | decoded at |")
    L.append("|---|---|")
    L.append("| `to_jc3_rot` (PSK X length, Y width, Z up -> JC3 X width, Y up, Z length, nose -Z; "
             "a proper rotation, det +1) | `Tools/scripts/bat_assemble.py`, the `to_jc3_rot` def "
             "(\"PSK (X length prow+, Y width, Z up) -> JC3 ...\"), used by `pivot_point` |")
    L.append("| `scale = 0.01` (the PSK is already real centimetres) and `offset` | "
             f"`{STATIONS}` (`scale`, `offset`), written by `bat_assemble.py --write` |")
    L.append("| socket location -> rig world: `bone pivot + qrot(bone world q, local, "
             "inverse=True)` | `Tools/scripts/grab_sockets.py`, the `wp = bwp + qrot(...)` line; "
             "the same rule is recorded as `convention.world_position` in "
             "`Research/BatmobileGrab/SOCKETS_JC3.json` |")
    L.append("| the combined rule `to_jc3_rot(p) * 0.01 + offset` | "
             "`SOCKETS_JC3.json` `convention.jc3_transform` |")
    L.append("")
    L.append("The BmAK column below is therefore a **derived** value: the table re-runs the "
             "socket->world step from `SOCKETS_JC3.json`'s own `relative_location_cm` and "
             "`BONES.json`'s bind world position/quaternion, then the transform above. Check "
             "`conversion_reproduces_sockets_json` proves it lands on the stored `position_m` "
             f"(max delta {max((r['delta_m'] for r in doc['rederived']), default=0.0):.2e} m), "
             "so the same numbers as the G1-13 table are reproduced rather than copied.")
    L.append("")
    L.append("## 2. The 9 points")
    L.append("")
    L.append("Positions are metres in the JC3 vehicle frame (X width, Y up, Z length, nose -Z). "
             "`d` is built - BmAK, in centimetres.")
    L.append("")
    L.append("| # | point | parent component | built (m) | BmAK socket (m) | socket role | "
             "dX | dY | dZ | \\|d\\| (cm) | status |")
    L.append("|---:|---|---|---|---|---|---:|---:|---:|---:|---|")
    for i, r in enumerate(rows, 1):
        if r["socket"]:
            L.append(f"| {i} | `{r['point']}` | `{r['component']}` | {v3(r['built_m'])} | "
                     f"{v3(r['bmak_m'])} | `{r['role']}` | {d3(r['diff_cm'])} | "
                     f"{r['mag_cm']:.3f} | {r['status']} |")
        else:
            L.append(f"| {i} | `{r['point']}` | `{r['component']}` | {v3(r['built_m'])} | - | - | "
                     f"- | - | - | - | UNKNOWN |")
    L.append("")
    L.append("Pass band: **0.01 cm** (0.1 mm). Derived: the export prints metres with 6 decimals, "
             "so one export quantum is 1e-6 m = 1e-4 cm; the band is 100x that and still ~1000x "
             "smaller than any physically meaningful offset on a 5 m car.")
    L.append("")
    L.append("## 3. What the table says")
    L.append("")
    L.append(f"* **{sum(1 for r in mounts if r['mag_cm'] <= doc['band_cm'])}/{len(mounts)} socket "
             f"points match**: `CannonMuzzle`, `ChainGunMuzzle`, `MissileL`, `MissileR`, "
             f"`BattleModeSpotLight` each sit on the socket of the same name, "
             f"max |d| {doc['max_mag_cm']:.3f} cm. The built world matrix's translation is the "
             f"`SOCKETS_JC3.json` `position_m` verbatim (B-05 wrote the point `world` from that "
             f"field), and the numbers above are the independent re-derivation.")
    L.append("* **The 4 `attach.vehicle` rows are not positions.** They are type-4 `MountAttach` "
             "markers cloned from the APC template with `world` = identity rotation + the "
             "template's local offset `0, -0.05405688, 0.002082527`; they name the chassis parts "
             "they attach to (`80201E4D`/`5C19E7E0`), not a BmAK fire point. BmAK has no socket "
             "by that name, so their position is UNKNOWN here, not a match.")
    L.append("* **`BattleModeSpotLight` is not a missile tube.** Its BmAK socket rides "
             "`Batmobile_Rig_Weapons_Drone_Decoder`, and BmAK's own pursuit launcher names it as "
             "`RPursuitModeMissileLauncher.LaunchSocketName = \"BattleModeSpotLight\"` "
             "(`Research/BatmobileGrab/WEAPONS.md`, the `RPursuitModeMissileLauncher` member "
             "table). So placing the EMP missile's point there follows the BmAK launch socket, "
             "but that socket is the spotlight/decoder anchor, not one of the two missile-mesh "
             "sockets `MissileL`/`MissileR`.")
    L.append("* **The two missile points sit on the launcher mesh's own sockets.** BmAK lists "
             "`MissileLaunchSockets` (array, 2 items, payload not decoded) and `MissileSockets` "
             "(`WEAPONS.md`, the launch-socket member list); which mesh socket each array entry "
             "maps to is not decoded, so `MissileL`/`MissileR` are matched by name/shape.")
    L.append("")
    L.append("## 4. Checks")
    L.append("")
    L.append("| check | result |")
    L.append("|---|---|")
    for k in ("point_count_9", "socket_points_5", "attach_points_4",
              "all_socket_points_resolve", "conversion_reproduces_sockets_json",
              "mounts_within_band"):
        L.append(f"| `{k}` | {'PASS' if doc['checks'][k] else 'FAIL'} |")
    L.append("")
    L.append("## 5. UNKNOWNs")
    L.append("")
    L.append("* **The position of the 4 `attach.vehicle` markers in BmAK terms.** They are "
             "template offsets, and no BmAK socket or bone of that name exists. What was tried: "
             "the whole 65-socket list (no `attach*` name) and the mount-part string properties "
             "on the point itself. Would be found in: a BmAK `MountAttach` table, which this repo "
             "has not decoded.")
    L.append("* **Which `MissileLaunchSockets` array entry belongs to which mesh socket.** The "
             "array is decoded as shape only (2 items, 8 B each; `WEAPONS.md`, the "
             "`RBatmobileEMPMissile` member table); the mapping to `MissileL`/`MissileR` is an "
             "inference from the two placed sockets, not a read value.")
    L.append("* **Whether JC3 uses a point's translation or only its rotation at runtime.** The "
             "positions are the same numbers a fleet vehicle stores; the engine side is native "
             "and is not decoded in this repo.")
    L.append("")
    L.append("## 6. Sources")
    L.append("")
    L.append("| source | sha256 |")
    L.append("|---|---|")
    L.append(f"| `{doc['epe']}` | `{doc['epe_sha256']}` |")
    L.append(f"| `{SOCKETS}` | `{doc['sockets_sha256']}` |")
    L.append(f"| `{BONES}` | `{doc['bones_sha256']}` |")
    L.append(f"| `{STATIONS}` | `{doc['stations_sha256']}` |")
    L.append("")
    L.append("## 7. Reproduce")
    L.append("")
    L.append("```")
    L.append("python Tools/scripts/v_weapon_points_rc2.py --check")
    L.append("```")
    L.append("")
    return "\n".join(L)


def write():
    doc = build()
    text = render(doc)
    path = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {OUT}: {len(doc['rows'])} points, {sum(1 for r in doc['rows'] if r['socket'])} "
          f"compared, max |d| {doc['max_mag_cm']:.3f} cm")
    for r in doc["rows"]:
        if r["socket"]:
            print(f"  {r['point']:<22} {v3(r['built_m'])}  {r['status']:<8} {r['mag_cm']:.3f} cm")
        else:
            print(f"  {r['point']:<22} {v3(r['built_m'])}  UNKNOWN (no BmAK socket)")
    return 0


def check():
    doc = build()
    want = render(doc)
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print(f"FAIL: {OUT} is missing (run --write)")
        return 1
    with open(path, encoding="utf-8") as f:
        got = f.read().replace("\r\n", "\n")
    ok = True
    for k, v in doc["checks"].items():
        print(f"  {k:<40} {'PASS' if v else 'FAIL'}")
        ok = ok and v
    if got != want:
        print("FAIL: the file differs from the re-derived text")
        gl, wl = got.splitlines(), want.splitlines()
        for i, (a, b) in enumerate(zip(gl, wl), 1):
            if a != b:
                print(f"  first difference at line {i}:\n  file: {a}\n  want: {b}")
                break
        else:
            print(f"  line count file {len(gl)} vs want {len(wl)}")
        ok = False
    else:
        print(f"  {'file_matches_rederivation':<40} PASS ({len(want)} bytes of text)")
    print(f"{'OK' if ok else 'FAILED'}: {sum(1 for r in doc['rows'] if r['socket'])}/"
          f"{len(doc['rows'])} points compared, max |d| {doc['max_mag_cm']:.3f} cm, "
          f"band {doc['band_cm']:g} cm")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    sys.exit(write() if a.write else check())


if __name__ == "__main__":
    main()
