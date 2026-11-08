"""t9_interaction.py - T-13: every JC3 interaction object's transform on the Batmobile body.

Reads `Research/JC3Grab/INTERACTION.json` (G2-18: the 85 donor interaction objects, their donor
positions, the three active stunt areas and the Batmobile body mesh) and places each object on the
Batmobile by **role**, not by the donor's bounding-box position:

  entry / exit / transition / point / trigger by side   -> the cockpit side of the Batmobile body
  *stunt* / *hood*                                      -> the roof / the hood stunt area
  interaction.seat.driver                               -> the `Driver` socket (COCKPIT.md §2)
  interaction.seat.stunt                                -> the roof stunt area
  interaction.seat.passenger1                           -> UNKNOWN: the Batmobile has one seat

Each anchor is a real point on the body shell found by a ray cast (`Working/TrueScale/body_lod1.rbm`
through `rbm_geom`), and the object is then moved **outward along the surface normal** by the
donor's own clearance where G2-18 decoded it (the stunt areas' `center_gap_m`) and by a chosen
band value elsewhere (the donor's side clearance is not in any decoded file - recorded as such).

Hijack objects (`*pull.out*`, `*pulled.out*`) are dropped: §11 `D-9` is resolved **no** (enemies
cannot pull Rico out of the Batmobile).

Output: `Working/Translation/t9_interaction.json` + `Working/Translation/T9_INTERACTION.md`.
`--check` rebuilds both from the sources, compares them field-for-field / byte-for-byte and asserts
the card's Done rule: every placed transform is >= 0.05 m outside the hull and <= 0.30 m from the
surface.

Usage:
    python Tools/scripts/t9_interaction.py --write
    python Tools/scripts/t9_interaction.py --check
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3interact  # noqa: E402  (mesh loader, exact triangle distance, inside test)

OUT = os.path.join(ROOT, "Working", "Translation")
SRC = os.path.join(ROOT, "Research", "JC3Grab", "INTERACTION.json")
JSON_NAME = "t9_interaction.json"
MD_NAME = "T9_INTERACTION.md"
SCHEMA = 1

BAND = (0.05, 0.30)         # the card's Done rule, metres
SIDE_MARGIN = 0.06          # band floor + 10 mm so a re-measure stays above 0.05
SIDE_CLEARANCE = 0.10       # chosen, inside the band (donor side clearance is not decoded)
SIDE_Y = 1.15               # cockpit side height, m  (COCKPIT.md: tub y 0.676..2.029)
SIDE_Z = -0.95              # cockpit side station, m (Driver z -1.065)
ROOF_Z = -0.50              # roof centre = the canopy over the driver (COCKPIT.md §3)
HOOD_Z = -2.14              # front deck = the hood (G2-18 front_area centre station)
UP_COS = math.cos(math.radians(20.0))   # the card's "normals within 20 deg of up"
DRIVER = (-0.0025, 0.8647, -1.0654)   # COCKPIT.md §2, the `Driver` socket
DROP = ("pull.out", "pulled.out")      # D-9 = no


# ------------------------------------------------------------------ geometry helpers
def up_faces(V, T):
    """Triangles whose face normal is within 20 deg of +up, with an up-oriented normal."""
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    ln = np.linalg.norm(n, axis=1)
    ok = ln > 1e-12
    n[ok] = n[ok] / ln[ok, None]
    flip = n[:, 1] < 0
    n[flip] = -n[flip]
    cent = (a + b + c) / 3.0
    return ok & (n[:, 1] >= UP_COS), n, cent


def plane_anchor(V, T, x, z):
    """A roof/deck plane: the up-facing triangle whose centroid is nearest (x, z)."""
    mask, n, cent = up_faces(V, T)
    idx = np.where(mask)[0]
    if not len(idx):
        raise SystemExit("no up-facing body triangle")
    d = np.hypot(cent[idx, 0] - x, cent[idx, 2] - z)
    i = int(idx[int(np.argmin(d))])
    return cent[i].copy(), n[i].copy()


def top_hit(V, T, x, z, y_from=3.2):
    """First body surface hit on a vertical ray down at (x, z): (point, normal)."""
    return _ray_hit(V, T, np.array([x, y_from, z]), np.array([0.0, -1.0, 0.0]),
                    np.array([0.0, 1.0, 0.0]))


def side_hit(V, T, sign, y, z, x_from=3.2):
    """First body surface hit on a horizontal ray at (y, z) from x = sign * 3.2."""
    d = np.array([-float(sign), 0.0, 0.0])
    return _ray_hit(V, T, np.array([sign * x_from, y, z]), d,
                    np.array([float(sign), 0.0, 0.0]))


def _ray_hit(V, T, origin, direction, normal):
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    e1, e2 = b - a, c - a
    h = np.cross(direction, e2)
    det = (e1 * h).sum(1)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1.0), 0.0)
    s = origin - a
    u = (s * h).sum(1) * inv
    q = np.cross(s, e1)
    v = (direction * q).sum(1) * inv
    t = (e2 * q).sum(1) * inv
    hit = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9) & (t > 1e-9)
    if not hit.any():
        raise SystemExit(f"ray from {origin} along {direction} misses the body mesh")
    i = int(np.argmin(np.where(hit, t, np.inf)))
    p = origin + direction * float(t[i])
    return p, normal


# ------------------------------------------------------------------ role table
def classify(name: str) -> dict:
    """Role, anchor kind and disposition for one object name. Deterministic, ordered rules."""
    dropped = any(k in name for k in DROP)
    if name == "interaction.seat.driver":
        return {"role": "seat.driver", "anchor": "socket", "disposition": "socket"}
    if name == "interaction.seat.passenger1":
        return {"role": "seat.passenger1", "anchor": "none", "disposition": "unknown"}
    if name == "interaction.seat.stunt":
        return {"role": "seat.stunt", "anchor": "roof", "disposition": "placed"}
    if "hood" in name:
        kind, role = "hood", "hood"
    elif "stunt" in name:
        kind, role = "roof", "stunt"
    elif "passenger1" in name:
        kind, role = "right", "passenger"
    else:
        kind, role = "left", "driver"
    return {"role": role, "anchor": kind,
            "disposition": "dropped (D-9)" if dropped else "placed"}


def anchor_table(V, T, areas):
    hood_area = next(a for a in areas if a["name"] == "front_area")
    roof_area = next(a for a in areas if a["name"] == "main_area")
    table = {}
    for kind, x, z, area in (("hood", hood_area["bat_center_geom"][0], HOOD_Z, hood_area),
                             ("roof", roof_area["bat_center_geom"][0], ROOF_Z, roof_area)):
        p, _n = top_hit(V, T, x, z)          # topmost body surface = the deck/roof skin
        table[kind] = {"surface": [round(float(c), 4) for c in p],
                       "normal": [0.0, 1.0, 0.0],
                       "area": area["name"], "donor_gap_m": area["center_gap_m"]}
    for kind, sign in (("left", -1), ("right", 1)):
        p, n = side_hit(V, T, sign, SIDE_Y, SIDE_Z)
        table[kind] = {"surface": [round(float(c), 4) for c in p],
                       "normal": [float(sign), 0.0, 0.0],
                       "station_m": [SIDE_Y, SIDE_Z], "donor_gap_m": None}
    return table


def clearance_for(anchor: dict) -> dict:
    gap = anchor.get("donor_gap_m")
    if gap is None:
        return {"m": SIDE_CLEARANCE, "source": "chosen (band midpoint; donor side clearance "
                                             "not decoded - UNKNOWN)"}
    return {"m": round(max(float(gap), SIDE_MARGIN), 4),
            "source": f"decoded (donor stunt-area gap {gap} m, band floor applied)"}


def solve_offset(tris, surface, normal, target):
    """Distance along the anchor normal so the measured hull distance equals `target`."""
    off = target
    p = surface + normal * off
    d = float(jc3interact.nearest_distance(tris, np.array([p]))[0])
    for _ in range(10):
        if abs(d - target) <= 0.004:
            break
        off = min(max(off + (target - d), BAND[0] + 0.006), BAND[1] - 0.006)
        p = surface + normal * off
        d = float(jc3interact.nearest_distance(tris, np.array([p]))[0])
    return off, p, d


def yaw_of(forward) -> float:
    return round(math.degrees(math.atan2(forward[0], -forward[2])), 3)


# ------------------------------------------------------------------ build
def build() -> dict:
    src = json.load(open(SRC, encoding="utf-8"))
    V, T = jc3interact.read_bat_mesh()
    tris = V[T]
    anchors = anchor_table(V, T, src["stunt_areas"]["areas"])

    rows = []
    for p in src["points"]:
        c = classify(p["name"])
        row = {"name": p["name"], "class": p["class"], "role": c["role"],
               "disposition": c["disposition"],
               "donor_serpente": p["serpente"],
               "state": p.get("state")}
        if c["anchor"] == "none":
            row.update({"anchor": None, "clearance": None, "transform": None,
                        "measure": None,
                        "verdict": "UNKNOWN - the Batmobile cockpit has one seat (COCKPIT.md §1); "
                                   "no analogous location for a passenger seat"})
            rows.append(row)
            continue
        if c["anchor"] == "socket":
            pos = list(DRIVER)
            row.update({"anchor": {"kind": "socket", "surface": pos, "normal": [0.0, 1.0, 0.0]},
                        "clearance": {"m": 0.0, "source": "COCKPIT.md §2 Driver socket"},
                        "transform": {"pos_m": [round(x, 4) for x in pos], "forward": [0.0, 0.0, -1.0],
                                      "up": [0.0, 1.0, 0.0], "yaw_deg": 0.0},
                        "measure": None,
                        "verdict": "inside by design (the seat is in the cockpit)"})
            rows.append(row)
            continue

        a = anchors[c["anchor"]]
        cl = clearance_for(a)
        surf = np.array(a["surface"], dtype=float)
        nrm = np.array(a["normal"], dtype=float)
        nrm = nrm / np.linalg.norm(nrm)
        off, p, _d = solve_offset(tris, surf, nrm, cl["m"])
        cl = {"m": round(float(off), 4), "target_m": cl["m"], "source": cl["source"]}
        pos = [float(p[i]) for i in range(3)]
        forward = [0.0, 0.0, -1.0] if c["anchor"] in ("hood", "roof") else \
                  [-a["normal"][0], 0.0, 0.0]   # side anchors face the body
        row.update({"anchor": {"kind": c["anchor"], "surface": a["surface"],
                                "normal": [round(float(x), 4) for x in nrm]},
                    "clearance": cl,
                    "transform": {"pos_m": [round(x, 4) for x in pos],
                                  "forward": forward, "up": [0.0, 1.0, 0.0],
                                  "yaw_deg": yaw_of(forward)},
                    "measure": None, "verdict": None})
        rows.append(row)

    # one distance/inside pass for all placed transforms + the socket
    pts, idx = [], []
    for i, r in enumerate(rows):
        if r["transform"] is not None:
            pts.append(r["transform"]["pos_m"])
            idx.append(i)
    P = np.array(pts, dtype=float)
    dist = jc3interact.nearest_distance(tris, P)
    ins = jc3interact.inside(tris, P)
    for k, i in enumerate(idx):
        rows[i]["measure"] = {"nearest_m": round(float(dist[k]), 4), "inside": bool(ins[k])}
        if rows[i]["disposition"] == "socket":
            continue
        lo, hi = BAND
        rows[i]["verdict"] = ("in band" if (lo <= dist[k] <= hi and not ins[k])
                              else ("FAIL: inside hull" if ins[k] else "FAIL: out of band"))

    placed = [r for r in rows if r["disposition"] == "placed"]
    dropped = [r for r in rows if r["disposition"].startswith("dropped")]
    counts = {
        "objects": len(rows),
        "placed": len(placed),
        "dropped_D9": len(dropped),
        "socket": sum(1 for r in rows if r["disposition"] == "socket"),
        "unknown": sum(1 for r in rows if r["disposition"] == "unknown"),
        "in_band": sum(1 for r in placed if r["verdict"] == "in band"),
        "by_role": {k: sum(1 for r in rows if r["role"] == k)
                    for k in sorted({r["role"] for r in rows})},
    }
    return {
        "schema": SCHEMA, "generator": "t9_interaction.py", "card": "T-13",
        "source": os.path.relpath(SRC, ROOT).replace("\\", "/"),
        "source_digest": src["digest"],
        "decision": {"id": "D-9", "status": "resolved 2026-10-28 (user): no",
                     "applied": "hijack objects (*pull.out*, *pulled.out*) dropped"},
        "band_m": list(BAND),
        "mesh": {"file": "Working/TrueScale/body_lod1.rbm", "vertices": int(len(V)),
                 "triangles": int(len(T)), "bbox": [[round(float(x), 4) for x in V.min(0)],
                                                    [round(float(x), 4) for x in V.max(0)]]},
        "frames": {"jc3": "x lateral (left -x), y up, z longitudinal (nose -z)",
                   "driver_socket": list(DRIVER)},
        "anchors": {k: v for k, v in anchors.items()},
        "counts": counts,
        "objects": rows,
    }


# ------------------------------------------------------------------ render
def render_md(d: dict) -> str:
    m = d["mesh"]
    a = []
    add = a.append
    add("# Interaction translation (T-13)")
    add("")
    add("Every interaction object in the Serpente donor `.epe` placed on the **Batmobile** body, by")
    add("role, with a transform (position, forward, up, yaw) and a measured distance to the hull.")
    add(f"Rebuilt by `python Tools/scripts/t9_interaction.py --check` from")
    add(f"`{d['source']}` (digest `{d['source_digest']}`) and the body mesh")
    add(f"`{m['file']}` ({m['triangles']} triangles, {m['vertices']} vertices).")
    add("")
    add("## 1. Decision applied")
    add("")
    add(f"`{d['decision']['id']}` is **{d['decision']['status']}**: {d['decision']['applied']}.")
    add("They keep a transform for completeness but are not part of the port.")
    add("")
    add("## 2. Method")
    add("")
    add("Frame (JC3, the same one as COCKPIT.md): x lateral (left = -x), y vertical (ground 0.020),")
    add("z longitudinal, nose at -z. Each object's role picks an anchor on the body shell, found by a")
    add("ray cast against the body mesh; the transform sits `clearance` metres outward along the")
    add("anchor normal.")
    add("")
    add("| anchor | surface point (m) | normal | target clearance |")
    add("|---|---|---|---|")
    kinds = [("hood", f"front deck - topmost body surface at z {HOOD_Z}"),
             ("roof", f"roof - topmost body surface at z {ROOF_Z} (canopy over the driver)"),
             ("left", f"cockpit left side ray, y {SIDE_Y}, z {SIDE_Z}"),
             ("right", f"cockpit right side ray, y {SIDE_Y}, z {SIDE_Z}")]
    for k, label in kinds:
        an = d["anchors"][k]
        cl = clearance_for(an)
        add(f"| `{k}` - {label} | {an['surface']} | {an['normal']} | {cl['m']} m - {cl['source']} |")
    add("")
    add("The `Driver` socket is the seat transform: " + str(d["frames"]["driver_socket"]) +
        " m, forward (0, 0, -1) (COCKPIT.md §2).")
    add("")
    add("## 3. Counts")
    add("")
    c = d["counts"]
    add("| item | count |")
    add("|---|---|")
    for k in ("objects", "placed", "dropped_D9", "socket", "unknown", "in_band"):
        add(f"| {k} | {c[k]} |")
    add("")
    add("| role | objects |")
    add("|---|---|")
    for k, v in c["by_role"].items():
        add(f"| `{k}` | {v} |")
    add("")
    add("## 4. Every object")
    add("")
    add("| object | role | disposition | anchor | pos (m) | clearance (m) | nearest (m) | inside | verdict |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in d["objects"]:
        t = r["transform"]
        pos = "-" if not t else ", ".join(f"{x:g}" for x in t["pos_m"])
        an = "-" if not r["anchor"] else r["anchor"]["kind"]
        cl = "-" if not r["clearance"] else f"{r['clearance']['m']:g}"
        me = r["measure"]
        near = "-" if not me else f"{me['nearest_m']:.4f}"
        ins = "-" if not me else ("yes" if me["inside"] else "no")
        add(f"| `{r['name']}` | {r['role']} | {r['disposition']} | {an} | {pos} | {cl} | {near} | "
            f"{ins} | {r['verdict']} |")
    add("")
    add("## 5. The Done rule")
    add("")
    add(f"`--check` asserts, for every **placed** object: nearest hull triangle >= {BAND[0]} m and")
    add(f"<= {BAND[1]} m, and the point is not inside the hull. The `Driver` socket is the one")
    add("documented exception - a seat is inside the cockpit by definition - and")
    add("`interaction.seat.passenger1` has no transform because the Batmobile cockpit has one seat.")
    add("")
    add("## 6. UNKNOWNs and limits")
    add("")
    add("* **Donor clearance for entries, exits, transitions, points and triggers is not in any")
    add("  decoded file.** G2-18 recorded the donor gap only for the three stunt areas (0.048 m hood,")
    add("  0.1474 m roof); the side anchors therefore use a chosen 0.10 m inside the card's band and")
    add("  the choice is labelled, not presented as a game value.")
    add("* **No passenger seat exists** on the Batmobile (COCKPIT.md §1: one cockpit tub, one seat),")
    add("  so `interaction.seat.passenger1` is UNKNOWN rather than placed.")
    add("* Side anchors are one station per side (y 1.15, z -0.95); the card does not ask for a")
    add("  per-object lateral spread, and the donor's world positions are mostly inherited container")
    add("  origins (70 of 85), so there is nothing finer to copy.")
    add("* Yaw is `atan2(forward.x, -forward.z)` in degrees, the project's JC3 convention (forward =")
    add("  -z at 0); it is derived from the anchor normal, not decoded from the donor.")
    add("")
    add("## 7. Reproduce")
    add("")
    add("```")
    add("python Tools/scripts/t9_interaction.py --write")
    add("python Tools/scripts/t9_interaction.py --check")
    add("```")
    add("")
    return "\n".join(a).rstrip() + "\n"


# ------------------------------------------------------------------ commands
def cmd_write() -> int:
    d = build()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(d, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render_md(d))
    c = d["counts"]
    print(f"{JSON_NAME}: {c['objects']} objects, {c['placed']} placed, {c['dropped_D9']} dropped "
          f"(D-9), {c['socket']} socket, {c['unknown']} unknown, {c['in_band']} in band")
    return 0


def invariant_checks(d: dict) -> list:
    bad = []
    rows = d["objects"]
    if len(rows) != 85:
        bad.append(f"{len(rows)} objects, expected 85")
    lo, hi = BAND
    for r in rows:
        if r["disposition"] == "placed":
            m = r["measure"]
            if m is None:
                bad.append(f"{r['name']}: placed without a measurement")
            elif m["inside"]:
                bad.append(f"{r['name']}: inside the hull")
            elif not (lo <= m["nearest_m"] <= hi):
                bad.append(f"{r['name']}: {m['nearest_m']} m outside [{lo}, {hi}]")
        elif r["disposition"] == "socket":
            if r["transform"]["pos_m"] != [round(x, 4) for x in DRIVER]:
                bad.append("driver socket moved")
            if not r["measure"]:
                bad.append("driver socket has no measurement")
        elif r["disposition"] == "unknown":
            if r["transform"] is not None:
                bad.append(f"{r['name']}: unknown but has a transform")
        elif r["disposition"].startswith("dropped"):
            if not any(k in r["name"] for k in DROP):
                bad.append(f"{r['name']}: dropped without a D-9 name")
        else:
            bad.append(f"{r['name']}: unknown disposition {r['disposition']}")
    c = d["counts"]
    if c["placed"] + c["dropped_D9"] + c["socket"] + c["unknown"] != c["objects"]:
        bad.append("counts do not add up")
    if c["in_band"] != c["placed"]:
        bad.append(f"{c['placed'] - c['in_band']} placed object(s) out of band")
    if c["dropped_D9"] != 6:
        bad.append(f"{c['dropped_D9']} dropped, expected 6")
    if c["unknown"] != 1:
        bad.append(f"{c['unknown']} unknown, expected 1 (passenger seat)")
    return bad


def cmd_check() -> int:
    d = build()
    bad = []
    jp, mp = os.path.join(OUT, JSON_NAME), os.path.join(OUT, MD_NAME)
    for p in (jp, mp):
        if not os.path.exists(p):
            print(f"FAIL: {os.path.basename(p)} missing")
            return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != d:
        for k in sorted(set(old) | set(d)):
            if old.get(k) != d.get(k):
                bad.append(f"json section changed: {k}")
                break
    md = render_md(d)
    cur = open(mp, encoding="utf-8").read()
    if md != cur:
        import difflib
        diff = list(difflib.unified_diff(cur.splitlines(), md.splitlines(), "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += invariant_checks(d)
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    c = d["counts"]
    print(f"PASS: {c['objects']} objects, {c['placed']} placed in band "
          f"[{BAND[0]}, {BAND[1]}] m, {c['dropped_D9']} dropped (D-9), 1 socket, 1 unknown")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
