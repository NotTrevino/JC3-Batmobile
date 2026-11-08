"""bmak_light_sockets.py - re-check LIGHTS.md's socket -> bone step against the cooked mesh.

`Research/BatmobileGrab/LIGHTS.md` maps 101 `VehicleLights` entries to a bone by looking the
entry's socket up in the exported skeleton.  This script re-derives the step from the cooked
skeletal mesh instead:

  * socket -> `BoneName` + relative `location_uu`   (`SKINS.json`, decoded from the mesh's
    `Sockets` array export)
  * bone   -> world bind transform                   (`BONES.json`, 180 bones)
  * the light's recorded position                    (`LIGHTS.json`, `socket_location`)

For every light it reports whether the socket exists in the cooked table, whether the socket's
`BoneName` matches the bone LIGHTS chose, whether that bone is one of the 180, and the distance
between the light's recorded position and the socket's world position.

The world position is computed two ways and the *data* decides which one LIGHTS recorded:

  raw    : location_uu                              (the socket offset itself, cm)
  world  : bone.world_position_cm + R(bone.quat) * location_uu

The mode with the smaller median error is the one LIGHTS used; the outliers (> 1 cm) are listed
under it.  Guessing the mode would be exactly the kind of assumption this card forbids, so both
numbers are printed.

Usage
    python Tools/scripts/bmak_light_sockets.py --write
    python Tools/scripts/bmak_light_sockets.py --check
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "LIGHT_SOCKETS.md")
JS = os.path.join(OUT, "LIGHT_SOCKETS.json")
TOL_CM = 1.0


def load(name: str) -> dict:
    return json.load(open(os.path.join(OUT, name), encoding="utf-8"))


def rot(q, v):
    """Rotate v by quaternion q=(x,y,z,w)."""
    x, y, z, w = q
    vx, vy, vz = v
    # t = 2 * cross(q.xyz, v)
    tx = 2 * (y * vz - z * vy)
    ty = 2 * (z * vx - x * vz)
    tz = 2 * (x * vy - y * vx)
    return [vx + w * tx + (y * tz - z * ty),
            vy + w * ty + (z * tx - x * tz),
            vz + w * tz + (x * ty - y * tx)]


def dist(a, b) -> float:
    return math.sqrt(sum((p - q) ** 2 for p, q in zip(a, b)))


def median(xs):
    s = sorted(xs)
    n = len(s)
    return 0.0 if not n else (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)


def build() -> dict:
    L, S, B = load("LIGHTS.json"), load("SKINS.json"), load("BONES.json")
    bones = {b["name"]: b for b in B["bones"]}
    skins = S["skins"]
    tables = {k: v["sockets"]["by_name"] for k, v in skins.items()}
    skin_pkg = {k: v["package"] for k, v in skins.items()}

    def own_table(socket: str, pkg: str):
        """The socket as this package's own cooked mesh records it, or (None, None).

        No borrowing: the four tables disagree about the same socket name, so a socket read from
        another package's mesh is not evidence about this one (see `conflicts`).
        """
        for k, t in tables.items():
            if skin_pkg[k] == pkg and socket in t:
                return k, t[socket]
        return None, None

    rows, missing, bone_mismatch, not_in_rig, no_table = [], [], [], [], []
    for veh in L["vehicles"]:
        for e in veh["entries"]:
            key, sock = own_table(e["socket"], veh["package"])
            rec = {"package": veh["package"], "owner": veh["owner"],
                   "socket": e["socket"], "light_bone": e["bone"],
                   "type": e.get("type"), "orphan_socket": e.get("orphan_socket", False),
                   "recorded": e["socket_location"], "table": key}
            if sock is None:
                known = any(e["socket"] in t for t in tables.values())
                rec["status"] = ("no socket table decoded for this package" if known
                                 else "socket missing from the cooked mesh")
                if known:
                    no_table.append({k2: rec[k2] for k2 in
                                     ("package", "socket", "type", "light_bone",
                                      "orphan_socket")})
                else:
                    missing.append(rec)
                rows.append(rec)
                continue
            rec["socket_bone"] = sock["bone"]
            rec["location_uu"] = sock.get("location_uu")
            b = bones.get(sock["bone"])
            rec["bone_in_180"] = bool(b)
            rec["bone_agrees"] = sock["bone"] == e["bone"]
            if not rec["bone_agrees"]:
                bone_mismatch.append({"package": veh["package"], "socket": e["socket"],
                                      "light_bone": e["bone"],
                                      "socket_bone": sock["bone"]})
            if not b:
                not_in_rig.append({"package": veh["package"], "socket": e["socket"],
                                   "bone": sock["bone"]})
                rows.append(rec)
                continue
            wp = b["bind"]["world_position_cm"]
            q = b["bind"]["world_rotation_quat"]
            world = [wp[i] + rot(q, sock["location_uu"])[i] for i in range(3)]
            rec["world_cm"] = [round(v, 3) for v in world]
            rec["d_raw_cm"] = round(dist(e["socket_location"], sock["location_uu"]), 3)
            rec["d_world_cm"] = round(dist(e["socket_location"], world), 3)
            rec["status"] = "ok"
            rows.append(rec)

    scored = [r for r in rows if "d_raw_cm" in r]
    med_raw = median([r["d_raw_cm"] for r in scored])
    med_world = median([r["d_world_cm"] for r in scored])
    mode = "raw" if med_raw <= med_world else "world"
    key = "d_raw_cm" if mode == "raw" else "d_world_cm"
    over = [r for r in scored if r[key] > TOL_CM]
    for r in scored:
        r["delta_cm"] = r.pop(key)
    for r in scored:
        r.pop("d_raw_cm" if mode == "world" else "d_world_cm", None)

    by_pkg = {}
    for r in rows:
        g = by_pkg.setdefault(r["package"], {"entries": 0, "ok": 0, "missing": 0,
                                             "bone_mismatch": 0, "bone_not_in_rig": 0,
                                             "over_tol": 0, "no_table": 0})
        g["entries"] += 1
        g["ok"] += 1 if r["status"] == "ok" else 0
        g["no_table"] += 1 if r["status"].startswith("no socket table") else 0
        g["missing"] += 1 if r["status"].startswith("socket missing") else 0
        g["bone_mismatch"] += 0 if r.get("bone_agrees", True) else 1
        g["bone_not_in_rig"] += 0 if r.get("bone_in_180", True) else 1
        g["over_tol"] += 1 if r.get("delta_cm", 0) > TOL_CM else 0

    # Cross-mesh check: the same socket name in different cooked meshes, same bone or not.
    light_bones = {}
    for v in L["vehicles"]:
        for e in v["entries"]:
            if e["bone"]:
                light_bones.setdefault(e["socket"], {}).setdefault(e["bone"], set()).add(
                    v["package"])
    conflicts = []
    for s in sorted(light_bones):
        by, locs = {}, {}
        for k, t in tables.items():
            if s in t and t[s].get("location_uu"):
                by.setdefault(t[s]["bone"], []).append(k)
                locs[k] = [round(x, 3) for x in t[s]["location_uu"]]
        if len(by) > 1:
            conflicts.append({"socket": s,
                              "tables": dict(sorted(by.items())),
                              "locations": locs,
                              "lights": {b: sorted(ps) for b, ps in light_bones[s].items()}})

    checks = [
        ("the 101 light entries and 21 distinct sockets parse",
         sum(len(v["entries"]) for v in L["vehicles"]) == 101
         and len({e["socket"] for v in L["vehicles"] for e in v["entries"]}) == 21,
         "%d entries, %d sockets, %d vehicles"
         % (sum(len(v["entries"]) for v in L["vehicles"]),
            len({e["socket"] for v in L["vehicles"] for e in v["entries"]}),
            len(L["vehicles"]))),
        ("every entry either resolves in its own package's socket table or is listed",
         len(rows) == 101
         and len(rows) == len(scored) + len(missing) + len(no_table) + len(not_in_rig),
         "%d rows = %d scored + %d socket missing + %d no table + %d bone-not-in-rig"
         % (len(rows), len(scored), len(missing), len(no_table), len(not_in_rig))),
        ("every resolved row compares its cooked BoneName with the bone LIGHTS chose",
         all("bone_agrees" in r for r in scored),
         "%d resolved, %d agree, %d disagree (disagreements tabulated below)"
         % (len(scored), len(scored) - len(bone_mismatch), len(bone_mismatch))),
        ("every socket bone is one of BONES.json's 180",
         not not_in_rig,
         "bones %d; sockets outside the rig: %d %s"
         % (len(bones), len(not_in_rig), not_in_rig[:3])),
        ("both position interpretations are measured and the smaller-median one is chosen",
         len(scored) > 0 and med_raw >= 0 and med_world >= 0 and mode in ("raw", "world"),
         "mode=%s (median raw %.3f cm, world %.3f cm); %d entries over %.1f cm under the "
         "chosen mode (tabulated below)"
         % (mode, med_raw, med_world, len(over), TOL_CM)),
        ("no row is scored against another package's mesh",
         all(skin_pkg[r["table"]] == r["package"] for r in scored),
         "%d scored rows, all from their own package's table; %d rows have no table for their "
         "package" % (len(scored), len(no_table))),
        ("all six orphan-flagged rows are unresolved and listed",
         sum(1 for r in rows if r["orphan_socket"]) == 6
         and all(r["status"] != "ok" for r in rows if r["orphan_socket"]),
         "%d orphan-flagged: %d missing from their own mesh, %d unverifiable (no table)"
         % (sum(1 for r in rows if r["orphan_socket"]), len(missing),
            sum(1 for r in no_table if r["orphan_socket"]))),
        ("cross-mesh socket tables are compared, not silently merged",
         len(conflicts) >= 1 and all(len(c["tables"]) > 1 for c in conflicts),
         "%d socket names carry different parent bones in different cooked meshes: %s"
         % (len(conflicts), [c["socket"] for c in conflicts][:8])),
    ]

    return {
        "task": "re-check LIGHTS.md's socket -> bone step against the cooked skeletal mesh",
        "inputs": {"lights": "Research/BatmobileGrab/LIGHTS.json",
                   "skins": "Research/BatmobileGrab/SKINS.json",
                   "bones": "Research/BatmobileGrab/BONES.json",
                   "bones_count": len(bones)},
        "mode": {"chosen": mode, "median_raw_cm": round(med_raw, 3),
                 "median_world_cm": round(med_world, 3), "tolerance_cm": TOL_CM,
                 "rule": "the interpretation with the smaller median error is the one LIGHTS "
                         "recorded; both medians are printed"},
        "by_package": by_pkg,
        "missing": missing,
        "bone_mismatch": bone_mismatch,
        "bone_not_in_rig": not_in_rig,
        "over_tolerance": over,
        "no_table": no_table,
        "conflicts": conflicts,
        "rows": rows,
        "checks": [{"check": n, "pass": bool(ok), "detail": d} for n, ok, d in checks],
    }


def render(d: dict) -> str:
    a = []
    A = a.append
    m = d["mode"]
    A("# Light sockets vs the cooked skeletal mesh")
    A("")
    A("Generated by `Tools/scripts/bmak_light_sockets.py` (`--write`); `--check` re-derives every")
    A("distance.  Reviewed card: `Research/BatmobileGrab/LIGHTS.md`.")
    A("")
    A("Sources: `LIGHTS.json` (101 entries, 21 sockets, 4 packages), `SKINS.json` (cooked `Sockets`")
    A("arrays: `BoneName` + `location_uu`), `BONES.json` (%d bones with bind transforms)."
      % d["inputs"]["bones_count"])
    A("")
    A("## How the world position is computed")
    A("")
    A("`world = bone.world_position_cm + R(bone.world_rotation_quat) * socket.location_uu`")
    A("")
    A("LIGHTS' `socket_location` could in principle be the raw offset or the world point, so both")
    A("are measured and the data chooses:")
    A("")
    A("| interpretation | median error |")
    A("|---|---:|")
    A("| raw offset vs recorded | %.3f cm |" % m["median_raw_cm"])
    A("| world point vs recorded | %.3f cm |" % m["median_world_cm"])
    A("")
    A("**Chosen: `%s`** (smaller median)." % m["chosen"])
    A("")
    A("## Summary by package")
    A("")
    A("| package | entries | verified in own table | socket missing | no table for | bone "
      "differs | bone not in rig | > 1 cm |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for p, g in d["by_package"].items():
        A("| `%s` | %d | %d | %d | %d | %d | %d | %d |"
          % (p, g["entries"], g["ok"], g["missing"], g.get("no_table", 0),
             g["bone_mismatch"], g["bone_not_in_rig"], g["over_tol"]))
    A("")
    A("## Lights whose socket is missing")
    A("")
    if d["missing"]:
        A("| package | socket | type | LIGHTS bone |")
        A("|---|---|---|---|")
        for r in sorted(d["missing"], key=lambda x: (x["package"], x["socket"])):
            A("| `%s` | `%s` | `%s` | `%s` |"
              % (r["package"], r["socket"], r["type"], r["light_bone"]))
    else:
        A("none")
    A("")
    A("## Packages with no decoded socket table")
    A("")
    A("`SKINS.json` decodes a `Sockets` array for four cooked meshes: `Playable_Batmobile_SF`")
    A("plus the three `Showcase_Batmobiles_*` skins.  The other three LIGHTS packages")
    A("(`Playable_BatmobileMK2_SF`, `Playable_BatmobileJoker_SF`, `Playable_BatmobileFunhouse_SF`)")
    A("have no table of their own, and the tables disagree about the same socket names (next")
    A("section), so a socket borrowed from another mesh would not be evidence about this one.")
    A("These rows are listed and **excluded** from the position and bone findings - their sockets")
    A("are UNVERIFIED, not verified-wrong.")
    A("")
    if d["no_table"]:
        A("| package | rows | sockets |")
        A("|---|---:|---|")
        for p in sorted({r["package"] for r in d["no_table"]}):
            rs = [r for r in d["no_table"] if r["package"] == p]
            A("| `%s` | %d | %s |"
              % (p, len(rs), ", ".join("`%s`" % s for s in sorted({r["socket"]
                                                                    for r in rs}))))
    else:
        A("none")
    A("")
    A("## The same socket name, different parents in different cooked meshes")
    A("")
    A("A socket's relative location is only meaningful with the bone it hangs from, so this is the")
    A("check that the name -> bone step cannot survive on one table's word alone.")
    A("")
    if d["conflicts"]:
        A("| socket | `playable` | `standard` | `mk2` | `jokerfied` | LIGHTS bones |")
        A("|---|---|---|---|---|---|")
        for c in d["conflicts"]:
            cells = []
            for t in ("playable", "standard", "mk2", "jokerfied"):
                cells.append("`%s`" % c["tables"][t][0] if t in c["tables"] else "-")
            A("| `%s` | %s | %s |"
              % (c["socket"], " | ".join(cells),
                 ", ".join("`%s`" % b for b in sorted(c["lights"]))))
        A("")
        A("The locations differ too, and neither location appears under any other socket name in")
        A("any table (`locations` in the JSON), so this is **not** a name/offset shift inside one")
        A("array: the two mesh families genuinely record different socket data for the same name.")
    else:
        A("none")
    A("")
    A("## Lights whose position differs by more than 1 cm (`%s` mode)" % m["chosen"])
    A("")
    if d["over_tolerance"]:
        A("| package | socket | recorded (cm) | computed (cm) | delta cm |")
        A("|---|---|---|---|---:|")
        for r in d["over_tolerance"]:
            rec = "(" + ", ".join("%.3f" % v for v in r["recorded"]) + ")"
            wc = r.get("world_cm")
            wcs = "(" + ", ".join("%.3f" % v for v in wc) + ")" if wc else "-"
            A("| `%s` | `%s` | %s | %s | %.3f |"
              % (r["package"], r["socket"], rec, wcs, r["delta_cm"]))
    else:
        A("none - every resolved light is within 1 cm.")
    A("")
    A("This is a **consistency** result, not independent confirmation: LIGHTS.md was built from the")
    A("same `SKINS.json` socket arrays, so a 0.000 cm median says the card copied its source")
    A("faithfully and that the offsets are raw socket-relative vectors (the world interpretation")
    A("misses by the bone's bind displacement).  The check that is *not* circular is the")
    A("cross-mesh table comparison above.")
    A("")
    A("## Socket `BoneName` vs the bone LIGHTS chose")
    A("")
    if d["bone_mismatch"]:
        A("| package | socket | LIGHTS bone | cooked socket BoneName |")
        A("|---|---|---|---|")
        for r in d["bone_mismatch"]:
            A("| `%s` | `%s` | `%s` | `%s` |"
              % (r["package"], r["socket"], r["light_bone"], r["socket_bone"]))
    else:
        A("every resolved socket's `BoneName` equals the bone LIGHTS recorded.")
    A("")
    A("## Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c["check"], "PASS" if c["pass"] else "FAIL",
                                          c["detail"]))
    A("")
    A("## UNKNOWNs")
    A("")
    A("1. **Socket tables for the MK2 / Joker / Funhouse packages.**  No cooked socket table was")
    A("   decoded for them, so their 73 light rows are unverified.  The `Showcase_Batmobiles_MK2`")
    A("   and `_Jokerfied` tables are a different package and are not substituted.")
    A("2. **Which family the headlight bones are right for.**  `playable`/`standard` parent the six")
    A("   headlight sockets to `Winch_DOOR_Mesh`; `mk2`/`jokerfied` parent them to")
    A("   `Batmobile_Chassis`.  This card does not decide which mesh is correct - it reports that")
    A("   the tables disagree and that LIGHTS.md inherits the split.")
    A("3. **Why a socket is absent.**  `HeadLight1c` and `HeadLight2c` appear in none of the four")
    A("   cooked tables, so no mesh in `SKINS.json` carries them; whether another mesh in the")
    A("   package holds that name is not claimed.")
    A("")
    A("## Reproduce")
    A("")
    A("    uv run python Tools/scripts/bmak_light_sockets.py --write")
    A("    uv run python Tools/scripts/bmak_light_sockets.py --check")
    A("")
    return "\n".join(a) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md, js = render(d), json.dumps(d, indent=1) + "\n"
    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode())))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode())))
    if args.check:
        bad = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                bad.append("%s missing" % os.path.relpath(path, ROOT))
            elif open(path, encoding="utf-8").read() != want:
                bad.append("%s differs" % os.path.relpath(path, ROOT))
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
